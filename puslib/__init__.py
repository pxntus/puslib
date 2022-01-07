import sys
from functools import partial
from dataclasses import dataclass

_MIN_PYTHON = (3, 7)
if sys.version_info < _MIN_PYTHON:
    sys.exit(f"Python {_MIN_PYTHON[0]}.{_MIN_PYTHON[1]} or later is required.\n", 1)

__version__ = "0.1.0"


from .packet import PusTcPacket, PusTmPacket, AckFlag  # noqa: E402
from .time import CucTime  # noqa: E402
from .parameter import UInt8Parameter, UInt16Parameter  # noqa: E402


class PusPolicy:
    def __init__(self):
        self.common = self.Common
        self.request_verification = self.RequestVerification
        self.housekeeping = self.Housekeeping

    @property
    def CucTime(self):
        return partial(CucTime.create, 4, 2, has_preamble=True)

    @property
    def PusTcPacket(self):
        return partial(PusTcPacket.create, ack_flags=AckFlag.ACCEPTANCE, has_source_field=False)

    @property
    def PusTmPacket(self):
        return partial(PusTmPacket.create, has_type_counter_field=False, has_destination_field=False)

    # Common PUS Service related types

    @property
    def IdType(self):
        return UInt16Parameter

    @property
    def NType(self):
        return UInt8Parameter

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


_pus_policy = PusPolicy()


def set_pus_policy(policy):
    global _pus_policy
    _pus_policy = policy


def get_pus_policy():
    return _pus_policy
