import sys
from websocket_proxpy.proxy import WebSocketProxpy
from websocket_proxpy.util import loggers
from websocket_proxpy.util import base

try:
    import yaml
except ImportError:
    base.fatal_fail("'yaml' library required (pip install yaml). Exiting.")
    sys.exit()

CONFIG_FILE_NAME = "config.yaml"

config = yaml.load(open(CONFIG_FILE_NAME), Loader=yaml.SafeLoader)

WebSocketProxpy(loggers.ConsoleDebugLogger('websocket_proxy')).run(config)
