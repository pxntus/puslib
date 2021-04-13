from .pus_001_request_verification import RequestVerification
from .pus_003_housekeeping import Housekeeping
from .pus_005_event_reporting import EventReporting, Severity  # noqa: F401
from .pus_008_function_management import FunctionManagement
from .pus_017_test import Test
from .pus_020_parameter_management import ParameterManagement

# Aliases
PusService1 = RequestVerification
PusService3 = Housekeeping
PusService5 = EventReporting
PusService8 = FunctionManagement
PusService17 = Test
PusService20 = ParameterManagement
