from pathlib import Path

from .. import get_pus_policy
from .stream import InputStream


class FileInput(InputStream):
    def __init__(self, archive_file, other_headers_size=0, validate_pec=True):
        self._input = Path(archive_file)
        self._other_headers_size = other_headers_size
        self._validate_pec = validate_pec

    def __iter__(self):
        with open(self._input, 'rb') as f:
            content = f.read()
        data = memoryview(content)
        offset = 0
        while offset < len(data):
            offset += self._other_headers_size
            packet_length, packet = get_pus_policy().PusTcPacket.deserialize(data[offset:], validate_fields=False, validate_pec=self._validate_pec)
            offset += packet_length
            yield packet

    def read(self, offset=0):
        with open(self._input, 'rb') as f:
            content = f.read()
        data = memoryview(content)
        _, packet = get_pus_policy().PusTcPacket.deserialize(data[self._other_headers_size + offset:], validate_fields=False, validate_pec=False)
        return packet
