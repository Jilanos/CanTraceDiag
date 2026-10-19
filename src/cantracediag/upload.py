"""Streaming staging of browser uploads with independent byte budgets (req_034).

FastAPI's ``UploadFile`` parameters make Starlette parse the *whole* multipart
body into spooled temporary files before the handler runs, so a size cap checked
in the handler only fires after the bytes are already on disk. This module
parses the request body as it arrives instead and writes each file part straight
into a staging directory, enforcing while streaming:

* an inclusive cap on the trace part;
* an independent cap on the sum of uploaded DBC parts;
* an allowance for the multipart envelope (boundaries, part headers and
  non-file form fields);
* a cap on the whole body, checked against a declared ``Content-Length`` before
  reading and against the bytes actually received while reading.

Nothing is buffered beyond one network chunk. The caller owns the staging
directory and removes it on any failure, cancellation or disconnect.
"""

from __future__ import annotations

import errno
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

import python_multipart
from python_multipart.multipart import parse_options_header
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

from cantracediag.security import MIB, UploadLimits

# Upper bound on parts in one request (trace + DBCs from a folder pick + library
# digests); far above real use, low enough to stop a part-flood.
MAX_PARTS = 1000
# A non-file form field carries a library digest; nothing legitimate is longer.
MAX_FIELD_BYTES = 4096
# Free space kept beyond the declared body before staging starts.
_STAGING_HEADROOM = 64 * MIB


