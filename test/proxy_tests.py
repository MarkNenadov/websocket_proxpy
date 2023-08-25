import unittest
import yaml
from websocket_proxpy.proxy import WebSocketProxpy, WebSocketConnection
from websocket_proxpy.util.loggers import ConsoleDebugLogger


class WebSocketProxpyTests(unittest.TestCase):
    web_socket_proxpy = WebSocketProxpy(ConsoleDebugLogger('websocket_proxy'))

    def setUp(self) -> None:
        pass

    # load config from yaml tests
    def test_load_config_from_yam_when_empty(self) -> None:
        self.assertFalse(self.web_socket_proxpy.load_config_from_yaml(None))

    def test_load_config_from_yam_when_filled(self) -> None:
        proxpy = self.web_socket_proxpy
        self.assertEqual("", proxpy.password)
        self.assertEqual(1111, proxpy.port)
        self.assertEqual("localhost", proxpy.host)
        self.assertEqual("OPEN_URL", proxpy.serverType)
        self.assertEqual(10000, proxpy.requests_per_connection)
        self.assertEqual("", proxpy.proxied_url)
        self.assertEqual("", proxpy.send_prefix)
        self.assertEqual("", proxpy.send_suffix)
        with open("testConfig.yaml") as yamlFile:
            self.assertTrue(proxpy.load_config_from_yaml(yaml.load(yamlFile, Loader=yaml.Loader)))
        self.assertEqual("gogol", proxpy.password)
        self.assertEqual(7777, proxpy.port)
        self.assertEqual("192.168.1.10", proxpy.host)
        self.assertEqual("FORCED_URL", proxpy.serverType)
        self.assertEqual(500, proxpy.requests_per_connection)
        self.assertEqual("ws://localhost:8080/test", proxpy.proxied_url)
        self.assertEqual("prefix", proxpy.send_prefix)
        self.assertEqual("suffix", proxpy.send_suffix)

    # is_close tests
    def test_is_close_with_non_json_text(self) -> None:
        self.assertFalse(self.web_socket_proxpy.is_close("xyz"))

    def test_is_close_with_non_matching_json(self) -> None:
        self.assertFalse(self.web_socket_proxpy.is_close("{\"action\": \"test\"}"))

    def test_is_close_with_matching_json(self) -> None:
        self.assertTrue(self.web_socket_proxpy.is_close("{\"action\": \"close\"}"))

    def test_get_post_authentication_directions(self) -> None:
        self.assertEqual("Authenticated. Supply URL.", self.web_socket_proxpy.get_post_authentication_directions())

    # authenticate tests
    def test_authenticate_without_credentials(self) -> None:
        connection = WebSocketConnection()
        self.assertFalse(self.web_socket_proxpy.authenticate(connection))

    def test_authenticate_with_matching_credentials(self) -> None:
        connection = WebSocketConnection()
        self.web_socket_proxpy.password = "test"
        connection.credentials = "{\"password\": \"test\"}"
        self.assertTrue(self.web_socket_proxpy.authenticate(connection))

    def test_authenticate_with_non_matching_credentials(self) -> None:
        connection = WebSocketConnection()
        self.web_socket_proxpy.password = "something else"
        self.assertFalse(self.web_socket_proxpy.authenticate(connection))
        self.web_socket_proxpy.password = ""

        connection = WebSocketConnection()
        connection.credentials = "&\"password\": \"test\"}"
        self.assertFalse(self.web_socket_proxpy.authenticate(connection))

    # parse_destination_url tests
    def test_parse_destination_url(self) -> None:
        proxpy = self.web_socket_proxpy
        self.assertIsNone(proxpy.parse_destination_url("blah"))
        self.assertIsNone(proxpy.parse_destination_url("{\"yo\": \"hey\"}"))
        self.assertEqual("blah", proxpy.parse_destination_url("{\"url\": \"blah\"}"))
        self.assertIsNone(proxpy.parse_destination_url("*\"url\": \"blah\"}"))

    # has valid server type tests
    def test_has_valid_server_type(self) -> None:
        proxpy = self.web_socket_proxpy
        self.assertTrue(proxpy.has_valid_server_type())

        proxpy.serverType = "FORCED_URL_NO_PASSWORD"
        self.assertTrue(proxpy.has_valid_server_type())

        proxpy.serverType = "FORCED_URL"
        self.assertTrue(proxpy.has_valid_server_type())

        proxpy.serverType = "OPEN_URL"
        self.assertTrue(proxpy.has_valid_server_type())

        proxpy.serverType = "XYZ"
        self.assertFalse(proxpy.has_valid_server_type())

    # is_forced_url_no_password_server tests
    def test_is_forced_url_no_password_server(self) -> None:
        proxpy = self.web_socket_proxpy
        self.assertFalse(proxpy.is_forced_url_no_password_server())

        proxpy.serverType = "FORCED_URL_NO_PASSWORD"
        self.assertTrue(proxpy.is_forced_url_no_password_server())

        proxpy.serverType = "FORCED_URL"
        self.assertFalse(proxpy.is_forced_url_no_password_server())

        proxpy.serverType = "OPEN_URL"
        self.assertFalse(proxpy.is_forced_url_no_password_server())

    # is_force_url_server tests
    def test_is_forced_url_server(self) -> None:
        self.web_socket_proxpy = WebSocketProxpy(ConsoleDebugLogger('websocket_proxy'))
        self.assertFalse(self.web_socket_proxpy.is_forced_url_server())

        self.web_socket_proxpy.serverType = "FORCED_URL_NO_PASSWORD"
        self.assertFalse(self.web_socket_proxpy.is_forced_url_server())

        self.web_socket_proxpy.serverType = "FORCED_URL"
        self.assertTrue(self.web_socket_proxpy.is_forced_url_server())

        self.web_socket_proxpy.serverType = "OPEN_URL"
        self.assertFalse(self.web_socket_proxpy.is_forced_url_server())

    # is_open_url_server tests
    def test_is_open_url_server(self) -> None:
        self.web_socket_proxpy = WebSocketProxpy(ConsoleDebugLogger('websocket_proxy'))
        self.assertTrue(self.web_socket_proxpy.is_open_url_server())

        self.web_socket_proxpy.serverType = "FORCED_URL_NO_PASSWORD"
        self.assertFalse(self.web_socket_proxpy.is_open_url_server())

        self.web_socket_proxpy.serverType = "FORCED_URL"
        self.assertFalse(self.web_socket_proxpy.is_open_url_server())

        self.web_socket_proxpy.serverType = "OPEN_URL"
        self.assertTrue(self.web_socket_proxpy.is_open_url_server())


if __name__ == '__main__':
    unittest.main()
