# Windows standalone qualification -- 1 GiB ASC (2026-10-19)

Evidence for req_034 / task_049. Only anonymized facts are recorded: counts,
hashes, timings, memory and hardware. No operational trace, payload, DBC content
or machine-specific path is included.

## What was measured

| Item | Value |
| --- | --- |
| Executable | `CanTraceDiag-1.3.0-windows-x64.exe`, local build of commit `0c094f2` (PyInstaller 6.16.0, CPython 3.13.15), 88,676,361 bytes, SHA-256 `e48918e3e98782e03a7ccad162e45ac03c4f6bc07a7ade20546b6d399257bbe3`, unsigned |
| OS | Windows 11 Professionnel 10.0.26300, x64 |
| CPU / RAM / storage | Intel Core i7-12700H (14 cores, 20 threads) / 16 GiB / Samsung NVMe SSD |
| Browser | Google Chrome 155.0.8059.82 (driven by Playwright, `channel=chrome`) |
| Harness | `scripts/qualify_windows_large_asc.py` (service and browser process trees sampled every 0.25 s; per-process peak working sets summed) |
| Fixture | `scripts/generate_large_asc.py --size 1073741824` (seed 20261019): exactly 1,073,741,824 bytes, SHA-256 `aa633f4c94b9b9f540c26ab4c019ec57dc4c6af2c95bc4840c97d928ee4a729e` |
| Fixture content | 18,728,198 classic data frames (4,163,174 extended ids, 1,388,464 on sparse channel 9, Rx and Tx), 193,076 equal-timestamp lines, 62 malformed records, 74 error frames, 37 status events, 8 ids, 6,024.79 s |
| DBC density | 6 messages / 15 signals; 17,340,008 of 18,728,198 frames (92.6 %) resolve to a DBC message |

## Results against the AC4 budgets

Verdicts compare the measured number directly with the stated limit.

| Criterion (req_034 AC4) | Limit | Measured | Verdict |
| --- | --- | --- | --- |
| 1 GiB import usable (upload to ready), API upload | <= 15 min (900 s) | 391.7 s | met |
| 1 GiB import usable, through the browser UI file picker | <= 900 s | 432.3 s | met |
| Peak service process-tree working set | <= 6 GiB (6,442,450,944 B) | 2,253,631,488 B (sum of per-process peaks) | met |
| Peak dedicated-browser working set | <= 2 GiB (2,147,483,648 B) | 1,065,050,112 B (sum of per-process peaks) | met |
| Warm p95, 200-row filtered trace page (20 interactions) | <= 2 s | API 0.933 s; UI 0.646 s | met |
| Warm p95, two signals <= 4,000 points (20 interactions) | <= 3 s | API 0.455 s | met |
| Warm p95, two-signal A/B cursor lookup (20 interactions) | <= 1 s | API 0.313 s; UI 0.327 s | met |
| Indexing cancellation acknowledged | <= 5 s | 0.21 s (API run), 0.32 s (UI run) | met |

## Boundary, fidelity and recovery (AC1-AC3, AC10)

| Check | Result |
| --- | --- |
| 1 GiB + 1 byte trace part, with Content-Length | 413 "Trace file exceeds the 1 GiB (1,073,741,824 bytes) limit.", no staging left, no analysis published |
| 1 GiB + 1 byte, chunked (no Content-Length) | 413, same message |
| 1 GiB - 1 byte | accepted, 18,728,198 frames |
| Exactly 1 GiB | accepted, frames and events equal the fixture manifest |
| Raw ASC export vs source, frame by frame (timestamp to 1 us, channel, id, extended flag, direction, DLC, payload) | 18,728,198 compared, 0 mismatches |
| Source unchanged | SHA-256 identical before and after |
| Cancel during transfer | 409, previous analysis kept, staging removed |
| Cancel during indexing | 409, previous analysis kept, staging removed, one analysis directory |
| Index size on disk | 377-378 MB |

## External acquisition (supplementary, AC10)

The externally converted/concatenated acquisition named in the request was
imported by the same executable, read in place from a `\\wsl.localhost` share
(no DBC, no copy into the repository).

| Item | Value |
| --- | --- |
| Size / SHA-256 | 668,097,985 bytes / `eded5296dac635a5284c0235db63ff70b8daf2a09573ddb5440f6327c7d9aa81` (unchanged after the run) |
| Imported | 10,613,470 frames, 0 events, 45 ids, 0.198 s to 5,389.987 s |
| Upload to ready | 238.0 s |
| Peak service process-tree working set | 1,081,487,360 B |
| Raw ASC export vs source, frame by frame | 10,613,470 compared, 0 mismatches |

## Packaged smoke and launcher (AC5-AC9)

The same executable passes `packaging/windows/smoke.py` (16/16: scrubbed
environment without Python on PATH, per-user and data paths with spaces and
non-ASCII characters, occupied preferred port, ASC+DBC/TRC/BLF/raw-CAN MF4
imports, plots, trace page, cursors, report, CSV and raw-ASC exports, native
non-ASCII path import, second-launch attach, `--stop`, restart restore) and
`packaging/windows/test_launcher.py` (13/13: missing release, development
commit, wrong architecture, checksum/provenance mismatch, incomplete and altered
downloads, verified download and run, offline cache, corrupted cache, network
failure, packed refs, explicit `-Release`, checkout on a `\\wsl.localhost`
share).

## Reservations (not part of the verdicts above)

- The qualified file is a local build. The release workflow rebuilds the
  executable from the tag with the same pinned constraints; that published
  artifact has a different SHA-256 and is smoke- and launcher-tested in CI, but
  this full-size run has not been repeated on it.
- Cold first plot (not budgeted by AC4): the first full-range request for two
  signals took 23.9 s through the API and 42.9 s through the UI, because a
  signal is decoded on first use. Warm figures above apply afterwards.
- One reference machine was measured; its CPU exceeds the four-core minimum.
  Memory was sampled at 0.25 s; the reported value is the sum of each process's
  own peak working set, which is not lower than the true simultaneous peak.
- The browser was driven by Playwright with a fresh profile; UI latencies are
  timed inside the page (request plus render).
