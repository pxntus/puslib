def _seq_count_generator():
    seq_count = -1
    max_count = 2 ** 14
    while True:
        seq_count = (seq_count + 1) % max_count
        yield seq_count


class PusIdent:
    """Represents the identity of A PUS packet.

    The identity of a PUS packet consists of:

    - APID (Application ID)
    - packet sequence count

    The sequence count is per APID and spans [0..32767].

    The APID-sequence pair, thus, uniquely identifies a PUS packet for the foreseeable future.
    """
    def __init__(self, apid: int):
        """Create an identity instance.

        Arguments:
            apid -- application ID [0..2047]
        """
        if not 0 <= apid <= 2047:
            raise ValueError("APID must be between 0 and 2047")
        self._apid = apid
        self._seq_count_generator = _seq_count_generator()

    @property
    def apid(self) -> int:
        return self._apid

    def seq_count(self) -> int:
        """Returns next sequence count.

        Returns:
            sequence count [0..32767]
        """
        return next(self._seq_count_generator)
