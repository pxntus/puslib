import math
from datetime import datetime, timedelta

import pytest

from puslib.time import CucTime, TAI_EPOCH
from puslib.exceptions import InvalidTimeFormat


@pytest.mark.parametrize("basic_unit_length, frac_unit_length, seconds, fraction", [
    (1, 0, 0, None),
    (1, 1, 0, 0),
    (2, 2, 0, 0),
    (4, 3, 0, 0),
    (5, 3, 0, 0),
    (7, 8, 0, 0),
    (7, 10, 0, 0),
    (1, 10, 0, 0),
])
def test_init(basic_unit_length, frac_unit_length, seconds, fraction):
    ct = CucTime(basic_unit_length=basic_unit_length, frac_unit_length=frac_unit_length)
    assert ct.seconds == seconds
    assert ct.fraction == fraction
    assert ct.time_field == (seconds, fraction)


@pytest.mark.parametrize("num_second_octets, num_fraction_octets", [
    (0, 0),
    (8, 0),
    (1, 11),
])
def test_limits(num_second_octets, num_fraction_octets):
    with pytest.raises(InvalidTimeFormat):
        CucTime(basic_unit_length=num_second_octets, frac_unit_length=num_fraction_octets)


def test_get_time():
    ct = CucTime(1, 2, 1, 1)
    assert ct.seconds == 1
    assert ct.fraction == 2
    assert ct.time_field == (1, 2)


def test_set_time():
    ct = CucTime(basic_unit_length=1, frac_unit_length=0)
    secs1 = -1
    with pytest.raises(ValueError):
        ct.seconds = secs1
    secs2 = 2 ** 8 - 1
    ct.seconds = secs2
    assert ct.seconds == secs2
    secs3 = 2 ** 8
    with pytest.raises(ValueError):
        ct.seconds = secs3
    assert ct.seconds == secs2

    frac1 = 1
    with pytest.raises(ValueError):
        ct.fraction = frac1

    ct = CucTime(basic_unit_length=1, frac_unit_length=1)
    frac1 = -1
    with pytest.raises(ValueError):
        ct.fraction = frac1
    frac2 = 2 ** 8 - 1
    ct.fraction = frac2
    assert ct.fraction == frac2
    frac3 = 2 ** 8
    with pytest.raises(ValueError):
        ct.fraction = frac3
    assert ct.fraction == frac2


@pytest.mark.parametrize("basic_unit_length, frac_unit_length, seconds_since_epoch", [
    (4, 1, 1.0),
    (4, 1, 1.5),
    (4, 2, 100.75),
])
def test_from_datetime(basic_unit_length, frac_unit_length, seconds_since_epoch):
    ct = CucTime(basic_unit_length=basic_unit_length, frac_unit_length=frac_unit_length)
    dt = ct.epoch + timedelta(seconds=seconds_since_epoch)
    ct.from_datetime(dt)
    fraction, seconds = math.modf(seconds_since_epoch)
    assert ct.seconds == seconds
    assert ct.fraction == round(fraction * ((2 ** (frac_unit_length * 8)) - 1))


COMMON_CUCTIME_TEST_VECTORS = [
    (bytes([0b00100001, 0x02, 0x03]), True, datetime(2000, 1, 1), 1, 1, 2, 3),
    (bytes([0b10011101, 0b00100000, 0x00, 0x00, 0x00, 0x00, 0x02, 0x03]), True, None, 5, 1, 2, 3),
    (bytes([0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x03]), False, datetime(2000, 1, 1), 4, 3, 2, 3),
    (bytes([0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x03]), False, None, 5, 3, 2, 3),
    (bytes([0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x03]), False, datetime(2000, 1, 1), 4, 4, 2, 3),
    (bytes([0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x03]), False, None, 5, 5, 2, 3),
]


@pytest.mark.parametrize("packed_cuc, has_preamble, epoch, num_second_octets, num_fraction_octets, seconds, fraction", COMMON_CUCTIME_TEST_VECTORS)
def test_from_bytes(packed_cuc, has_preamble, epoch, num_second_octets, num_fraction_octets, seconds, fraction):  # pylint: disable=unused-argument
    ct = CucTime(basic_unit_length=num_second_octets, frac_unit_length=num_fraction_octets, has_preamble=has_preamble)
    ct.from_bytes(packed_cuc)
    assert ct.epoch == TAI_EPOCH
    assert ct.seconds == seconds
    assert ct.fraction == fraction


@pytest.mark.parametrize("packed_cuc, has_preamble, epoch, num_second_octets, num_fraction_octets, seconds, fraction", COMMON_CUCTIME_TEST_VECTORS)
def test_serialize(packed_cuc, has_preamble, epoch, num_second_octets, num_fraction_octets, seconds, fraction):
    ct = CucTime(seconds, fraction, num_second_octets, num_fraction_octets, has_preamble, epoch)
    assert len(ct) == len(packed_cuc)
    assert bytes(ct) == packed_cuc


@pytest.mark.parametrize("packed_cuc, has_preamble, epoch, num_second_octets, num_fraction_octets, seconds, fraction", COMMON_CUCTIME_TEST_VECTORS)
def test_deserialize(packed_cuc, has_preamble, epoch, num_second_octets, num_fraction_octets, seconds, fraction):
    ct = CucTime.deserialize(packed_cuc, has_preamble, epoch, num_second_octets, num_fraction_octets)
    assert len(ct) == len(packed_cuc)
    assert ct.epoch == epoch if epoch else TAI_EPOCH
    assert ct.seconds == seconds
    assert ct.fraction == fraction
    assert ct._format.basic_unit_length == num_second_octets  # pylint: disable=protected-access
    assert ct._format.frac_unit_length == num_fraction_octets  # pylint: disable=protected-access
