import sched
import warnings

import pytest

from puslib.exceptions import TcPacketRoutingError
from puslib.ident import PusIdent
from puslib.packet import PusTcPacket, AckFlag
from puslib.parameter import UInt16Parameter
from puslib.process import Process, Router
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


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, delay: float) -> None:
        self.now += delay


def _create_tc(service_type: int, service_subtype: int, apid: int = APID, data: bytes | None = None) -> PusTcPacket:
    return PusTcPacket.create(apid=apid, name=0, ack_flags=AckFlag.NONE,
                              service_type=service_type, service_subtype=service_subtype, data=data)


def test_forward_tc_with_wrong_apid_raises():
    process = Process(APID, QueuedOutput(), sched.scheduler(), test=True)
    with pytest.raises(TcPacketRoutingError):
        process.forward(_create_tc(17, 1, apid=APID + 1))


def test_forward_tc_to_missing_service_raises():
    process = Process(APID, QueuedOutput(), sched.scheduler(), test=False)
    with pytest.raises(TcPacketRoutingError):
        process.forward(_create_tc(17, 1))


def test_forward_tc_to_enabled_standard_service():
    tm_stream = QueuedOutput()
    process = Process(APID, tm_stream, sched.scheduler(), test=True)
    process.forward(_create_tc(17, 1))
    report = tm_stream.get()
    assert report is not None
    assert (report.service, report.subservice) == (17, 2)


def test_function_without_function_management_raises():
    process = Process(APID, QueuedOutput(), sched.scheduler())
    with pytest.raises(RuntimeError):
        process.function(fid=0, args=())(lambda: True)


def test_function_is_called_by_tc():
    process = Process(APID, QueuedOutput(), sched.scheduler(), function_management=True)
    calls = []

    @process.function(fid=3, args=(UInt16Parameter,))
    def _func(arg1):
        calls.append(arg1)
        return True

    process.forward(_create_tc(8, 1, data=bytes.fromhex("00030007")))
    assert calls == [7]


def test_action_runs_periodically():
    clock = FakeClock()
    scheduler = sched.scheduler(clock.time, clock.sleep)
    process = Process(APID, QueuedOutput(), scheduler)
    runs = 0

    @process.action(interval=1)
    def _step():
        nonlocal runs
        runs += 1

    assert runs == 1  # first run immediately when added
    for now, expected_runs in ((0.9, 1), (1.0, 2), (2.5, 3)):
        clock.now = now
        scheduler.run(blocking=False)
        assert runs == expected_runs


def test_router_forwards_tc_by_apid():
    router = Router()
    services = {}
    for apid in (10, 20):
        process = Process(apid, QueuedOutput(), sched.scheduler())
        services[apid] = process.add_service(CustomService)
        router.register(process)

    router.forward(_create_tc(CUSTOM_SERVICE, 1, apid=20, data=b'\x01'))
    assert services[10].received == []  # no TC routed here
    assert services[20].received == [b'\x01']


def test_router_register_duplicate_apid_raises():
    router = Router()
    router.register(Process(APID, QueuedOutput(), sched.scheduler()))
    with pytest.raises(ValueError):
        router.register(Process(APID, QueuedOutput(), sched.scheduler()))


def test_router_forward_tc_to_unknown_apid_raises():
    router = Router()
    router.register(Process(APID, QueuedOutput(), sched.scheduler()))
    with pytest.raises(TcPacketRoutingError):
        router.forward(_create_tc(17, 1, apid=APID + 1))


def test_add_custom_service_and_forward_tc():
    tm_stream = QueuedOutput()
    process = Process(APID, tm_stream, sched.scheduler())
    service = process.add_service(CustomService)

    assert service.service == CUSTOM_SERVICE
    assert service.name == "Custom"
    assert service.description == "Custom service"

    packet = PusTcPacket.create(apid=APID, name=0, ack_flags=AckFlag.NONE,
                                service_type=CUSTOM_SERVICE, service_subtype=1, data=b'\x01\x02')
    process.forward(packet)

    assert service.received == [b'\x01\x02']


def test_add_duplicate_service_raises():
    process = Process(APID, QueuedOutput(), sched.scheduler())
    process.add_service(CustomService)
    with pytest.raises(ValueError):
        process.add_service(CustomService)


def test_add_service_conflicting_with_standard_service_raises():
    process = Process(APID, QueuedOutput(), sched.scheduler(), test=True)
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
