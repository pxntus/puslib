import struct
from enum import IntEnum, IntFlag
from dataclasses import dataclass
from typing import Optional

from .exceptions import CrcException, IncompletePacketException, InvalidPacketException
from .time import CucTime
from .crc_ccitt import calculate as crc_ccitt_calculate

CCSDS_PACKET_VERSION_NUMBER = 0
CCSDS_MAX_PACKET_SIZE = 65542

TM_PACKET_PUS_VERSION_NUMBER = 2
TC_PACKET_PUS_VERSION_NUMBER = 2

IDLE_APID = 0b11111111111

_COMMON_SEC_HDR_STRUCT = struct.Struct('>BBB')
_PEC_FIELD_SIZE = 2


def _validate_int_field(field_name, val, min_val, max_val):
    if isinstance(val, int):
        if not min_val <= val <= max_val:
            raise InvalidPacketException(f"{field_name} must be between {min_val} and {max_val}")
    else:
        raise TypeError(f"{field_name} must be an integer")


def _validate_bool_field(field_name, val):
    if not isinstance(val, bool):
        raise TypeError(f"{field_name} must be a bool")


class PacketType(IntEnum):
    TM = 0
    TC = 1


class SequenceFlag(IntEnum):
    CONTINUATION_SEGMENT = 0b00
    FIRST_SEGMENT = 0b01
    LAST_SEGMENT = 0b10
    UNSEGMENTED = 0b11


@dataclass
class _PacketPrimaryHeader:
    packet_version_number: int = CCSDS_PACKET_VERSION_NUMBER

    # Packet ID
    packet_type: PacketType = PacketType.TM
    secondary_header_flag: bool = True
    apid: int = 0

    # Packet sequence control
    seq_flags: SequenceFlag = SequenceFlag.UNSEGMENTED
    seq_count_or_name: int = 0

    data_length: int = 0


