import struct

from puslib import get_pus_policy


class ParamReport:
    """Parameter report used by housekeeping and event reporting services.

    A parameter report serializes to the following format:

      +-----------+-------------------+-------------------+-------------+
      | report ID | Parameter value 1 | Parameter value 2 |     ...     |
      +-----------+-------------------+-------------------+-------------+

    where number of parameter values is deduced from report ID.
    """
    def __init__(self, sid, enabled=True, params_in_report=None):
        self._id = sid
        self._params = params_in_report
        self._enabled = enabled

        fmt = get_pus_policy().IdType().format
        if params_in_report:
            fmt += "".join([p.format for p in params_in_report.values()])
        fmt = '>' + fmt.replace('>', '')
        self._cached_struct = struct.Struct(fmt)

    def __len__(self):
        return len(self._params)

    def __iter__(self):
        for param_id, param in self._params.items():
            yield param_id, param

    @property
    def id(self):
        return self._id

    @property
    def enabled(self):
        return self._enabled

    def to_bytes(self):
        args = [self._id]
        if self._params:
            args.extend([p.value for p in self._params.values()])
        return self._cached_struct.pack(*args)

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False
