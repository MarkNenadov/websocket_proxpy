from websocket_proxpy.proxy import WebSocketProxpy
from websocket_proxpy.util import loggers
from websocket_proxpy.util import base

try:
	import yaml
except ImportError:
    base.fatal_fail("'yaml' library required (pip install yaml). Exiting.")

CONFIG_FILE_NAME = "config.yaml"

config = yaml.load(open(CONFIG_FILE_NAME))

WebSocketProxpy(loggers.ConsoleDebugLogger()).run(config)

