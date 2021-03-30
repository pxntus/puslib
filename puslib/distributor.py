class TmDistributor:
    def __init__(self, stream=None):
        self._streams = []
        if stream:
            self.add_stream(stream)

    def add_stream(self, stream):
        self._streams.append(stream)

    def send(self, packet):
        for stream in self._streams:
            stream.write(packet)
