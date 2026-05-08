"""CRC-16-CCITT checksum (polynomial 0x1021, preset 0xFFFF)."""

import binascii

_PRESET = 0xffff


def calculate(buffer: bytes | bytearray | memoryview) -> int:
    """Calculate the CRC-16-CCITT checksum on a buffer.

    Using polynomial 0x1021 (default for crc_hqx) and preset (or initial value)
    0xffff according to ECSS and CCSDS standards.

    Arguments:
        buffer -- input buffer to calculate checksum for

    Returns:
        16 bit CRC checksum
    """
    return binascii.crc_hqx(buffer, _PRESET)
