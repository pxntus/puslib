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

    The policy is stored as a module-level global and is not thread-safe. This is a
    deliberate design choice: the library assumes a single-threaded execution model
    where the policy is set once at startup and remains unchanged for the lifetime of
    the application. Calling set_policy() from multiple threads, or changing the policy
    while packets are being processed, results in undefined behavior.

    If per-thread policies are ever required, replace this global with a
    contextvars.ContextVar to give each thread or async task its own policy instance.

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
