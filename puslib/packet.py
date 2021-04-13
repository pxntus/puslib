import struct
from enum import IntEnum, IntFlag
from dataclasses import dataclass

from .exceptions import CrcException, IncompletePacketException, InvalidPacketException, TooSmallBufferException
from .time import CucTime
from .crc_ccitt import calculate as crc_ccitt_calculate

CCSDS_PACKET_VERSION_NUMBER = 0
CCSDS_MAX_PACKET_SIZE = 65542

TM_PACKET_PUS_VERSION_NUMBER = 2
TC_PACKET_PUS_VERSION_NUMBER = 2

_CCSDS_HDR_STRUCT = struct.Struct('>HHH')
_COMMON_SEC_HDR_STRUCT = struct.Struct('>BBB')

_SOURCE_FIELD_SIZE = 2

_MSG_TYPE_COUNTER_FIELD_SIZE = 2
_DESTINATION_FIELD_SIZE = 2

_PEC_FIELD_SIZE = 2


def _validate_int_field(field_name, val, min_val, max_val):
    if isinstance(val, int):
        if not (min_val <= val <= max_val):
            raise InvalidPacketException(f"{field_name} must be between {min_val} and {max_val}")
    else:
        raise TypeError(f"{field_name} must be an integer")


def _validate_bool_field(field_name, val):
    if not isinstance(val, bool):
        raise TypeError(f"{field_name} must be a bool")


class PacketType(IntEnum):
    TM = 0
    TC = 1


@dataclass
class _PacketPrimaryHeader:
    packet_version_number: int = CCSDS_PACKET_VERSION_NUMBER

    # Packet ID
    packet_type: PacketType = PacketType.TM
    secondary_header_flag: bool = True
    apid: int = 0

    # Packet sequence control
    seq_flags: int = 0b11
    seq_count_or_name: int = 0

    data_length: int = 0


class CcsdsSpacePacket:
    def __init__(self, has_pec=True):
        self.header = _PacketPrimaryHeader()
        self.secondary_header = None
        self.payload = None
        self._has_pec = has_pec

    def __len__(self):
        return _CCSDS_HDR_STRUCT.size + (len(self.payload) if self.payload else 0) + (2 if self._has_pec else 0)

    def __bytes__(self):
        buffer = bytearray(len(self))
        self.serialize(buffer)
        return bytes(buffer)

    def __str__(self):
        s = f"{self.header.packet_type.name} Packet\n"
        s += f"  APID: {self.header.apid}\n"
        s += f"  Sequence count: {self.header.seq_count_or_name}\n"
        return s

    @property
    def packet_type(self):
        return self.header.packet_type

    @property
    def apid(self):
        return self.header.apid

    @property
    def has_pec(self):
        return self._has_pec

    def serialize(self, buffer):
        if len(buffer) < self.header.data_length + 1:
            raise TooSmallBufferException()

        packet_id = self.header.packet_version_number << 13 | (1 if self.header.packet_type == PacketType.TC else 0) << 12 | (1 if self.header.secondary_header_flag else 0) << 11 | self.header.apid
        seq_ctrl = self.header.seq_flags << 14 | self.header.seq_count_or_name
        _CCSDS_HDR_STRUCT.pack_into(buffer, 0, packet_id, seq_ctrl, self.header.data_length)
        return _CCSDS_HDR_STRUCT.size

    def request_id(self):
        packet_id = self.header.packet_version_number << 13 | (1 if self.header.packet_type == PacketType.TC else 0) << 12 | (1 if self.header.secondary_header_flag else 0) << 11 | self.header.apid
        seq_ctrl = self.header.seq_flags << 14 | self.header.seq_count_or_name
        return struct.pack('>HH', packet_id, seq_ctrl)

    @classmethod
    def deserialize(cls, buffer, has_pec=True, validate_pec=True):
        packet_id, seq_ctrl, data_length = _CCSDS_HDR_STRUCT.unpack_from(buffer)

        packet_size = _CCSDS_HDR_STRUCT.size + data_length + 1
        if packet_size > len(buffer):
            raise IncompletePacketException()
        if packet_size > CCSDS_MAX_PACKET_SIZE:
            raise InvalidPacketException("Packet too large")
        if has_pec and validate_pec:
            mv = memoryview(buffer)
            if crc_ccitt_calculate(mv[:packet_size]) != 0:
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

        packet_type = kwargs.get('packet_type', None)
        if not isinstance(packet_type, PacketType):
            raise TypeError("Packet type must be a PacketType")
        packet.header.packet_type = packet_type

        secondary_header_flag = kwargs.get('secondary_header_flag', True)
        _validate_bool_field('Secondary header flag', secondary_header_flag)
        packet.header.secondary_header_flag = secondary_header_flag

        apid = kwargs.get('apid', None)
        _validate_int_field('apid', apid, 0, 0x7ff)
        packet.header.apid = apid

        seq_flags = kwargs.get('seq_flags', 0b11)
        _validate_int_field('Sequence flags', seq_flags, 0, 0b11)
        packet.header.seq_flags = seq_flags

        seq_count = kwargs.get('seq_count_or_name', None)
        _validate_int_field('Sequence count or name', seq_count, 0, 0x3fff)
        packet.header.seq_count_or_name = seq_count

        data = kwargs.get('data', None)
        if isinstance(data, (bytearray, bytes, type(None))):
            packet.payload = data
        else:
            raise TypeError("Application data must be None or a bytearray")

        data_length = kwargs.get('data_length', None)
        data_size_except_source_data = kwargs.get('secondary_header_length', 0) + (2 if packet.has_pec else 0)
        max_data_size = CCSDS_MAX_PACKET_SIZE - _CCSDS_HDR_STRUCT.size - data_size_except_source_data
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
    source: (int, None) = None


