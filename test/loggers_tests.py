import unittest
import logging
from unittest.mock import patch
from websocket_proxpy.util.loggers import ConsoleDebugLogger


class TestConsoleDebugLogger(unittest.TestCase):

    @patch('logging.getLogger')
    @patch('logging.StreamHandler')
    @patch('logging.Formatter')
    def test_log(self, mock_formatter, mock_stream_handler, mock_get_logger):
        logger_name = "test_logger"
        message = "Test message"
        logger_instance = ConsoleDebugLogger(logger_name)

        mock_logger = mock_get_logger.return_value
        mock_formatter_instance = mock_formatter.return_value
        mock_stream_handler_instance = mock_stream_handler.return_value

        logger_instance.log(message)

        mock_get_logger.assert_called_once_with(logger_name)
        mock_logger.setLevel.assert_called_once_with(logging.DEBUG)
        mock_logger.addHandler.assert_called_once_with(mock_stream_handler_instance)

        mock_formatter.assert_called_once_with('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        mock_stream_handler.assert_called_once_with()
        mock_stream_handler_instance.setFormatter.assert_called_once_with(mock_formatter_instance)

        mock_logger.debug.assert_called_once_with("WebSocketProxy: %s", message)


if __name__ == '__main__':
    unittest.main()
