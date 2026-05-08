"""CRC-16-CCITT checksum (polynomial 0x1021, preset 0xFFFF)."""

import binascii

_POLYNOMIAL = 0x1021
_PRESET = 0xffff


def calculate(buffer: bytes | bytearray | memoryview) -> int:
    """Calculate the CRC-16-CCITT checksum on a buffer.

    Arguments:
        buffer -- input buffer to calculate checksum for

    Returns:
        16 bit CRC checksum
    """
    return binascii.crc_hqx(buffer, _PRESET)
