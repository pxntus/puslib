class PusIdent:
    def __init__(self, apid):
        self._apid = apid

    @property
    def apid(self):
        return self._apid

    def next_seq_count(self):
        seq_count = -1
        max_count = 2 ** 14
        while True:
            seq_count = (seq_count + 1) % max_count
            yield seq_count
