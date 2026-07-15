"""Command-line entry point for CanTraceDiag."""

from __future__ import annotations

from pathlib import Path

import typer

from cantracediag.dbc import DbcCatalog
from cantracediag.pipeline import import_trace

app = typer.Typer(help="Local analysis of CANalyzer ASC traces with DBC decoding.")


@app.command()
def info(
    trace: Path = typer.Argument(..., help="Path to a local .asc trace"),
    dbc: list[Path] = typer.Option([], "--dbc", "-d", help="Local DBC file(s)"),
) -> None:
    """Import a trace and print a summary without launching the UI."""
    store, result = import_trace(trace, list(dbc))
    s = result.summary
    typer.echo(f"Trace: {result.trace_path}  (base {result.asc_base})")
    typer.echo(f"DBC:   {', '.join(result.dbc_paths) or '(none)'}")
    typer.echo(
        f"Frames: {s['frames']}  decoded: {s['decoded_frames']}  "
        f"events: {s['events']}  unique ids: {s['unique_ids']}"
    )
    typer.echo(f"Time:   {s['start_s']}s .. {s['end_s']}s")
    if result.ambiguous_ids:
        typer.echo("Ambiguous ids across DBCs:")
        for frame_id, names in result.ambiguous_ids.items():
            typer.echo(f"  {hex(frame_id)}: {', '.join(names)}")
    store.close()


@app.command()
def signals(
    dbc: list[Path] = typer.Argument(..., help="Local DBC file(s) to inspect"),
) -> None:
    """List messages and signals available in the given DBC files."""
    catalog = DbcCatalog()
    for path in dbc:
        catalog.load(path)
    for sig in catalog.signals():
        unit = f" [{sig.unit}]" if sig.unit else ""
        typer.echo(f"{sig.message_name}.{sig.signal_name}{unit}  ({hex(sig.arbitration_id)})")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind host (localhost by default)"),
    port: int = typer.Option(8000, help="Bind port"),
) -> None:
    """Launch the local web UI and query API."""
    import uvicorn

    typer.echo(f"CanTraceDiag UI on http://{host}:{port}")
    uvicorn.run("cantracediag.api:app", host=host, port=port, log_level="info")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
