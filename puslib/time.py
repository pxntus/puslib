import math
from enum import IntEnum
from datetime import datetime

import bitstring

from .exceptions import InvalidTimeFormat

TAI_EPOCH = datetime(year=1958, month=1, day=1)  # International Atomic Time (TAI) epoch


class TimeCodeIdentification(IntEnum):
    TAI = 0b001
    AGENCY_DEFINED = 0b010


class _TimeFormat:
    def __init__(self, basic_time_unit_length, frac_time_unit_length, epoch=None, preamble=None):
        if not (1 <= basic_time_unit_length <= 7):
            raise InvalidTimeFormat("Basic time unit must be 1 to 7 octets")
        self.basic_time_unit_length = basic_time_unit_length
        if not (0 <= frac_time_unit_length <= 10):
            raise InvalidTimeFormat("Fractional time unit must be 0 to 10 octets")
        self.frac_time_unit_length = frac_time_unit_length
        self.epoch = epoch if epoch else TAI_EPOCH
        self.time_code_id = TimeCodeIdentification.AGENCY_DEFINED if epoch else TimeCodeIdentification.TAI
        self.preamble = preamble if preamble else self._pack_preamble()

    def __bytes__(self):
        return self.preamble

    def __len__(self):
        return len(self.preamble)

    def _pack_preamble(self):
        p_field_extension = 1 if self.basic_time_unit_length > 4 or self.frac_time_unit_length > 3 else 0
        basic_time_unit_num_octets = min(3, self.basic_time_unit_length - 1)
        basic_frac_unit_num_octets = min(3, self.frac_time_unit_length)
        basic_time_unit_additional_octet = max(0, self.basic_time_unit_length - 4)
        basic_frac_unit_additional_octet = max(0, self.frac_time_unit_length - 3)

        octet1 = p_field_extension << 7 | self.time_code_id << 4 | basic_time_unit_num_octets << 2 | basic_frac_unit_num_octets
        if p_field_extension:
            octet2 = basic_time_unit_additional_octet << 5 | basic_frac_unit_additional_octet << 2
        preamble = bytes([octet1]) + (bytes([octet2]) if p_field_extension else b'')
        return preamble

    @classmethod
    def deserialize(cls, buffer):
        if len(buffer) < 2:
            raise ValueError("Buffer too small to contain CUC")
        octet1 = buffer[0]
        p_field_extension = octet1 >> 7
        if p_field_extension:
            octet2 = buffer[1]
        basic_time_unit_length = (((octet1 >> 2) & 0b11) + 1) + (((octet2 >> 5) & 0b11) if p_field_extension else 0)
        frac_time_unit_length = octet1 & 0b11 + (((octet2 >> 2) & 0b111) if p_field_extension else 0)
        epoch = (octet1 >> 4) & 0b111
        preamble = bytes([buffer[0]]) + (bytes([buffer[1]]) if p_field_extension else b'')
        return cls(basic_time_unit_length, frac_time_unit_length, epoch, preamble)


