from cantracediag.api import normalize_local_path


def test_wsl_localhost_unc_path() -> None:
    raw = r"\\wsl.localhost\Ubuntu\home\paul\dev\WORK\Data_can\trace.asc"
    assert normalize_local_path(raw) == "/home/paul/dev/WORK/Data_can/trace.asc"


def test_wsl_dollar_unc_path() -> None:
    raw = r"\\wsl$\Ubuntu\home\paul\trace.asc"
    assert normalize_local_path(raw) == "/home/paul/trace.asc"


def test_windows_drive_path_maps_to_mnt() -> None:
    assert normalize_local_path(r"C:\data\trace.asc") == "/mnt/c/data/trace.asc"


def test_posix_path_unchanged() -> None:
    assert normalize_local_path("/home/paul/trace.asc") == "/home/paul/trace.asc"


def test_quotes_are_stripped() -> None:
    assert normalize_local_path('"/home/paul/trace.asc"') == "/home/paul/trace.asc"


def test_native_windows_keeps_drive_and_unc_paths() -> None:
    # req_034 AC7: the standalone Windows backend reads these paths directly.
    for raw in (
        r"C:\Données d'essai\trace 1.asc",
        r"\\wsl.localhost\Ubuntu\home\paul\clone\trace.asc",
        r"\\server\share\acquisitions\trace.asc",
    ):
        assert normalize_local_path(f'"{raw}"', platform="nt") == raw
