import logging


class ConsoleDebugLogger:
    logger = None

    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        logging_stream_handler = logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging_stream_handler.setFormatter(formatter)

        self.logger.addHandler(logging_stream_handler)

    def log(self, message: str) -> None:
        self.logger.debug("WebSocketProxy: %s", message)
