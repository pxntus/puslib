import sys
import sched

sys.path.append(r'../')

from puslib import get_pus_policy  # noqa: E402
from puslib.process import Process  # noqa: E402
from puslib.parameter import UInt16Parameter, UInt32Parameter  # noqa: E402
from puslib.distributor import TmDistributor  # noqa: E402
from puslib.streams.console import ConsoleOutput  # noqa: E402


tm_output_stream = ConsoleOutput()
tm_distributor = TmDistributor(tm_output_stream)
scheduler = sched.scheduler()

my_process = Process(10, tm_distributor, scheduler, function_management=True, test=True)


@my_process.action(interval=1)
def step():
    print("step")


@my_process.function(fid=0, args=(UInt16Parameter, UInt32Parameter))
def tc_test(arg1, arg2):
    print(f"tc_test({arg1}, {arg2})")
    return True


def inject_tc():
    tc_packet = get_pus_policy().PusTcPacket(
        apid=10,
        name=0,
        service_type=8,
        service_subtype=1,
        data=bytes.fromhex("0000000300000007")
    )
    my_process.forward(tc_packet)


def inject_tc2():
    tc_packet = get_pus_policy().PusTcPacket(
        apid=10,
        name=0,
        service_type=17,
        service_subtype=1
    )
    my_process.forward(tc_packet)


scheduler.enter(2.5, 1, inject_tc)
scheduler.enter(4.5, 1, inject_tc2)

scheduler.run()