class PusTcPacket(CcsdsSpacePacket):
    def __init__(self, has_pec=True):
        super().__init__(has_pec)
        self.secondary_header = _PacketSecondaryHeaderTc()

    def __len__(self):
        size = super().__len__()
        if self.header.secondary_header_flag:
            size += _COMMON_SEC_HDR_STRUCT.size
            if self.secondary_header.source:
                size += _SOURCE_FIELD_SIZE
        return size

    def __str__(self):
        s = super().__str__()
        if self.header.secondary_header_flag:
            s += f"  Service type: {self.secondary_header.service_type}\n"
            s += f"  Service subtype: {self.secondary_header.service_subtype}\n"
            if self.payload:
                s += f"  Application data: 0x{self.payload.hex()}"
        return s

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

    def serialize(self, buffer):
        offset = super().serialize(buffer)

        # First static part of secondary header
        tmp = self.secondary_header.pus_version << 4 | self.secondary_header.ack_flags
        values = [tmp, self.secondary_header.service_type, self.secondary_header.service_subtype]
        _COMMON_SEC_HDR_STRUCT.pack_into(buffer, offset, *values)
        offset += _COMMON_SEC_HDR_STRUCT.size

        # Last "optional" part of secondary header
        if self.secondary_header.source:
            buffer[offset:offset + _SOURCE_FIELD_SIZE] = self.secondary_header.source.to_bytes(_SOURCE_FIELD_SIZE, byteorder='big')
            offset += _SOURCE_FIELD_SIZE

        # User data field
        if self.payload:
            app_data_length = self.header.data_length + 1 - _COMMON_SEC_HDR_STRUCT.size - (2 if self.secondary_header.source else 0) - (2 if self.has_pec else 0)
            buffer[offset:offset + app_data_length] = self.payload
            offset += app_data_length

        # Packet error control
        if self.has_pec:
            mv = memoryview(buffer)
            pec = crc_ccitt_calculate(mv[0:offset])
            buffer[offset:offset + _PEC_FIELD_SIZE] = pec.to_bytes(_PEC_FIELD_SIZE, byteorder='big')
            offset += _PEC_FIELD_SIZE

        return offset

    @classmethod
    def deserialize(cls, buffer, has_source_field=True, has_pec=True, validate_fields=True, validate_pec=True):
        packet_version_number, packet_type, secondary_header_flag, apid, seq_flags, seq_count_or_name, data_length = super(cls, cls).deserialize(buffer, has_pec, validate_pec)
        offset = _CCSDS_HDR_STRUCT.size

        data_field_except_source_length = ((_COMMON_SEC_HDR_STRUCT.size + (2 if has_source_field else 0)) if secondary_header_flag else 0) + (2 if has_pec else 0)
        if len(buffer) < _CCSDS_HDR_STRUCT.size + data_field_except_source_length:
            raise IncompletePacketException()

        if secondary_header_flag:
            # First static part of secondary header
            tmp, service_type, service_subtype = _COMMON_SEC_HDR_STRUCT.unpack_from(buffer, offset)
            pus_version = (tmp >> 4) & 0b1111
            ack_flags = AckFlag(tmp & 0b1111)
            offset += _COMMON_SEC_HDR_STRUCT.size

            # Last "optional" part of secondary header
            if has_source_field:
                source = int.from_bytes(buffer[offset:offset + _SOURCE_FIELD_SIZE], byteorder='big')
                offset += _SOURCE_FIELD_SIZE
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

        packet_length = _CCSDS_HDR_STRUCT.size + data_length + 1

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
            secondary_header_length = _COMMON_SEC_HDR_STRUCT.size + (2 if source else 0)
            kwargs['secondary_header_length'] = secondary_header_length
        kwargs['packet_type'] = PacketType.TC
        kwargs['seq_count_or_name'] = kwargs.get('name', None)
        packet = super(cls, cls).create(**kwargs)

        if packet.header.secondary_header_flag:
            pus_version = kwargs.get('pus_version', TC_PACKET_PUS_VERSION_NUMBER)
            if pus_version:
                _validate_int_field('TC packet PUS version', pus_version, 0, 0b1111)
                packet.secondary_header.pus_version = pus_version

            ack_flags = kwargs.get('ack_flags', AckFlag.NONE)
            if ack_flags:
                _validate_int_field('Acknowledgement flags', ack_flags, 0, 0b1111)
                packet.secondary_header.ack_flags = ack_flags

            service_type = kwargs.get('service_type', None)
            if service_type:
                _validate_int_field('Service type', service_type, 0, 255)
                packet.secondary_header.service_type = service_type

            service_subtype = kwargs.get('service_subtype', None)
            if service_subtype:
                _validate_int_field('Service subtype', service_subtype, 0, 255)
                packet.secondary_header.service_subtype = service_subtype

            if source:
                _validate_int_field('Source ID', source, 0, 0xffff)
                packet.secondary_header.source = source

        return packet


