from pathlib import Path

from .. import get_policy
from .stream import InputStream


class FileInput(InputStream):
    def __init__(self, archive_file, has_type_counter_field=True, has_destination_field=True, other_headers_size=0, validate_pec=True):
        self._input = Path(archive_file)
        self._has_type_counter_field = has_type_counter_field
        self._has_destination_field = has_destination_field
        self._other_headers_size = other_headers_size
        self._validate_pec = validate_pec

    def __iter__(self):
        with open(self._input, 'rb') as f:
            content = f.read()
        data = memoryview(content)
        offset = 0
        while offset < len(data):
            other_headers = data[offset:offset + self._other_headers_size]
            offset += self._other_headers_size
            packet = get_policy().PusTmPacket().deserialize(data[offset:], cuc_time=get_policy().CucTime(), has_type_counter_field=self._has_type_counter_field, has_destination_field=self._has_destination_field, validate_fields=False, validate_pec=self._validate_pec)
            offset += len(packet)
            yield other_headers, packet

    def read(self, offset=0):
        with open(self._input, 'rb') as f:
            content = f.read()
        data = memoryview(content)
        _, packet = get_policy().PusTmPacket.deserialize(data[self._other_headers_size + offset:], validate_fields=False, validate_pec=False)
        return packet
