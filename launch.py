from websocket_proxpy.proxy import WebSocketProxpy
from websocket_proxpy.util import loggers
import yaml

CONFIG_FILE_NAME = "config.yaml"

config = yaml.load(open(CONFIG_FILE_NAME))

WebSocketProxpy(loggers.ConsoleDebugLogger()).run(config)

