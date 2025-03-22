import struct
from collections import namedtuple
from collections.abc import Callable
from typing import SupportsBytes, Sequence

from puslib import get_policy
from puslib.ident import PusIdent
from puslib.parameter import Parameter
from puslib.services import RequestVerification
from puslib.services.service import PusService, PusServiceType
from puslib.services.error_codes import CommonErrorCode

_FuncDef = namedtuple('FuncDef', ['callback', 'arg_types'])


class FunctionManagement(PusService):
    """PUS service 8: Function management service."""

    def __init__(self, ident: PusIdent, pus_service_1: RequestVerification):
        """Create a PUS service instance.

        Arguments:
            ident -- PUS identifier
            pus_service_1 -- PUS service 1 instance
        """
        super().__init__(PusServiceType.FUNCTION_MANAGEMENT, ident, pus_service_1)
        super()._register_sub_service(1, self._perform)
        self._functions = {}

    def _perform(self, app_data: SupportsBytes):
        """Handle function request.

        Arguments:
            app_data -- application data of TC request

        Returns:
            subservice status
        """
        fid = get_policy().function_management.function_id_type()
        try:
            fid.value = get_policy().function_management.function_id_type.from_bytes(app_data[:len(fid)])
        except struct.error:
            return CommonErrorCode.INCOMPLETE
        if fid.value not in self._functions:
            return CommonErrorCode.PUS8_INVALID_FID
        func_def = self._functions[fid.value]

        args = []
        offset = len(fid)
        if func_def.arg_types:
            try:
                for arg in func_def.arg_types:
                    args.append(arg.from_bytes(app_data[offset:]))
                    offset += len(arg())
            except struct.error:
                return CommonErrorCode.PUS8_INVALID_ARGS

        if offset != len(app_data):
            return CommonErrorCode.PUS8_INVALID_ARGS

        return func_def.callback(*args)

    def add(self, func: Callable, fid: int, args: Sequence[Parameter]):
        """Add function handler.

        Arguments:
            func -- function handler
            fid -- function ID
            args -- function arguments
        """
        self._functions[fid] = _FuncDef(func, args)
