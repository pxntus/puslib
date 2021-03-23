from functools import partial
from dataclasses import dataclass

from .packet import PusTcPacket, PusTmPacket
from .time import CucTime


@dataclass
class PusPolicy:
    # Basic CCSDS packets
    time: partial = partial(CucTime)
    create_tc_packet: partial = partial(PusTcPacket.create)
    deserialize_tc_packet: partial = partial(PusTcPacket.deserialize)
    create_tm_packet: partial = partial(PusTmPacket.create)
    deserialize_tm_packet: partial = partial(PusTmPacket.deserialize)
