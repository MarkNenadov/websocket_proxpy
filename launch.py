from websocket_proxpy.proxy import WebSocketProxpy
from websocket_proxpy.util import loggers
import yaml

CONFIG_FILE_NAME = "config.yaml"

configYaml = yaml.load(open(CONFIG_FILE_NAME))

WebSocketProxpy(loggers.ConsoleDebugLogger()).run(configYaml)

