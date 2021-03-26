from enum import IntEnum

from .time import CucTime
from .packet import PusTcPacket


class PacketFieldType(IntEnum):
    Boolean = 1
    Enumerated = 2
    UInt = 3
    Int = 4
    Real = 5
    BitString = 6
    OctetString = 7
    String = 8
    AbsoluteTime = 9
    RelativeTime = 10
    Deducted = 11
    Packet = 12


class Parameter:
    def __init__(self, name, value_type, init_value=None):
        if init_value:
            self._validate(init_value)
        self._value = init_value
        self._value_type = value_type

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._validate(new_value)
        self._value = new_value

    @property
    def type(self):
        return self._value_type

    @property
    def format(self):
        raise NotImplementedError

    def _validate(self, value):
        raise NotImplementedError


class BoolParameter(Parameter):
    def __init__(self, name, init_value=None):
        super().__init__(name, PacketFieldType.Boolean, init_value)

    def _validate(self, value):
        if not isinstance(value, bool):
            raise TypeError("Boolean expected")

    @property
    def format(self):
        return '?'


class _IntegerParameter(Parameter):
    def _validate(self, value):
        if not isinstance(value, int):
            raise TypeError("Integer expected")


class UInt8Parameter(_IntegerParameter):
    def __init__(self, name, init_value=None):
        super().__init__(name, PacketFieldType.UInt, init_value)

    def _validate(self, value):
        super()._validate(value)
        if not (0 <= value <= 255):
            raise ValueError

    @property
    def format(self):
        return 'B'


class UInt16Parameter(_IntegerParameter):
    def __init__(self, name, init_value=None):
        super().__init__(name, PacketFieldType.UInt, init_value)

    def _validate(self, value):
        if not (0 <= value <= 65535):
            raise ValueError

    @property
    def format(self):
        return 'H'


class UInt32Parameter(_IntegerParameter):
    def __init__(self, name, init_value=None):
        super().__init__(name, PacketFieldType.UInt, init_value)

    def _validate(self, value):
        if not (0 <= value <= 4294967295):
            raise ValueError

    @property
    def format(self):
        return 'I'


class UInt64Parameter(_IntegerParameter):
    def __init__(self, name, init_value=None):
        super().__init__(name, PacketFieldType.UInt, init_value)

    def _validate(self, value):
        if not (0 <= value <= 18446744073709551615):
            raise ValueError

    @property
    def format(self):
        return 'Q'


class Int8Parameter(_IntegerParameter):
    def __init__(self, name, init_value=None):
        super().__init__(name, PacketFieldType.Int, init_value)

    def _validate(self, value):
        super()._validate(value)
        if not (-128 <= value <= 127):
            raise ValueError

    @property
    def format(self):
        return 'b'


class Int16Parameter(_IntegerParameter):
    def __init__(self, name, init_value=None):
        super().__init__(name, PacketFieldType.Int, init_value)

    def _validate(self, value):
        if not (-32768 <= value <= 32767):
            raise ValueError

    @property
    def format(self):
        return 'h'


class Int32Parameter(_IntegerParameter):
    def __init__(self, name, init_value=None):
        super().__init__(name, PacketFieldType.Int, init_value)

    def _validate(self, value):
        if not (-2147483648 <= value <= 2147483647):
            raise ValueError

    @property
    def format(self):
        return 'i'


class Int64Parameter(_IntegerParameter):
    def __init__(self, name, init_value=None):
        super().__init__(name, PacketFieldType.Int, init_value)

    def _validate(self, value):
        if not (-9223372036854775808 <= value <= 9223372036854775807):
            raise ValueError

    @property
    def format(self):
        return 'q'


class _RealParameter(Parameter):
    def _validate(self, value):
        if not isinstance(value, float):
            raise TypeError("Float expected")


class Real32Parameter(_RealParameter):
    @property
    def format(self):
        return 'f'


class Real64Parameter(_RealParameter):
    @property
    def format(self):
        return 'd'


class OctetStringParameter(Parameter):
    def __init__(self, name, init_value=None):
        super().__init__(name, PacketFieldType.OctetString, init_value)

    def _validate(self, value):
        if not isinstance(value, (bytes, bytearray)):
            raise TypeError("Bytes or bytearray expected")

    @property
    def format(self):
        return len(self.value) + 's'


class AbsoluteTimeParameter(Parameter):
    def __init__(self, name, init_value=None):
        super().__init__(name, PacketFieldType.AbsoluteTime, init_value)

    def _validate(self, value):
        if not isinstance(value, CucTime):
            raise TypeError("CucTime expected")

    @property
    def format(self):
        return len(self.value) + 's'


class RelativeTimeParameter(AbsoluteTimeParameter):
    def __init__(self, name, init_value=None):
        super(Parameter, self).__init__(name, PacketFieldType.RelativeTime, init_value)


class PacketParameter(Parameter):
    def __init__(self, name, init_value=None):
        super().__init__(name, PacketFieldType.Packet, init_value)

    def _validate(self, value):
        if not isinstance(value, PusTcPacket):
            raise TypeError("PusTcPacket expected")

    @property
    def format(self):
        return len(self.value) + 's'
