import unittest
from websocket_proxpy.proxy import WebSocketProxpy, WebSocketConnection
from websocket_proxpy.util.loggers import ConsoleDebugLogger


class WebSocketProxpyTests(unittest.TestCase):
    web_socket_proxpy = WebSocketProxpy(ConsoleDebugLogger())

    def setUp(self):
        pass

    # is_close tests
    def test_is_close_with_non_json_text(self):
        self.assertFalse(self.web_socket_proxpy.is_close("xyz"))

    def test_is_close_with_non_matching_json(self):
        self.assertFalse(self.web_socket_proxpy.is_close("{\"action\": \"test\"}"))

    def test_is_close_with_matching_json(self):
        self.assertTrue(self.web_socket_proxpy.is_close("{\"action\": \"close\"}"))

    def test_get_post_authentication_directions(self):
        self.assertEquals("Authenticated. Supply URL.", self.web_socket_proxpy.get_post_authentication_directions())

    # authenticate tests
    def test_authenticate_without_credentials(self):
        connection = WebSocketConnection()
        self.assertFalse(self.web_socket_proxpy.authenticate(connection))

    def test_authenticate_with_matching_credentials(self):
        connection = WebSocketConnection()
        self.web_socket_proxpy.password = "test"
        connection.credentials = "{\"password\": \"test\"}"
        self.assertTrue(self.web_socket_proxpy.authenticate(connection))

    def test_authenticate_with_non_matching_credentials(self):
        connection = WebSocketConnection()
        self.web_socket_proxpy.password = "something else"
        self.assertFalse(self.web_socket_proxpy.authenticate(connection))

    def test_authenticate_with_bad_json(self):
        connection = WebSocketConnection()
        connection.credentials = "&\"password\": \"test\"}"
        self.assertFalse(self.web_socket_proxpy.authenticate(connection))

    # parse_destination_url tests
    def test_parse_destination_url(self):
        self.assertIsNone(self.web_socket_proxpy.parse_destination_url("blah"))
        self.assertIsNone(self.web_socket_proxpy.parse_destination_url("{\"yo\": \"hey\"}"))
        self.assertEqual("blah", self.web_socket_proxpy.parse_destination_url("{\"url\": \"blah\"}"))
        self.assertIsNone(self.web_socket_proxpy.parse_destination_url("*\"url\": \"blah\"}"))

    # has valid server type tests
    def test_has_valid_server_type(self):
        self.assertTrue(self.web_socket_proxpy.has_valid_server_type())

        self.web_socket_proxpy.serverType = "FORCED_URL_NO_PASSWORD"
        self.assertTrue(self.web_socket_proxpy.has_valid_server_type())

        self.web_socket_proxpy.serverType = "FORCED_URL"
        self.assertTrue(self.web_socket_proxpy.has_valid_server_type())

        self.web_socket_proxpy.serverType = "OPEN_URL"
        self.assertTrue(self.web_socket_proxpy.has_valid_server_type())

        self.web_socket_proxpy.serverType = "XYZ"
        self.assertFalse(self.web_socket_proxpy.has_valid_server_type())

    # is_forced_url_no_password_server tests
    def test_is_forced_url_no_password_server(self):
        self.assertFalse(self.web_socket_proxpy.is_forced_url_no_password_server())

        self.web_socket_proxpy.serverType = "FORCED_URL_NO_PASSWORD"
        self.assertTrue(self.web_socket_proxpy.is_forced_url_no_password_server())

        self.web_socket_proxpy.serverType = "FORCED_URL"
        self.assertFalse(self.web_socket_proxpy.is_forced_url_no_password_server())

        self.web_socket_proxpy.serverType = "OPEN_URL"
        self.assertFalse(self.web_socket_proxpy.is_forced_url_no_password_server())

    # is_force_url_server tests
    def test_is_forced_url_server(self):
        self.web_socket_proxpy = WebSocketProxpy(ConsoleDebugLogger())
        self.assertFalse(self.web_socket_proxpy.is_forced_url_server())

        self.web_socket_proxpy.serverType = "FORCED_URL_NO_PASSWORD"
        self.assertFalse(self.web_socket_proxpy.is_forced_url_server())

        self.web_socket_proxpy.serverType = "FORCED_URL"
        self.assertTrue(self.web_socket_proxpy.is_forced_url_server())

        self.web_socket_proxpy.serverType = "OPEN_URL"
        self.assertFalse(self.web_socket_proxpy.is_forced_url_server())

    # is_open_url_server tests
    def test_is_open_url_server(self):
        self.web_socket_proxpy = WebSocketProxpy(ConsoleDebugLogger())
        self.assertTrue(self.web_socket_proxpy.is_open_url_server())

        self.web_socket_proxpy.serverType = "FORCED_URL_NO_PASSWORD"
        self.assertFalse(self.web_socket_proxpy.is_open_url_server())

        self.web_socket_proxpy.serverType = "FORCED_URL"
        self.assertFalse(self.web_socket_proxpy.is_open_url_server())

        self.web_socket_proxpy.serverType = "OPEN_URL"
        self.assertTrue(self.web_socket_proxpy.is_open_url_server())


if __name__ == '__main__':
    unittest.main()