from functools import partial
from dataclasses import dataclass
from typing import Type

from puslib.packet import PusTcPacket, PusTmPacket, AckFlag
from puslib.time import CucTime
from puslib.parameter import Parameter, UInt8Parameter, UInt16Parameter


@dataclass(slots=True)
class Time:
    """Time related settings."""
    has_preamble: bool = True
    basic_unit_length: int = 4
    frac_unit_length: int = 2


@dataclass(slots=True)
class Telecommanding:
    """Telecommanding related settings."""
    source_id_type: Type[Parameter] | None = None


@dataclass(slots=True)
class Telemetry:
    """Telemetry related settings."""
    destination_id_type: Type[Parameter] | None = None
    msg_type_counter_type: Type[Parameter] | None = None
    time = Time()


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
        func = partial(
            CucTime.create,
            basic_unit_length=self.common.tm.time.basic_unit_length,
            frac_unit_length=self.common.tm.time.frac_unit_length,
            has_preamble=self.common.tm.time.has_preamble)
        return func(*args, **kwargs)

    def PusTcPacket(self, *args, **kwargs):  # pylint: disable=invalid-name
        func = partial(
            PusTcPacket.create,
            pus_version=self.common.pus_version,
            ack_flags=AckFlag.NONE,
            source=self.common.tc.source_id_type)
        return func(*args, **kwargs)

    def PusTmPacket(self, *args, **kwargs):  # pylint: disable=invalid-name
        func = partial(
            PusTmPacket.create,
            pus_version=self.common.pus_version,
            msg_type_counter=self.common.tm.msg_type_counter_type,
            destination=self.common.tm.destination_id_type)
        return func(*args, **kwargs)

    @dataclass(slots=True)
    class Common:
        """Policies common for all PUS services."""
        tc = Telecommanding()
        tm = Telemetry()
        pus_version = 1  # 1 - PUS rev A; 2 - PUS rev C
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
