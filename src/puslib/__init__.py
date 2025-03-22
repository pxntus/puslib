from functools import partial
from dataclasses import dataclass

from puslib.packet import PusTcPacket, PusTmPacket, AckFlag  # noqa: E402
from puslib.time import CucTime  # noqa: E402
from puslib.parameter import UInt8Parameter, UInt16Parameter  # noqa: E402

__version__ = "0.2.5"


class PusPolicy:
    def __init__(self):
        self.common = self.Common
        self.request_verification = self.RequestVerification
        self.housekeeping = self.Housekeeping
        self.event_reporting = self.EventReporting
        self.function_management = self.FunctionManagement

    def CucTime(self, *args, **kwargs):  # pylint: disable=invalid-name
        func = partial(CucTime.create,
                       basic_unit_length=4,
                       frac_unit_length=2,
                       has_preamble=True)
        return func(*args, **kwargs)

    def PusTcPacket(self, *args, **kwargs):  # pylint: disable=invalid-name
        func = partial(PusTcPacket.create,
                       pus_version=1,
                       ack_flags=AckFlag.ACCEPTANCE,
                       source=None)
        return func(*args, **kwargs)

    def PusTmPacket(self, *args, **kwargs):  # pylint: disable=invalid-name
        func = partial(PusTmPacket.create,
                       pus_version=1,
                       msg_type_counter=None,
                       destination=None)
        return func(*args, **kwargs)

    @dataclass
    class Common:
        """Policies common for all PUS services.
        """
        param_id_type = UInt16Parameter

    @dataclass
    class RequestVerification:
        failure_code_type = UInt8Parameter

    @dataclass
    class Housekeeping:
        structure_id_type = UInt16Parameter
        collection_interval_type = UInt16Parameter
        count_type = UInt16Parameter
        periodic_generation_action_status_type = UInt8Parameter  # TM[3,35] & TM[3,36]

    @dataclass
    class EventReporting:
        event_definition_id_type = UInt16Parameter
        count_type = UInt8Parameter

    @dataclass
    class FunctionManagement:
        function_id_type = UInt16Parameter
        count_type = UInt8Parameter


_pus_policy = PusPolicy()


def set_policy(policy):
    global _pus_policy  # pylint: disable=global-statement
    _pus_policy = policy


def get_policy():
    return _pus_policy
