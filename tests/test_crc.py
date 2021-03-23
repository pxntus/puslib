from collections import namedtuple

from puslib import crc_ccitt


def test_calculateb():
    # Test vectors taken from ECSS-E-70-41C, Annex B
    TestVector = namedtuple('TestVector', ['data', 'crc'])
    test_vectors = [
        TestVector(bytes.fromhex("0000"), 0x1d0f),
        TestVector(bytes.fromhex("000000"), 0xcc9c),
        TestVector(bytes.fromhex("ABCDEF01"), 0x04a2),
        TestVector(bytes.fromhex("1456F89A0001"), 0x7fd5)
    ]

    for test_vector in test_vectors:
        assert crc_ccitt.calculateb(test_vector.data) == test_vector.crc
