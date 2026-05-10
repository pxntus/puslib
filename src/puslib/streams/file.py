from collections.abc import Iterator
from pathlib import Path

from puslib import get_policy
from puslib.packet import PusTmPacket
from puslib.streams.stream import InputStream


class FileInput(InputStream):
    """Input stream that reads TM packets from a binary archive file."""

    def __init__(self, archive_file: str | Path, has_type_counter_field: bool = True, has_destination_field: bool = True, other_headers_size: int = 0, validate_pec: bool = True):
        """Create a file input stream.

        Arguments:
            archive_file -- path to the binary telemetry archive

        Keyword Arguments:
            has_type_counter_field -- whether packets include a message type counter field (default: {True})
            has_destination_field -- whether packets include a destination ID field (default: {True})
            other_headers_size -- number of bytes of non-PUS header preceding each packet (default: {0})
            validate_pec -- whether to validate the packet error control (CRC) field (default: {True})
        """
        self._input = Path(archive_file)
        self._has_type_counter_field = has_type_counter_field
        self._has_destination_field = has_destination_field
        self._other_headers_size = other_headers_size
        self._validate_pec = validate_pec

    def __iter__(self) -> Iterator[tuple[memoryview, PusTmPacket]]:
        """Iterate over all packets in the archive, yielding (other_headers, packet) tuples."""
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

    def read(self, offset: int = 0) -> PusTmPacket:
        """Read a single packet at a given byte offset within the archive.

        Keyword Arguments:
            offset -- byte offset from the start of the data region (after other_headers_size) (default: {0})

        Returns:
            deserialized TM packet
        """
        with open(self._input, 'rb') as f:
            content = f.read()
        data = memoryview(content)
        packet = get_policy().PusTmPacket().deserialize(data[self._other_headers_size + offset:], cuc_time=get_policy().CucTime(), has_type_counter_field=self._has_type_counter_field, has_destination_field=self._has_destination_field, validate_fields=False, validate_pec=self._validate_pec)
        return packet
