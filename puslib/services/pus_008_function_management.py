from puslib import get_pus_policy
from .service import PusService, PusServiceType
from .error_codes import CommonErrorCode


class FunctionManagement(PusService):
    def __init__(self, ident, pus_service_1, tm_distributor):
        super().__init__(PusServiceType.FUNCTION_MANAGEMENT, ident, pus_service_1, tm_distributor)
        super()._register_sub_service(1, self._perform)
        self._functions = {}

    def _perform(self, app_data):
        fid = get_pus_policy().IdType()
        if len(app_data) < fid.size:
            return CommonErrorCode.INCOMPLETE
        fid.value = int.from_bytes(app_data[:fid.size], byteorder='big')
        if fid.value not in self._functions:
            return CommonErrorCode.PUS8_INVALID_FID
        f = self._functions[fid.value]

        # TODO: Implement argument unpacking.

        return f()

    def add(self, func, fid):
        self._functions[fid] = func
