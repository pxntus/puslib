_POLYNOMIAL = 0x1021
_PRESET = 0xffff


def _initial(c):
    crc = 0
    c = c << 8
    for _ in range(8):
        tmp = crc << 1
        if (crc ^ c) & 0x8000:
            tmp ^= _POLYNOMIAL
        crc = tmp
        c = c << 1
    return crc


_tab = [_initial(i) for i in range(256)]


def _update_crc(crc, byte):
    byte = byte & 0xff
    tmp = (crc >> 8) ^ byte
    crc = (crc << 8) ^ _tab[tmp & 0xff]
    return crc & 0xffff


def calculate(buffer):
    crc = _PRESET
    for byte in buffer:
        crc = _update_crc(crc, byte)
    return crc
