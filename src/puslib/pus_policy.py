from functools import partial
from dataclasses import dataclass

from puslib.packet import PusTcPacket, PusTmPacket, AckFlag
from puslib.time import CucTime
from puslib.parameter import UInt8Parameter, UInt16Parameter


class PusPolicy:
    """Represent a PUS policy.

    The PUS policy is inspired by the policy-based design pattern.
    It controls the behaviour of the PUS binary format. Many parts of the PUS standard is
    undefined or mission-dependent. This policy collects a variety of such mission dependencies.

    The PUS policy consists of:
    - partial functions for creating PUS related primitives, e.g., TM and TC packets.
    - attributes defining types of various data fields.

    In order to create a mission-specific PUS policy, you can create your own policy
    class and register it with set_policy. The policy class must contain the same methods
    and attributes as this class.
    """

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

    @dataclass(slots=True)
    class Common:
        """Policies common for all PUS services.
        """
        param_id_type = UInt16Parameter

    @dataclass(slots=True)
    class RequestVerification:
        failure_code_type = UInt8Parameter

    @dataclass(slots=True)
    class Housekeeping:
        structure_id_type = UInt16Parameter
        collection_interval_type = UInt16Parameter
        count_type = UInt16Parameter
        periodic_generation_action_status_type = UInt8Parameter  # TM[3,35] & TM[3,36]

    @dataclass(slots=True)
    class EventReporting:
        event_definition_id_type = UInt16Parameter
        count_type = UInt8Parameter

    @dataclass(slots=True)
    class FunctionManagement:
        function_id_type = UInt16Parameter
        count_type = UInt8Parameter
