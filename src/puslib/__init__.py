from puslib.packet import PusTcPacket, PusTmPacket, AckFlag  # noqa: F401
from puslib.time import CucTime  # noqa: F401
from puslib.pus_policy import PusPolicy

__version__ = "0.2.5"

_pus_policy = PusPolicy()


def set_policy(policy):
    global _pus_policy  # pylint: disable=global-statement
    _pus_policy = policy


def get_policy():
    return _pus_policy