class CcsdsSpacePacket:
    _CCSDS_HDR_STRUCT = struct.Struct('>HHH')

    def __init__(self, has_pec=True):
        self.header = _PacketPrimaryHeader()
        self.secondary_header = None
        self.payload = bytes()
        self._has_pec = has_pec

    def __len__(self):
        return self._CCSDS_HDR_STRUCT.size + (len(self.payload) if self.payload else 0) + (2 if self._has_pec else 0)

    def __bytes__(self):
        return self.serialize()

    def __str__(self):
        pkt_info = f"{self.header.packet_type.name} Packet\n"
        pkt_info += f"  APID: {self.header.apid}\n"
        pkt_info += f"  Sequence count: {self.header.seq_count_or_name}\n"
        return pkt_info

    @property
    def packet_type(self):
        return self.header.packet_type

    @property
    def apid(self):
        return self.header.apid

    @property
    def has_pec(self):
        return self._has_pec

    def serialize(self):
        packet_id = self.header.packet_version_number << 13 | (1 if self.header.packet_type == PacketType.TC else 0) << 12 | (1 if self.header.secondary_header_flag else 0) << 11 | self.header.apid
        seq_ctrl = self.header.seq_flags << 14 | self.header.seq_count_or_name
        ccsds_header = self._CCSDS_HDR_STRUCT.pack(packet_id, seq_ctrl, self.header.data_length)
        if self.header.secondary_header_flag:
            packet_data_field = b''  # Leave it to subclasses to handle data field
        else:
            packet_data_field = self.payload
        return ccsds_header + packet_data_field

    def request_id(self):
        packet_id = self.header.packet_version_number << 13 | (1 if self.header.packet_type == PacketType.TC else 0) << 12 | (1 if self.header.secondary_header_flag else 0) << 11 | self.header.apid
        seq_ctrl = self.header.seq_flags << 14 | self.header.seq_count_or_name
        return struct.pack('>HH', packet_id, seq_ctrl)

    @classmethod
    def deserialize(cls, buffer, has_pec=True, validate_pec=True):
        packet_id, seq_ctrl, data_length = cls._CCSDS_HDR_STRUCT.unpack_from(buffer)

        packet_size = cls._CCSDS_HDR_STRUCT.size + data_length + 1
        if packet_size > len(buffer):
            raise IncompletePacketException()
        if packet_size > CCSDS_MAX_PACKET_SIZE:
            raise InvalidPacketException("Packet too large")
        if has_pec and validate_pec:
            mem_view = memoryview(buffer)
            if crc_ccitt_calculate(mem_view[:packet_size]) != 0:
                raise CrcException

        packet_version_number = (packet_id >> 13) & 0b111
        packet_type = PacketType.TC if (packet_id >> 12) & 0b1 == 1 else PacketType.TM
        secondary_header_flag = True if (packet_id >> 11) & 0b1 == 1 else False
        apid = packet_id & 0x7ff
        seq_flags = (seq_ctrl >> 14) & 0b11
        seq_count_or_name = seq_ctrl & 0x3fff  # count or name
        return packet_version_number, packet_type, secondary_header_flag, apid, seq_flags, seq_count_or_name, data_length

    @classmethod
    def create(cls, **kwargs):
        packet = cls(kwargs.get('has_pec', True))

        packet_version_number = kwargs.get('packet_version_number', CCSDS_PACKET_VERSION_NUMBER)
        _validate_int_field('Packet version number', packet_version_number, 0, 0)
        packet.header.packet_version_number = packet_version_number

        packet_type = kwargs.get('packet_type', PacketType.TM)
        if not isinstance(packet_type, PacketType):
            raise TypeError("Packet type must be a PacketType")
        packet.header.packet_type = packet_type

        secondary_header_flag = kwargs.get('secondary_header_flag', True)
        _validate_bool_field('Secondary header flag', secondary_header_flag)
        packet.header.secondary_header_flag = secondary_header_flag

        apid = kwargs.get('apid', IDLE_APID)
        _validate_int_field('apid', apid, 0, 0x7ff)
        packet.header.apid = apid

        seq_flags = kwargs.get('seq_flags', SequenceFlag.UNSEGMENTED)
        packet.header.seq_flags = seq_flags

        seq_count = kwargs.get('seq_count_or_name', 0)
        _validate_int_field('Sequence count or name', seq_count, 0, 0x3fff)
        packet.header.seq_count_or_name = seq_count

        data = kwargs.get('data', None)
        if isinstance(data, (bytearray, bytes, type(None))):
            if data is None:
                data = bytes()
            packet.payload = data
        else:
            raise TypeError("Application data must be None, bytes or a bytearray")

        data_length = kwargs.get('data_length', None)
        data_size_except_source_data = kwargs.get('secondary_header_length', 0) + (2 if packet.has_pec else 0)
        max_data_size = CCSDS_MAX_PACKET_SIZE - cls._CCSDS_HDR_STRUCT.size - data_size_except_source_data
        if data_length:
            min_data_size = data_size_except_source_data
            _validate_int_field('Data length', data_length + 1, min_data_size, max_data_size)
            if data_size_except_source_data + (len(packet.payload) if packet.payload else 0) != data_length + 1:
                raise InvalidPacketException("Mismatch between packet data length and packet data field")
        else:
            data_length = data_size_except_source_data + (len(packet.payload) if packet.payload else 0)
            if data_length > max_data_size:
                raise ValueError("Application data too large")
            if data_length > 0:
                data_length -= 1
        packet.header.data_length = data_length

        return packet


class AckFlag(IntFlag):
    NONE = 0b0000
    ACCEPTANCE = 0b0001
    START_OF_EXECUTION = 0b0010
    PROGRESS = 0b0100
    COMPLETION = 0b1000


@dataclass
class _PacketSecondaryHeaderTc:
    pus_version: int = TC_PACKET_PUS_VERSION_NUMBER
    ack_flags: AckFlag = AckFlag.NONE
    service_type: int = 0
    service_subtype: int = 0
    source: Optional[int] = None


