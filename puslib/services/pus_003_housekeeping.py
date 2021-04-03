from .service import PusService, PusServiceType


class Housekeeping(PusService):
    def __init__(self, ident, pus_service_1, tm_output_stream):
        super().__init__(PusServiceType.HOUSEKEEPING, ident, pus_service_1, tm_output_stream)
