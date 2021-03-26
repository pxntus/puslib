import struct
from functools import partial
from dataclasses import dataclass

from .packet import PusTcPacket, PusTmPacket
from .time import CucTime
from .parameter import Parameter, UInt16Parameter


@dataclass
class PusPolicy:
    # Basic CCSDS packets
    time: partial = partial(CucTime)
    create_tc_packet: partial = partial(PusTcPacket.create)
    deserialize_tc_packet: partial = partial(PusTcPacket.deserialize)
    create_tm_packet: partial = partial(PusTmPacket.create)
    deserialize_tm_packet: partial = partial(PusTmPacket.deserialize)

    EnumerateParameter: Parameter = UInt16Parameter

    # PUS 8: Function Management
    function_id_type: struct.Struct = struct.Struct('>H')

    def __post_init__(self):
        tmp = self.EnumerateParameter('')
        self.enumerate_struct = struct.Struct(tmp.format)
