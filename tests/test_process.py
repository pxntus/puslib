import sched
import warnings

import pytest

from puslib.ident import PusIdent
from puslib.packet import PusTcPacket, AckFlag
from puslib.process import Process
from puslib.services import RequestVerification
from puslib.services.service import PusService, PusServiceType
from puslib.streams.buffer import QueuedOutput
from puslib.streams.stream import OutputStream

APID = 10
CUSTOM_SERVICE = 130


class CustomService(PusService):
    def __init__(self, ident: PusIdent, pus_service_1: RequestVerification, tm_output_stream: OutputStream):
        super().__init__(CUSTOM_SERVICE, ident, pus_service_1, tm_output_stream, name="Custom", description="Custom service")
        self.received: list[bytes] = []
        self._register_sub_service(1, self._handler)

    def _handler(self, app_data: bytes | bytearray) -> bool:
        self.received.append(bytes(app_data))
        return True


def _create_process(tm_stream: QueuedOutput, **kwargs) -> Process:
    return Process(APID, tm_stream, sched.scheduler(), **kwargs)


def test_add_custom_service_and_forward_tc():
    tm_stream = QueuedOutput()
    process = _create_process(tm_stream)
    service = process.add_service(CustomService)

    assert service.service == CUSTOM_SERVICE
    assert service.name == "Custom"
    assert service.description == "Custom service"

    packet = PusTcPacket.create(apid=APID, name=0, ack_flags=AckFlag.NONE,
                                service_type=CUSTOM_SERVICE, service_subtype=1, data=b'\x01\x02')
    process.forward(packet)

    assert service.received == [b'\x01\x02']


def test_add_duplicate_service_raises():
    process = _create_process(QueuedOutput())
    process.add_service(CustomService)
    with pytest.raises(ValueError):
        process.add_service(CustomService)


def test_add_service_conflicting_with_standard_service_raises():
    process = _create_process(QueuedOutput(), test=True)
    with pytest.raises(ValueError), pytest.warns(UserWarning):
        process.add_service(lambda ident, pus_service_1, tm: PusService(17, ident, pus_service_1, tm))


@pytest.mark.parametrize("service_type", [-1, 256])
def test_service_type_out_of_range_raises(service_type):
    with pytest.raises(ValueError):
        PusService(service_type, PusIdent(APID))


@pytest.mark.parametrize("service_type", [0, 23, 127])
def test_custom_service_type_below_128_warns(service_type):
    with pytest.warns(UserWarning):
        PusService(service_type, PusIdent(APID))


@pytest.mark.parametrize("service_type", [128, 255])
def test_custom_service_type_from_128_does_not_warn(service_type):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        service = PusService(service_type, PusIdent(APID))
    assert service.service == service_type
    assert service.name == f"SERVICE_{service_type}"
    assert service.description == ""


def test_standard_service_type_properties_and_no_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        service = PusService(PusServiceType.TEST, PusIdent(APID))
    assert service.service == 17
    assert service.name == "TEST"
    assert service.description == "Test"
    assert service._service_type is PusServiceType.TEST  # pylint: disable=protected-access


def test_invalid_service_type_raises():
    with pytest.raises(TypeError):
        PusService("17", PusIdent(APID))  # type: ignore[arg-type]