class UploadRejected(Exception):
    """An upload refused with an HTTP status and an operator-facing message."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


class UploadCancelled(Exception):
    """The operator cancelled the import while the upload was streaming."""


@dataclass(slots=True)
class StagedFile:
    name: str  # original basename, for display
    path: Path
    size: int


@dataclass(slots=True)
class StagedUpload:
    trace: StagedFile | None = None
    dbcs: list[StagedFile] = field(default_factory=list)
    fields: dict[str, list[str]] = field(default_factory=dict)
    received: int = 0


def format_bytes(n: int) -> str:
    """``1073741824`` -> ``"1 GiB (1,073,741,824 bytes)"``; exact, never rounded up."""
    for unit, size in (("GiB", 1024 * MIB), ("MiB", MIB), ("KiB", 1024)):
        if n >= size and n % size == 0:
            return f"{n // size} {unit} ({n:,} bytes)"
    return f"{n:,} bytes"


def safe_name(name: str) -> str:
    """Basename only, so uploaded/relative paths cannot escape the staging dir."""
    return Path(name.replace("\\", "/")).name or "upload"


def _too_large(what: str, limit: int) -> UploadRejected:
    return UploadRejected(413, f"{what} exceeds the {format_bytes(limit)} limit.")


def _no_space() -> UploadRejected:
    return UploadRejected(
        507,
        "Not enough free disk space to stage the upload. Free space on the "
        "workspace drive, then retry.",
    )


class _Part:
    __slots__ = ("disposition", "name", "filename", "kind", "handle", "path", "size", "data")

    def __init__(self) -> None:
        self.disposition = b""
        self.name = ""
        self.filename: str | None = None
        self.kind = "field"  # "trace" | "dbc" | "ignored" | "field"
        self.handle: BinaryIO | None = None
        self.path: Path | None = None
        self.size = 0
        self.data = bytearray()


async def stage_multipart(
    request: Request,
    staging: Path,
    limits: UploadLimits,
    *,
    trace_suffixes: tuple[str, ...],
    cancel_check: Callable[[], bool] | None = None,
    on_progress: Callable[[int, int | None], None] | None = None,
) -> StagedUpload:
    """Stream ``request``'s multipart body into ``staging`` under ``limits``.

    Recognized parts: one ``trace`` file, any number of ``dbcs`` files (entries
    not ending in ``.dbc`` are discarded but still counted against the DBC
    budget) and ``library`` text fields. Raises :class:`UploadRejected` on a
    malformed or oversized body, :class:`UploadCancelled` when ``cancel_check``
    turns true, and lets ``ClientDisconnect`` propagate. Partially written files
    are closed; the caller removes ``staging``.
    """
    content_type, params = parse_options_header(request.headers.get("content-type", ""))
    if content_type != b"multipart/form-data" or b"boundary" not in params:
        raise UploadRejected(400, "Expected a multipart/form-data upload.")

    declared: int | None = None
    raw_length = request.headers.get("content-length")
    if raw_length is not None and raw_length.strip().isdigit():
        declared = int(raw_length)
        if declared > limits.max_request:
            raise _too_large("Upload", limits.max_request)
        try:
            free = shutil.disk_usage(staging).free
        except OSError:
            free = None
        if free is not None and free < declared + _STAGING_HEADROOM:
            raise _no_space()

    staged = StagedUpload()
    file_bytes = 0
    dbc_bytes = 0
    parts = 0
    current = _Part()
    header_name = bytearray()
    header_value = bytearray()
    pending: list[tuple[BinaryIO, bytes]] = []
    seen_dbcs: set[str] = set()
    opened: list[BinaryIO] = []

    def on_part_begin() -> None:
        nonlocal current, parts
        parts += 1
        if parts > MAX_PARTS:
            raise UploadRejected(400, "Too many parts in the upload.")
        current = _Part()

    def on_header_field(data: bytes, start: int, end: int) -> None:
        header_name.extend(data[start:end])

    def on_header_value(data: bytes, start: int, end: int) -> None:
        header_value.extend(data[start:end])
        if len(header_value) > MAX_FIELD_BYTES:
            raise UploadRejected(400, "Malformed multipart part header.")

    def on_header_end() -> None:
        if bytes(header_name).lower() == b"content-disposition":
            current.disposition = bytes(header_value)
        header_name.clear()
        header_value.clear()

    def on_headers_finished() -> None:
        _, options = parse_options_header(current.disposition)
        if b"name" not in options:
            raise UploadRejected(400, "Malformed multipart part: missing field name.")
        current.name = options[b"name"].decode("utf-8", "replace")
        if b"filename" not in options:
            return
        current.filename = options[b"filename"].decode("utf-8", "replace")
        base = safe_name(current.filename)
        if current.name == "trace":
            if staged.trace is not None:
                raise UploadRejected(400, "Only one trace file can be uploaded.")
            if not base.lower().endswith(trace_suffixes):
                listed = ", ".join(trace_suffixes[:-1]) + f", or {trace_suffixes[-1]}"
                raise UploadRejected(400, f"Trace file must be an {listed} file.")
            current.kind = "trace"
        elif current.name == "dbcs":
            if not base.lower().endswith(".dbc"):
                current.kind = "ignored"  # e.g. a non-DBC file from a folder pick
                return
            if base in seen_dbcs:
                raise UploadRejected(400, f"Duplicate DBC basename: {base}")
            seen_dbcs.add(base)
            current.kind = "dbc"
        else:
            raise UploadRejected(400, "Unexpected file field in the upload.")
        # Trace and DBCs live in sibling subfolders so a DBC can never shadow the
        # trace even if both share a basename.
        folder = staging / current.kind
        folder.mkdir(exist_ok=True)
        current.path = folder / base
        try:
            current.handle = open(current.path, "xb")  # noqa: SIM115 - closed on part end
        except OSError as exc:
            if exc.errno == errno.ENOSPC:
                raise _no_space() from exc
            raise
        opened.append(current.handle)
        if current.kind == "trace":
            staged.trace = StagedFile(base, current.path, 0)

    def on_part_data(data: bytes, start: int, end: int) -> None:
        nonlocal file_bytes, dbc_bytes
        chunk = data[start:end]
        if current.filename is None:
            current.data.extend(chunk)
            if len(current.data) > MAX_FIELD_BYTES:
                raise UploadRejected(400, "Form field too large.")
            return
        current.size += len(chunk)
        file_bytes += len(chunk)
        if current.kind == "trace":
            if current.size > limits.trace:
                raise _too_large("Trace file", limits.trace)
        else:
            dbc_bytes += len(chunk)
            if dbc_bytes > limits.dbc:
                raise _too_large("Uploaded DBC total", limits.dbc)
        if current.handle is not None:
            pending.append((current.handle, chunk))

    def on_part_end() -> None:
        if current.filename is None:
            value = bytes(current.data).decode("utf-8", "replace")
            staged.fields.setdefault(current.name, []).append(value)
            return
        if current.kind == "trace" and staged.trace is not None:
            staged.trace.size = current.size
        elif current.kind == "dbc" and current.path is not None:
            staged.dbcs.append(StagedFile(safe_name(current.filename), current.path, current.size))
        if current.handle is not None:
            # Closed after the pending writes of this chunk are flushed.
            pending.append((current.handle, b""))

    parser = python_multipart.MultipartParser(
        params[b"boundary"],
        {
            "on_part_begin": on_part_begin,
            "on_part_data": on_part_data,
            "on_part_end": on_part_end,
            "on_header_field": on_header_field,
            "on_header_value": on_header_value,
            "on_header_end": on_header_end,
            "on_headers_finished": on_headers_finished,
        },
    )

    def flush(batch: list[tuple[BinaryIO, bytes]]) -> None:
        try:
            for handle, chunk in batch:
                if chunk:
                    handle.write(chunk)
                else:
                    handle.close()
        except OSError as exc:
            if exc.errno == errno.ENOSPC:
                raise _no_space() from exc
            raise

    try:
        async for chunk in request.stream():
            if cancel_check is not None and cancel_check():
                raise UploadCancelled("Import cancelled by operator.")
            if not chunk:
                continue
            staged.received += len(chunk)
            if staged.received > limits.max_request:
                raise _too_large("Upload", limits.max_request)
            try:
                parser.write(chunk)
            except python_multipart.exceptions.MultipartParseError as exc:
                raise UploadRejected(400, "Malformed multipart upload.") from exc
            if staged.received - file_bytes > limits.envelope:
                raise _too_large("Upload envelope (form fields and multipart framing)",
                                 limits.envelope)
            if pending:
                batch = pending[:]
                pending.clear()
                await run_in_threadpool(flush, batch)
            if on_progress is not None:
                on_progress(staged.received, declared)
        parser.finalize()
        if pending:
            await run_in_threadpool(flush, pending[:])
            pending.clear()
    finally:
        for handle in opened:
            if not handle.closed:
                handle.close()

    if staged.trace is None:
        raise UploadRejected(400, "No trace file in the upload.")
    if declared is not None and staged.received != declared:
        raise UploadRejected(400, "Upload ended before the declared length was received.")
    return staged
