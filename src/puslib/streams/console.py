from puslib.streams.stream import OutputStream


class ConsoleOutput(OutputStream):
    """Output stream that prints packets to stdout. Intended for debugging."""

    def write(self, packet):
        print(packet)
