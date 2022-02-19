import sys
import sched
from dataclasses import dataclass

sys.path.append(r'../')

from puslib import get_policy  # noqa: E402
from puslib.parameter import UInt16Parameter, UInt32Parameter  # noqa: E402
from puslib.services import Severity  # noqa: E402
from puslib.process import Process  # noqa: E402
from puslib.streams.console import ConsoleOutput  # noqa: E402


@dataclass
class _ParamCollection:
    param1: UInt32Parameter = UInt32Parameter(0)
    param2: UInt32Parameter = UInt32Parameter(0)
    param3: UInt16Parameter = UInt16Parameter(0)


class MyAppProcess(Process):
    def __init__(self, tm_output_stream, scheduler):
        super().__init__(10, tm_output_stream, scheduler,
                         housekeeping=False,
                         event_reporting=True,
                         function_management=True,
                         test=True)

        self.parameters = _ParamCollection()

        self._report = {0: self.parameters.param1, 1: self.parameters.param2}
        self.event1 = self._pus_service_5.add(eid=0,
                                              severity=Severity.INFO,
                                              params_in_report=self._report,
                                              trig_param=self.parameters.param1,
                                              to_value=10)
        self.event2 = self._pus_service_5.add(eid=1,
                                              severity=Severity.INFO,
                                              params_in_report=self._report,
                                              trig_param=self.parameters.param1,
                                              to_value=5)


tm_output_stream = ConsoleOutput()
scheduler = sched.scheduler()
my_process = MyAppProcess(tm_output_stream, scheduler)


@my_process.action(interval=1)
def step():
    my_process.parameters.param1.value += 1
    print("step")


@my_process.function(fid=0, args=(UInt16Parameter, UInt32Parameter))
def tc_test(arg1, arg2):
    print(f"tc_test({arg1}, {arg2})")
    return True


def inject_tc():
    tc_packet = get_policy().PusTcPacket(
        apid=10,
        name=0,
        service_type=8,
        service_subtype=1,
        data=bytes.fromhex("0000000300000007")
    )
    my_process.forward(tc_packet)


def inject_tc2():
    tc_packet = get_policy().PusTcPacket(
        apid=10,
        name=0,
        service_type=17,
        service_subtype=1
    )
    my_process.forward(tc_packet)


#scheduler.enter(2.5, 1, inject_tc)
#scheduler.enter(4.5, 1, inject_tc2)

scheduler.run()
