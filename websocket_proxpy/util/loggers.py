import logging


class ConsoleDebugLogger():
    logger = None

    def __init__(self):
        self.logger = logging.getLogger('websocket_proxy')
        self.logger.setLevel(logging.DEBUG)

        logging_stream_handler = logging.StreamHandler()
        self.logger.addHandler(logging_stream_handler)

    def log(self, message):
        self.logger.debug("WebSocketProxy: " + message)