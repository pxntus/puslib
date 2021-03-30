def _seq_count_generator():
    seq_count = -1
    max_count = 2 ** 14
    while True:
        seq_count = (seq_count + 1) % max_count
        yield seq_count


class PusIdent:
    def __init__(self, apid):
        self._apid = apid
        self._seq_count_generator = _seq_count_generator()

    @property
    def apid(self):
        return self._apid

    def seq_count(self):
        return next(self._seq_count_generator)
