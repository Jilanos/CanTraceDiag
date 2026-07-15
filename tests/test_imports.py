from cantracediag import __version__
from cantracediag.models import DecodedSignalSample, RawCanFrame


def test_package_imports() -> None:
    assert __version__ == "0.1.0"


def test_models_are_instantiable() -> None:
    frame = RawCanFrame(
        timestamp_s=0.1,
        channel="CAN1",
        arbitration_id=0x123,
        is_extended_id=False,
        dlc=8,
        data=bytes.fromhex("0102030405060708"),
    )
    sample = DecodedSignalSample(
        timestamp_s=frame.timestamp_s,
        channel=frame.channel,
        arbitration_id=frame.arbitration_id,
        message_name="ExampleMessage",
        signal_name="ExampleSignal",
        value=12.3,
        unit="V",
    )

    assert frame.dlc == 8
    assert sample.value == 12.3