@dataclass
class _PacketSecondaryHeaderTm:
    pus_version: (int, None) = TM_PACKET_PUS_VERSION_NUMBER
    spacecraft_time_ref_status: (int, None) = None
    service_type: (int, None) = None
    service_subtype: (int, None) = None
    msg_type_counter: (int, None) = None
    destination: (int, None) = None
    time: (CucTime, None) = None


class PusTmPacket(CcsdsSpacePacket):
    def __init__(self, has_pec=True):
        super().__init__(has_pec)
        self.secondary_header = _PacketSecondaryHeaderTm()

    def __len__(self):
        size = super().__len__()
        if self.header.secondary_header_flag:
            size += _COMMON_SEC_HDR_STRUCT.size
            if self.secondary_header.msg_type_counter:
                size += _MSG_TYPE_COUNTER_FIELD_SIZE
            if self.secondary_header.destination:
                size += _DESTINATION_FIELD_SIZE
            size += len(self.secondary_header.time)
        return size

    def __str__(self):
        s = super().__str__()
        if self.header.secondary_header_flag:
            s += f"  Service type: {self.secondary_header.service_type}\n"
            s += f"  Service subtype: {self.secondary_header.service_subtype}\n"
            s += f"  CUC timestamp: {self.secondary_header.time}\n"
            if self.payload:
                s += f"  Source data: 0x{self.payload.hex()}"
        return s

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

    def serialize(self, buffer):
        offset = super().serialize(buffer)

        # First static part of secondary header
        tmp = self.secondary_header.pus_version << 4 | self.secondary_header.spacecraft_time_ref_status
        values = [tmp, self.secondary_header.service_type, self.secondary_header.service_subtype]
        _COMMON_SEC_HDR_STRUCT.pack_into(buffer, offset, *values)
        offset += _COMMON_SEC_HDR_STRUCT.size

        # "Optional" parts of secondary header
        if self.secondary_header.msg_type_counter:
            buffer[offset:offset + _MSG_TYPE_COUNTER_FIELD_SIZE] = self.secondary_header.msg_type_counter.to_bytes(_MSG_TYPE_COUNTER_FIELD_SIZE, byteorder='big')
            offset += _MSG_TYPE_COUNTER_FIELD_SIZE
        if self.secondary_header.destination:
            buffer[offset:offset + _DESTINATION_FIELD_SIZE] = self.secondary_header.destination.to_bytes(_DESTINATION_FIELD_SIZE, byteorder='big')
            offset += _DESTINATION_FIELD_SIZE

        # Time field
        buffer[offset:offset + len(self.secondary_header.time)] = bytes(self.secondary_header.time)
        offset += len(self.secondary_header.time)

        # User data field
        if self.payload:
            source_data_length = self.header.data_length + 1 - _COMMON_SEC_HDR_STRUCT.size - (2 if self.secondary_header.msg_type_counter else 0) - (2 if self.secondary_header.destination else 0) - len(self.secondary_header.time) - (2 if self.has_pec else 0)
            buffer[offset:offset + source_data_length] = self.payload
            offset += source_data_length

        # Packet error control
        if self.has_pec:
            mv = memoryview(buffer)
            pec = crc_ccitt_calculate(mv[0:offset])
            buffer[offset:offset + _PEC_FIELD_SIZE] = pec.to_bytes(_PEC_FIELD_SIZE, byteorder='big')
            offset += _PEC_FIELD_SIZE

        return offset

    @classmethod
    def deserialize(cls, buffer, cuc_time=None, has_type_counter_field=True, has_destination_field=True, has_pec=True, validate_fields=True, validate_pec=True):
        packet_version_number, packet_type, secondary_header_flag, apid, seq_flags, seq_count_or_name, data_length = super(cls, cls).deserialize(buffer, has_pec, validate_pec)
        offset = _CCSDS_HDR_STRUCT.size

        if secondary_header_flag:
            data_field_except_source_length = _COMMON_SEC_HDR_STRUCT.size + (2 if has_type_counter_field else 0) + (2 if has_destination_field else 0) + len(cuc_time) + (2 if has_pec else 0)
            if len(buffer) < _CCSDS_HDR_STRUCT.size + data_field_except_source_length:
                raise IncompletePacketException()

            # First static part of secondary header
            tmp, service_type, service_subtype = _COMMON_SEC_HDR_STRUCT.unpack_from(buffer, offset)
            pus_version = (tmp >> 4) & 0b1111
            spacecraft_time_ref_status = tmp & 0b1111
            offset += _COMMON_SEC_HDR_STRUCT.size

            # "Optional" parts of secondary header
            if has_type_counter_field:
                msg_type_counter = int.from_bytes(buffer[offset:offset + _MSG_TYPE_COUNTER_FIELD_SIZE], byteorder='big')
                offset += _MSG_TYPE_COUNTER_FIELD_SIZE
            else:
                msg_type_counter = None
            if has_destination_field:
                destination = int.from_bytes(buffer[offset:offset + _DESTINATION_FIELD_SIZE], byteorder='big')
                offset += _DESTINATION_FIELD_SIZE
            else:
                destination = None

            if cuc_time:
                cuc_time.from_bytes(buffer[offset:])
            else:
                cuc_time = CucTime.deserialize(buffer[offset:])
            offset += len(cuc_time)
        else:
            data_field_except_source_length = 2 if has_pec else 0
            if len(buffer) < _CCSDS_HDR_STRUCT.size + data_field_except_source_length:
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

        packet_length = _CCSDS_HDR_STRUCT.size + data_length + 1

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
            secondary_header_length = _COMMON_SEC_HDR_STRUCT.size + (2 if msg_type_counter else 0) + (2 if destination else 0) + len(time)
            kwargs['secondary_header_length'] = secondary_header_length
        kwargs['packet_type'] = PacketType.TM
        kwargs['seq_count_or_name'] = kwargs.get('seq_count', None)
        packet = super(cls, cls).create(**kwargs)

        pus_version = kwargs.get('pus_version', TM_PACKET_PUS_VERSION_NUMBER)
        if pus_version:
            _validate_int_field('TM packet PUS version', pus_version, 0, 0b1111)
            packet.secondary_header.pus_version = pus_version

        spacecraft_time_ref_status = kwargs.get('spacecraft_time_ref_status', 0)
        _validate_int_field('Spacecraft time reference status', spacecraft_time_ref_status, 0, 0b1111)
        packet.secondary_header.spacecraft_time_ref_status = spacecraft_time_ref_status

        service_type = kwargs.get('service_type', None)
        if service_type:
            _validate_int_field('Service type', service_type, 0, 255)
            packet.secondary_header.service_type = service_type

        service_subtype = kwargs.get('service_subtype', None)
        if service_subtype:
            _validate_int_field('Service subtype', service_subtype, 0, 255)
            packet.secondary_header.service_subtype = service_subtype

        if msg_type_counter:
            _validate_int_field('Message type counter', msg_type_counter, 0, 0xffff)
            packet.secondary_header.msg_type_counter = msg_type_counter

        if destination:
            _validate_int_field('Destination ID', destination, 0, 0xffff)
            packet.secondary_header.destination = destination

        if time:
            packet.secondary_header.time = time

        return packet
