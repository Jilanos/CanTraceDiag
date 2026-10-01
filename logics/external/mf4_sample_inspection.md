# External MF4 sample inspection

Read-only structural inspection on 2026-10-01 for the raw MF4 import and ASC export corpus. This is scoping evidence, not a working parser or a successful library import.

## Source locator and identity

The operator supplied an external recording named `00000002.MF4` in their Windows Downloads directory. Resolve that external path locally (the corresponding mounted Windows Downloads directory is accessible in this session). The recording stays outside the repository; do not commit it, its payloads or a converted operational ASC. Only this metadata note and synthetic fixtures belong in git.

- Size: 2,109,901 bytes.
- SHA-256: `e00a995c1fd4eb47111cad8cd12f7692dd15a176393ef2751e1ec9df5cd03099`.
- ID block: `UnFinMF`, MDF version `4.11`.
- Standard unfinished flags: `0x25`.
- Reachable metadata: one HD, one DG, one DT, 73 CG and 560 CN blocks.
- CG cycle counters are zero. The final DT starts at byte 106,776 and declares length 24 (header only), while 2,003,101 further bytes follow its header to EOF.
- The DG uses one-byte record IDs. Using CG fixed record widths or length-prefixed variable records, interpreting this final DT as extending to EOF consumes those trailing bytes exactly with no incomplete record.

## Provisional structural baseline

| Record ID | Acquisition group | Complete records |
| --- | --- | ---: |
| 32 | CAN9_Rx | 775 |
| 64 | CAN1_Rx | 116,838 |
| 66 | CAN1_Rx_IDE | 184 |
| Total | | 117,797 |

These are structural record counts under the unfinalized-DT recovery hypothesis, not independently verified decoded frames. An independent MDF library/tool must confirm IDs, timestamps, direction, bus IDs, lengths and payloads before treating the counts as an acceptance oracle. Document and explain any discrepancy instead of changing the baseline silently.

The schema also declares classic/FD, Rx/Tx, extended, remote/error CAN groups and LIN groups. Only the three groups above were populated in the structural scan. Declared schemas must not be mistaken for actual unsupported traffic. CAN_DataFrame fields include BusChannel, ID, IDE, DLC, DataLength, DataBytes, Dir, EDL, BRS and ESI; test actual unsupported traffic with synthetic fixtures.

## Implementation implications

- Recover this unfinished layout safely without changing the source; stale DT length and cycle counters cannot justify an empty success.
- Source integrity and finite valid frame values must be verified; unsafe/truncated recovery fails before publishing partial state.
- Preserve original sparse channels (1 and 9), extended identifiers, relative timestamps and known direction. Define deterministic inter-group chronological merging and tie order.
- Determine actual timestamp range/precision and confirm field semantics with an independent reader during the first implementation wave; they were not decoded in this inspection.
- Recompute the source hash after the manual MF4 -> ASC -> ASC re-import check, and record counts/value comparisons in task evidence without publishing operational data.
- No asammdf dependency was installed for this inspection and no product files were modified.

## Library references to evaluate

- [asammdf API](https://asammdf.readthedocs.io/en/stable/api.html): evaluate direct raw MDF4 group reads and safe unfinished-file handling.
- [python-can file IO](https://python-can.readthedocs.io/en/stable/file_io.html): MF4 is optional through asammdf; documentation includes structure restrictions, so do not assume broad third-party compatibility.
- [python-can MF4 implementation](https://python-can.readthedocs.io/en/stable/_modules/can/io/mf4.html): review metadata fidelity and resource behavior against the chosen installed version.
