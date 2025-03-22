from puslib.streams.stream import OutputStream


class ConsoleOutput(OutputStream):
    def write(self, packet):
        print(packet)
