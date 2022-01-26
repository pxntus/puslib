import struct
from collections import namedtuple

from .. import get_pus_policy
from .service import PusService, PusServiceType
from .error_codes import CommonErrorCode

_FuncDef = namedtuple('FuncDef', ['callback', 'arg_types'])


class FunctionManagement(PusService):
    def __init__(self, ident, pus_service_1):
        super().__init__(PusServiceType.FUNCTION_MANAGEMENT, ident, pus_service_1)
        super()._register_sub_service(1, self._perform)
        self._functions = {}

    def _perform(self, app_data):
        fid = get_pus_policy().function_management.function_id_type()
        try:
            fid.value = get_pus_policy().function_management.function_id_type.from_bytes(app_data[:fid.size])
        except struct.error:
            return CommonErrorCode.INCOMPLETE
        if fid.value not in self._functions:
            return CommonErrorCode.PUS8_INVALID_FID
        func_def = self._functions[fid.value]

        args = []
        offset = fid.size
        if func_def.arg_types:
            try:
                for arg in func_def.arg_types:
                    args.append(arg.from_bytes(app_data[offset:]))
                    offset += arg().size
            except struct.error:
                return CommonErrorCode.PUS8_INVALID_ARGS

        if offset != len(app_data):
            return CommonErrorCode.PUS8_INVALID_ARGS

        return func_def.callback(*args)

    def add(self, func, fid, args):
        self._functions[fid] = _FuncDef(func, args)