class PusTcPacket(CcsdsSpacePacket):
    _SOURCE_FIELD_SIZE = 2

    def __init__(self, has_pec=True):
        super().__init__(has_pec)
        self.secondary_header = _PacketSecondaryHeaderTc()

    def __len__(self):
        size = super().__len__()
        if self.header.secondary_header_flag:
            size += _COMMON_SEC_HDR_STRUCT.size
            if self.secondary_header.source is not None:
                size += self._SOURCE_FIELD_SIZE
        return size

    def __str__(self):
        pkt_info = super().__str__()
        if self.header.secondary_header_flag:
            pkt_info += f"  Service type: {self.secondary_header.service_type}\n"
            pkt_info += f"  Service subtype: {self.secondary_header.service_subtype}\n"
            if self.payload:
                pkt_info += f"  Application data: 0x{self.payload.hex()}"
        return pkt_info

    @property
    def name(self):
        return self.header.seq_count_or_name

    def ack(self, ack_flag):
        return ack_flag in self.secondary_header.ack_flags

    @property
    def service(self):
        return self.secondary_header.service_type

    @property
    def subservice(self):
        return self.secondary_header.service_subtype

    @property
    def source(self):
        return self.secondary_header.source

    @property
    def app_data(self):
        return self.payload

    def serialize(self):
        ccsds_header = super().serialize()

        # First static part of secondary header
        tmp = self.secondary_header.pus_version << 4 | self.secondary_header.ack_flags
        values = [tmp, self.secondary_header.service_type, self.secondary_header.service_subtype]
        ccsds_sec_header_static = _COMMON_SEC_HDR_STRUCT.pack(*values)

        # Last "optional" part of secondary header
        if self.secondary_header.source is not None:
            ccsds_sec_header_source = self.secondary_header.source.to_bytes(self._SOURCE_FIELD_SIZE, byteorder='big')
        else:
            ccsds_sec_header_source = bytes()

        # Packet error control
        packet_without_pec = ccsds_header + ccsds_sec_header_static + ccsds_sec_header_source + self.payload
        if self.has_pec:
            mem_view = memoryview(packet_without_pec)
            pec = crc_ccitt_calculate(mem_view)
            pec = pec.to_bytes(_PEC_FIELD_SIZE, byteorder='big')
        else:
            pec = bytes()

        return packet_without_pec + pec

    @classmethod
    def deserialize(cls, buffer, has_source_field=True, has_pec=True, validate_fields=True, validate_pec=True):
        packet_version_number, packet_type, secondary_header_flag, apid, seq_flags, seq_count_or_name, data_length = super(cls, cls).deserialize(buffer, has_pec, validate_pec)
        offset = cls._CCSDS_HDR_STRUCT.size

        data_field_except_source_length = ((_COMMON_SEC_HDR_STRUCT.size + (2 if has_source_field else 0)) if secondary_header_flag else 0) + (2 if has_pec else 0)
        if len(buffer) < cls._CCSDS_HDR_STRUCT.size + data_field_except_source_length:
            raise IncompletePacketException()

        if secondary_header_flag:
            # First static part of secondary header
            tmp, service_type, service_subtype = _COMMON_SEC_HDR_STRUCT.unpack_from(buffer, offset)
            pus_version = (tmp >> 4) & 0b1111
            ack_flags = AckFlag(tmp & 0b1111)
            offset += _COMMON_SEC_HDR_STRUCT.size

            # Last "optional" part of secondary header
            if has_source_field:
                source = int.from_bytes(buffer[offset:offset + cls._SOURCE_FIELD_SIZE], byteorder='big')
                offset += cls._SOURCE_FIELD_SIZE
            else:
                source = None
        else:
            pus_version = None
            ack_flags = None
            service_type = None
            service_subtype = None
            source = None

        # User data field
        app_data_length = data_length + 1 - data_field_except_source_length
        app_data = bytes(buffer[offset:offset + app_data_length]) if app_data_length else None

        packet_length = cls._CCSDS_HDR_STRUCT.size + data_length + 1

        if validate_fields:
            packet = cls.create(has_pec=has_pec,
                packet_version_number=packet_version_number,
                packet_type=packet_type,
                secondary_header_flag=secondary_header_flag,
                apid=apid,
                seq_flags=seq_flags,
                name=seq_count_or_name,
                data_length=data_length,
                pus_version=pus_version,
                ack_flags=ack_flags,
                service_type=service_type,
                service_subtype=service_subtype,
                source=source,
                data=app_data)
        else:
            packet = cls(has_pec)
            packet.header.packet_version_number = packet_version_number
            packet.header.packet_type = packet_type
            packet.header.secondary_header_flag = secondary_header_flag
            packet.header.apid = apid
            packet.header.seq_flags = seq_flags
            packet.header.seq_count_or_name = seq_count_or_name
            packet.header.data_length = data_length
            packet.payload = app_data
            packet.secondary_header.pus_version = pus_version
            packet.secondary_header.ack_flags = ack_flags
            packet.secondary_header.service_type = service_type
            packet.secondary_header.service_subtype = service_subtype
            packet.secondary_header.source = source

        return packet_length, packet

    @classmethod
    def create(cls, **kwargs):
        source = kwargs.get('source', None)

        if kwargs.get('secondary_header_flag', True):
            secondary_header_length = _COMMON_SEC_HDR_STRUCT.size + (2 if source is not None else 0)
            kwargs['secondary_header_length'] = secondary_header_length
        kwargs['packet_type'] = PacketType.TC
        kwargs['seq_count_or_name'] = kwargs.get('name', 0)
        packet = super(cls, cls).create(**kwargs)

        if packet.header.secondary_header_flag:
            pus_version = kwargs.get('pus_version', TC_PACKET_PUS_VERSION_NUMBER)
            if pus_version is not None:
                _validate_int_field('TC packet PUS version', pus_version, 0, 0b1111)
                packet.secondary_header.pus_version = pus_version

            ack_flags = kwargs.get('ack_flags', AckFlag.NONE)
            if ack_flags is not None:
                _validate_int_field('Acknowledgement flags', ack_flags, 0, 0b1111)
                packet.secondary_header.ack_flags = ack_flags

            service_type = kwargs.get('service_type', None)
            if service_type is not None:
                _validate_int_field('Service type', service_type, 0, 255)
                packet.secondary_header.service_type = service_type

            service_subtype = kwargs.get('service_subtype', None)
            if service_subtype is not None:
                _validate_int_field('Service subtype', service_subtype, 0, 255)
                packet.secondary_header.service_subtype = service_subtype

            if source is not None:
                _validate_int_field('Source ID', source, 0, 0xffff)
                packet.secondary_header.source = source

        return packet