class CucTime:
    def __init__(self, basic_time_unit_length, frac_time_unit_length, seconds=0, fraction=0, has_preamble=True, epoch=None, preamble=None):
        self._format = _TimeFormat(basic_time_unit_length, frac_time_unit_length, epoch, preamble)
        self._has_preamble = has_preamble
        self._seconds = seconds
        self._fraction = fraction if self._format.frac_time_unit_length else None

    def __len__(self):
        return (len(self._format) if self._has_preamble else 0) + self._format.basic_time_unit_length + self._format.frac_time_unit_length

    def __str__(self):
        seconds = self._seconds + (self._fraction / (2 ** (self._format.frac_time_unit_length * 8)))
        return f"{seconds:.3f} seconds since epoch ({self._format.epoch})"

    def __bytes__(self):
        return (bytes(self._format) if self._has_preamble else b'') + (bitstring.pack(f'uintbe:{self._format.basic_time_unit_length * 8}', self._seconds).bytes) + (bitstring.pack(f'uintbe:{self._format.frac_time_unit_length * 8}', self._fraction).bytes if self._format.frac_time_unit_length else b'')

    @property
    def epoch(self):
        return self._format.epoch

    @property
    def seconds(self):
        return self._seconds

    @seconds.setter
    def seconds(self, val):
        max_val = (2 ** (self._format.basic_time_unit_length * 8)) - 1
        if isinstance(val, int) and 0 <= val <= max_val:
            self._seconds = val
        else:
            raise ValueError(f"Seconds must be an integer between 0 and {max_val}")

    @property
    def fraction(self):
        return self._fraction

    @fraction.setter
    def fraction(self, val):
        if self._format.frac_time_unit_length == 0:
            raise ValueError("CUC time configured without fraction part")
        max_val = (2 ** (self._format.frac_time_unit_length * 8)) - 1
        if isinstance(val, int) and 0 <= val <= max_val:
            self._fraction = val
        else:
            raise ValueError(f"Fraction must be an integer between 0 and {max_val}")

    @property
    def time_field(self):
        return (self._seconds, self._fraction)

    def from_datetime(self, dt):
        if dt < self.epoch:
            raise ValueError("Cannot set CUC to before epoch")
        seconds_since_epoch = (dt - self.epoch).total_seconds()
        if self._format.frac_time_unit_length:
            fraction, seconds = math.modf(seconds_since_epoch)
            self._seconds = int(seconds)
            self._fraction = round(fraction * ((2 ** (self._format.frac_time_unit_length * 8)) - 1))
        else:
            self._seconds = round(seconds_since_epoch)
        return seconds_since_epoch

    def from_bytes(self, buffer):
        preamble_size = len(self._format) if self._has_preamble else 0
        if len(buffer) < preamble_size + self._format.basic_time_unit_length + self._format.frac_time_unit_length:
            raise ValueError("Buffer too small to contain CUC")

        fraction_offset = preamble_size + self._format.basic_time_unit_length
        self._seconds = int.from_bytes(buffer[preamble_size:fraction_offset], byteorder='big')
        self._fraction = int.from_bytes(buffer[fraction_offset:fraction_offset + self._format.frac_time_unit_length], byteorder='big')

    @classmethod
    def deserialize(cls, buffer, has_preamble=True, epoch=None, basic_time_unit_length=None, frac_time_unit_length=None):
        if len(buffer) < 2:
            raise ValueError("Buffer too small to contain CUC")
        if not has_preamble and not (basic_time_unit_length and frac_time_unit_length):
            raise ValueError("If preamble not used CUC must be defined by the other arguments")
        if has_preamble:
            time_format = _TimeFormat.deserialize(buffer)
            basic_time_unit_length = time_format.basic_time_unit_length
            frac_time_unit_length = time_format.frac_time_unit_length
            preamble = bytes(time_format)
        else:
            preamble = None
        preamble_size = len(time_format) if has_preamble else 0
        if len(buffer) < preamble_size + basic_time_unit_length + frac_time_unit_length:
            raise ValueError("Buffer too small to contain CUC")

        fraction_offset = preamble_size + basic_time_unit_length
        seconds = int.from_bytes(buffer[preamble_size:fraction_offset], byteorder='big')
        fraction = int.from_bytes(buffer[fraction_offset:fraction_offset + frac_time_unit_length], byteorder='big')

        return cls(basic_time_unit_length, frac_time_unit_length, seconds=seconds, fraction=fraction, has_preamble=has_preamble, epoch=epoch, preamble=preamble)

    @classmethod
    def create(cls, basic_time_unit_length, frac_time_unit_length, seconds=0, fraction=0, has_preamble=True, epoch=None, preamble=None):
        cuc_time = cls(basic_time_unit_length, frac_time_unit_length, seconds, fraction, has_preamble, epoch, preamble)
        if seconds == 0 and fraction == 0:
            dt_now = datetime.utcnow()
            cuc_time.from_datetime(dt_now)
        return cuc_time
