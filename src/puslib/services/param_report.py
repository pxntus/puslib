import struct
from collections import OrderedDict
from typing import Type

from puslib import get_policy
from puslib.parameter import Parameter


class ParamReport:
    """Parameter report used by housekeeping and event reporting services.

    A parameter report serializes to the following format:

      +-----------+-------------------+-------------------+-------------+
      | report ID | Parameter value 1 | Parameter value 2 |     ...     |
      +-----------+-------------------+-------------------+-------------+

    where number of parameter values is deduced from report ID.
    """
    def __init__(self, sid: int, enabled: bool = True, params_in_report: dict[int, Type[Parameter]] | None = None):
        """Create a parameter report.

        Arguments:
            sid -- structure ID

        Keyword Arguments:
            enabled -- report enabled at startup (default: {True})
            params_in_report -- parameters part of report (default: {None})
        """
        self._id = sid
        self._params = OrderedDict()
        self._enabled = enabled
        self._cached_struct = None
        self.append(params_in_report)

    def __len__(self):
        return len(self._params)

    def __iter__(self):
        for param_id, param in self._params.items():
            yield param_id, param

    def __bytes__(self):
        args = [self._id]
        if self._params:
            args.extend([p.value for p in self._params.values()])
        return self._cached_struct.pack(*args)

    @property
    def id(self) -> int:
        return self._id

    @property
    def enabled(self) -> bool:
        return self._enabled

    def append(self, params: dict[int, Type[Parameter]]):
        """Append parameters to report.

        Arguments:
            params -- parameters to append to report
        """
        if params is not None:
            self._params = {**self._params, **params}

        fmt = get_policy().common.param_id_type().format
        if len(self._params) > 0:
            fmt += "".join([p.format for p in self._params.values()])
            fmt = '>' + fmt.replace('>', '')
        self._cached_struct = struct.Struct(fmt)

    def enable(self):
        """Enable report.
        """
        self._enabled = True

    def disable(self):
        """Disable report.
        """
        self._enabled = False
