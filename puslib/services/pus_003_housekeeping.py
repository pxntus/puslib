from .service import PusService


class Housekeeping(PusService):
    def __init__(self, ident, pus_service_1, tm_distributor):
        super().__init__(3, ident, pus_service_1, tm_distributor)
