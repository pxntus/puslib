from .service import PusService
from .error_codes import CommonErrorCode


class FunctionManagement(PusService):
    def __init__(self, ident, pus_service_1, tm_distributor, function_spec):
        super().__init__(8, ident, pus_service_1, tm_distributor)
        super()._register_sub_service(1, self._perform)
        self._functions = function_spec

    def _perform(self, app_data):
        fid_size = PusService.pus_policy.function_id_type.size
        if len(app_data) < fid_size:
            return False, CommonErrorCode.INCOMPLETE
        fid = PusService.pus_policy.function_id_type.unpack(app_data)
        if fid not in self._functions:
            return False, CommonErrorCode.PUS8_INVALID_FID

        f = self._functions[fid]
        if 'impl' not in f:
            return False, CommonErrorCode.PUS8_FUNCTION_NOT_IMPLEMENTED
        if len(app_data) != fid_size + f['struct'].size:
            return False, CommonErrorCode.ILLEGAL_APP_DATA
        args = f['struct'].unpack_from(app_data, fid_size)
        # TODO: Implement argument verification

        return f['impl'](*args)

    def function(self, func, fid):
        self._functions[fid]['impl'] = func

        def wrapper(*args, **kwargs):
            func(*args, **kwargs)

        return wrapper
