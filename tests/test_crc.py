import pytest

from puslib import crc_ccitt


# Test vectors taken from ECSS-E-70-41C, Annex B
@pytest.mark.parametrize("data, crc", [
    (bytes.fromhex("0000"), 0x1d0f),
    (bytes.fromhex("000000"), 0xcc9c),
    (bytes.fromhex("ABCDEF01"), 0x04a2),
    (bytes.fromhex("1456F89A0001"), 0x7fd5)
])
def test_calculate(data, crc):
    assert crc_ccitt.calculate(data) == crc
