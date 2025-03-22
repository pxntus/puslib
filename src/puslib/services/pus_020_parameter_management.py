import struct
from typing import SupportsBytes, Type

from puslib import get_policy
from puslib.ident import PusIdent
from puslib.parameter import Parameter
from puslib.streams.stream import OutputStream
from puslib.services import RequestVerification
from puslib.services.service import PusService, PusServiceType


class ParameterManagement(PusService):
    """PUS service 20: Parameter management service."""

    def __init__(self, ident: PusIdent, pus_service_1: RequestVerification, tm_output_stream: OutputStream, params: dict[int, Type[Parameter]]):
        """Create a PUS service instance.

        Arguments:
            ident -- PUS identifier
            pus_service_1 -- PUS service 1 instance
            tm_output_stream -- output stream
            params -- parameters to manage
        """
        super().__init__(PusServiceType.ONBOARD_PARAMETER_MANAGEMENT, ident, pus_service_1, tm_output_stream)
        super()._register_sub_service(1, self._report_parameter_values)
        super()._register_sub_service(3, self._set_parameter_values)
        self._params = params

    def _report_parameter_values(self, app_data: SupportsBytes):
        """Handle report parameter values request.

        Arguments:
            app_data -- application data of TC request

        Returns:
            subservice status
        """
        num_ids = get_policy().function_management.count_type()
        param_id_dummy = get_policy().common.param_id_type()
        try:
            num_ids.value = num_ids.from_bytes(app_data)
            fmt = ">" + f"{num_ids.value}{param_id_dummy.format}".replace('>', '')
            ids = struct.unpack(fmt, app_data[len(num_ids):])
        except struct.error:
            return False
        if not all(param_id in self._params for param_id in ids):
            return False

        fmt = num_ids.format
        fmt += "".join([f"{param_id_dummy.format}{self._params[param_id].format}" for param_id in ids])
        fmt = '>' + fmt.replace('>', '')
        values = [self._params[param_id].value for param_id in ids]
        source_data = struct.pack(fmt, num_ids.value, *[arg for pair in zip(ids, values) for arg in pair])
        time = get_policy().CucTime()
        packet = get_policy().PusTmPacket(
            apid=self._ident.apid,
            seq_count=self._ident.seq_count(),
            service_type=self._service_type.value,
            service_subtype=2,
            time=time,
            data=source_data
        )
        self._tm_output_stream.write(packet)
        return True

    def _set_parameter_values(self, app_data: SupportsBytes):
        """Handle set parameter values request.

        Arguments:
            app_data -- application data of TC request

        Returns:
            subservice status
        """
        try:
            num_values = get_policy().function_management.count_type().from_bytes(app_data)
            new_values = {}
            offset = len(get_policy().function_management.count_type())
            for _ in range(num_values):
                param_id = get_policy().common.param_id_type().from_bytes(app_data[offset:])
                offset += len(get_policy().common.param_id_type())
                if param_id not in self._params or param_id in new_values:
                    return False
                param = self._params[param_id]
                param_value = param.from_bytes(app_data[offset:])
                offset += len(param)
                new_values[param_id] = param_value
        except struct.error:
            return False

        for pid, val in new_values.items():
            self._params[pid].value = val
        return True