@dataclass
class _PacketSecondaryHeaderTm:
    pus_version: Optional[int] = TM_PACKET_PUS_VERSION_NUMBER
    spacecraft_time_ref_status: Optional[int] = None
    service_type: Optional[int] = None
    service_subtype: Optional[int] = None
    msg_type_counter: Optional[int] = None
    destination: Optional[int] = None
    time: Optional[CucTime] = None


class PusTmPacket(CcsdsSpacePacket):
    _MSG_TYPE_COUNTER_FIELD_SIZE = 2
    _DESTINATION_FIELD_SIZE = 2

    def __init__(self, has_pec=True):
        super().__init__(has_pec)
        self.secondary_header = _PacketSecondaryHeaderTm()

    def __len__(self):
        size = super().__len__()
        if self.header.secondary_header_flag:
            size += _COMMON_SEC_HDR_STRUCT.size
            if self.secondary_header.msg_type_counter is not None:
                size += self._MSG_TYPE_COUNTER_FIELD_SIZE
            if self.secondary_header.destination is not None:
                size += self._DESTINATION_FIELD_SIZE
            size += len(self.secondary_header.time)
        return size

    def __str__(self):
        pkt_info = super().__str__()
        if self.header.secondary_header_flag:
            pkt_info += f"  Service type: {self.secondary_header.service_type}\n"
            pkt_info += f"  Service subtype: {self.secondary_header.service_subtype}\n"
            pkt_info += f"  CUC timestamp: {self.secondary_header.time}\n"
            if self.payload:
                pkt_info += f"  Source data: 0x{self.payload.hex()}"
        return pkt_info

    @property
    def seq_count(self):
        return self.header.seq_count_or_name

    @property
    def service(self):
        return self.secondary_header.service_type

    @property
    def subservice(self):
        return self.secondary_header.service_subtype

    @property
    def counter(self):
        return self.secondary_header.msg_type_counter

    @property
    def destination(self):
        return self.secondary_header.destination

    @property
    def time(self):
        return self.secondary_header.time

    @property
    def source_data(self):
        return self.payload

    def serialize(self):
        ccsds_header = super().serialize()

        # First static part of secondary header
        tmp = self.secondary_header.pus_version << 4 | self.secondary_header.spacecraft_time_ref_status
        values = [tmp, self.secondary_header.service_type, self.secondary_header.service_subtype]
        ccsds_sec_header_static = _COMMON_SEC_HDR_STRUCT.pack(*values)

        # "Optional" parts of secondary header
        if self.secondary_header.msg_type_counter is not None:
            ccsds_sec_header_msg_type_counter = self.secondary_header.msg_type_counter.to_bytes(self._MSG_TYPE_COUNTER_FIELD_SIZE, byteorder='big')
        else:
            ccsds_sec_header_msg_type_counter = bytes()
        if self.secondary_header.destination is not None:
            ccsds_sec_header_destination = self.secondary_header.destination.to_bytes(self._DESTINATION_FIELD_SIZE, byteorder='big')
        else:
            ccsds_sec_header_destination = bytes()

        # Packet error control
        packet_without_pec = ccsds_header + ccsds_sec_header_static + ccsds_sec_header_msg_type_counter + ccsds_sec_header_destination + bytes(self.secondary_header.time) + self.payload
        if self.has_pec:
            mem_view = memoryview(packet_without_pec)
            pec = crc_ccitt_calculate(mem_view)
            pec = pec.to_bytes(_PEC_FIELD_SIZE, byteorder='big')
        else:
            pec = bytes()

        return packet_without_pec + pec

    @classmethod
    def deserialize(cls, buffer, cuc_time=None, has_type_counter_field=True, has_destination_field=True, has_pec=True, validate_fields=True, validate_pec=True):
        packet_version_number, packet_type, secondary_header_flag, apid, seq_flags, seq_count_or_name, data_length = super(cls, cls).deserialize(buffer, has_pec, validate_pec)
        offset = cls._CCSDS_HDR_STRUCT.size

        if secondary_header_flag:
            data_field_except_source_length = _COMMON_SEC_HDR_STRUCT.size + (2 if has_type_counter_field else 0) + (2 if has_destination_field else 0) + len(cuc_time) + (2 if has_pec else 0)
            if len(buffer) < cls._CCSDS_HDR_STRUCT.size + data_field_except_source_length:
                raise IncompletePacketException()

            # First static part of secondary header
            tmp, service_type, service_subtype = _COMMON_SEC_HDR_STRUCT.unpack_from(buffer, offset)
            pus_version = (tmp >> 4) & 0b1111
            spacecraft_time_ref_status = tmp & 0b1111
            offset += _COMMON_SEC_HDR_STRUCT.size

            # "Optional" parts of secondary header
            if has_type_counter_field:
                msg_type_counter = int.from_bytes(buffer[offset:offset + cls._MSG_TYPE_COUNTER_FIELD_SIZE], byteorder='big')
                offset += cls._MSG_TYPE_COUNTER_FIELD_SIZE
            else:
                msg_type_counter = None
            if has_destination_field:
                destination = int.from_bytes(buffer[offset:offset + cls._DESTINATION_FIELD_SIZE], byteorder='big')
                offset += cls._DESTINATION_FIELD_SIZE
            else:
                destination = None

            if cuc_time:
                cuc_time.from_bytes(buffer[offset:])
            else:
                cuc_time = CucTime.deserialize(buffer[offset:])
            offset += len(cuc_time)
        else:
            data_field_except_source_length = 2 if has_pec else 0
            if len(buffer) < cls._CCSDS_HDR_STRUCT.size + data_field_except_source_length:
                raise IncompletePacketException()

            pus_version = None
            spacecraft_time_ref_status = None
            service_type = None
            service_subtype = None
            msg_type_counter = None
            destination = None
            cuc_time = None

        # User data field
        source_data_length = data_length + 1 - data_field_except_source_length
        source_data = bytes(buffer[offset:offset + source_data_length]) if source_data_length else None

        packet_length = cls._CCSDS_HDR_STRUCT.size + data_length + 1

        if validate_fields:
            packet = cls.create(has_pec=has_pec,
                packet_version_number=packet_version_number,
                packet_type=packet_type,
                secondary_header_flag=secondary_header_flag,
                apid=apid,
                seq_flags=seq_flags,
                seq_count=seq_count_or_name,
                data_length=data_length,
                pus_version=pus_version,
                spacecraft_time_ref_status=spacecraft_time_ref_status,
                service_type=service_type,
                service_subtype=service_subtype,
                msg_type_counter=msg_type_counter,
                destination=destination,
                time=cuc_time,
                data=source_data)
        else:
            packet = cls(has_pec)
            packet.header.packet_version_number = packet_version_number
            packet.header.packet_type = packet_type
            packet.header.secondary_header_flag = secondary_header_flag
            packet.header.apid = apid
            packet.header.seq_flags = seq_flags
            packet.header.seq_count_or_name = seq_count_or_name
            packet.header.data_length = data_length
            packet.payload = source_data
            packet.secondary_header.pus_version = pus_version
            packet.secondary_header.spacecraft_time_ref_status = spacecraft_time_ref_status
            packet.secondary_header.service_type = service_type
            packet.secondary_header.service_subtype = service_subtype
            packet.secondary_header.msg_type_counter = msg_type_counter
            packet.secondary_header.destination = destination
            packet.secondary_header.time = cuc_time

        return packet_length, packet

    @classmethod
    def create(cls, **kwargs):
        msg_type_counter = kwargs.get('msg_type_counter', None)
        destination = kwargs.get('destination', None)
        time = kwargs.get('time', None)

        if kwargs.get('secondary_header_flag', True):
            secondary_header_length = _COMMON_SEC_HDR_STRUCT.size + (2 if msg_type_counter is not None else 0) + (2 if destination is not None else 0) + len(time)
            kwargs['secondary_header_length'] = secondary_header_length
        kwargs['packet_type'] = PacketType.TM
        kwargs['seq_count_or_name'] = kwargs.get('seq_count', 0)
        packet = super(cls, cls).create(**kwargs)

        if packet.header.secondary_header_flag:
            pus_version = kwargs.get('pus_version', TM_PACKET_PUS_VERSION_NUMBER)
            if pus_version is not None:
                _validate_int_field('TM packet PUS version', pus_version, 0, 0b1111)
                packet.secondary_header.pus_version = pus_version

            spacecraft_time_ref_status = kwargs.get('spacecraft_time_ref_status', 0)
            _validate_int_field('Spacecraft time reference status', spacecraft_time_ref_status, 0, 0b1111)
            packet.secondary_header.spacecraft_time_ref_status = spacecraft_time_ref_status

            service_type = kwargs.get('service_type', None)
            if service_type is not None:
                _validate_int_field('Service type', service_type, 0, 255)
                packet.secondary_header.service_type = service_type

            service_subtype = kwargs.get('service_subtype', None)
            if service_subtype is not None:
                _validate_int_field('Service subtype', service_subtype, 0, 255)
                packet.secondary_header.service_subtype = service_subtype

            if msg_type_counter is not None:
                _validate_int_field('Message type counter', msg_type_counter, 0, 0xffff)
                packet.secondary_header.msg_type_counter = msg_type_counter

            if destination is not None:
                _validate_int_field('Destination ID', destination, 0, 0xffff)
                packet.secondary_header.destination = destination

            if time:
                packet.secondary_header.time = time

        return packet
