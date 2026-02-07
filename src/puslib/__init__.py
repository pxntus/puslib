from puslib.packet import PusTcPacket, PusTmPacket, AckFlag  # noqa: F401
from puslib.time import CucTime  # noqa: F401
from puslib.pus_policy import PusPolicy

__version__ = "0.3.0"

_pus_policy = PusPolicy()


def set_policy(policy):
    """Set PUS policy to be used.

    A PUS policy is an object defining various properties of the PUS implementation,
    e.g., various field lengths. This is due to that many parts of the PUS standard
    are mission-specific.

    The PUS policy is set on a global scope, thus, multiple simultaneous PUS policies
    are not supported. Might need to be reviewed in the future.

    Arguments:
        policy -- PUS policy
    """
    global _pus_policy  # pylint: disable=global-statement
    _pus_policy = policy


def get_policy():
    """Get the current selected PUS policy.

    Returns:
        PUS policy
    """
    return _pus_policy
