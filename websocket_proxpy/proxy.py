import websockets
import asyncio
import sys
import json
from websocket_proxpy.util.jsonutils import get_json_status_response


class WebSocketProxpy:
    logger = None
    host = "localhost"
    port = 1111
    serverType = "OPEN_URL"
    proxied_url = ""
    password = ""
    requests_per_connection = 10000

    def __init__(self, logger):
        self.logger = logger

    def is_open_url_server(self):
        return self.serverType == "OPEN_URL"

    def is_forced_url_server(self):
        return self.serverType == "FORCED_URL"

    def is_forced_url_no_password_server(self):
        return self.serverType == "FORCED_URL_NO_PASSWORD"

    def authenticate(self, connection):
        # expects {"password": "12345"}
        try:
            parsed_json = json.loads(connection.credentials)
        except ValueError:
            return False

        if 'password' not in parsed_json:
            return False
        elif parsed_json['password'] != self.password:
            return False
        else:
            self.logger.log("User authenticated.")
            return True

    @staticmethod
    def parse_destination_url(json_content):
        # expects {"url": "ws://localhost:8081/test"}
        try:
            parsed_json = json.loads(json_content)
        except ValueError:
            return None

        if 'url' not in parsed_json:
            return None
        return parsed_json['url']

    @staticmethod
    def is_close(json_content):
        # expects {"action": "close"}
        try:
            parsed_json = json.loads(json_content)
        except ValueError:
            return None

        if 'action' not in parsed_json:
            return False

        if parsed_json['action'] != "close":
            return False

        return True

    def load_config_from_yaml(self, config_yaml):
        self.load_server_config_from_yaml(config_yaml)
        self.load_authentication_config_from_yaml(config_yaml)

    @asyncio.coroutine
    def proxy_dispatcher(self, proxy_web_socket, path):
        self.logger.log("Connection established with CLIENT")

        connection = WebSocketConnection()

        if not self.is_forced_url_no_password_server():
            connection.credentials = yield from self.get_credentials(proxy_web_socket)

            if self.authenticate(connection):
                authenticated_message = "Authenticated " + self.get_post_authentication_directions()
                yield from proxy_web_socket.send(get_json_status_response("ok", authenticated_message + "'}"))
                if self.is_open_url_server():
                    proxied_url_json = yield from proxy_web_socket.recv()
                    proxied_url_value = self.parse_destination_url(proxied_url_json)
                    self.logger.log("PROXIED SERVER url received [" + proxied_url_value + "]")

                    if proxied_url_value is None:
                        url_missing_message = "Couldn't establish proxy. Url not provided in [" + proxied_url_json + "]"
                        yield from proxy_web_socket.send(get_json_status_response("error", url_missing_message + "'}"))
                        return
                else:
                    proxied_url_value = self.proxied_url

                proxied_web_socket = yield from websockets.connect(proxied_url_value)
                self.logger.log("Established connection with PROXIED SERVER [" + proxied_url_value + "]")
                connection_open_message = "Proxied connection [" + proxied_url_value + "] open for arbitrary requests.'"
                yield from proxy_web_socket.send(get_json_status_response("ok", connection_open_message))

                yield from self.process_arbitrary_requests(proxy_web_socket, proxied_web_socket, connection)
            else:
                auth_failed_message = "Authentication failed. Password invalid [" + connection.credentials + "]"
                yield from proxy_web_socket.send(get_json_status_response("error", auth_failed_message + "'}"))
                self.logger.log("CLIENT authentication credentials [" + connection.credentials + "] rejected.")
        else:
            proxied_url_value = self.proxied_url
            proxied_web_socket = yield from websockets.connect(proxied_url_value)
            self.logger.log("Established connection with PROXIED SERVER [" + proxied_url_value + "]")

            yield from self.process_arbitrary_requests(proxy_web_socket, proxied_web_socket, connection)

    def get_credentials(self, web_socket):
        credentials = yield from web_socket.recv()
        self.logger.log("Credentials received from CLIENT [" + credentials + "]")
        return credentials

    def run(self, config_yaml):
        self.load_config_from_yaml(config_yaml)
        server = websockets.serve(self.proxy_dispatcher, self.host, self.port)
        self.logger.log("Initializing PROXY SERVER")
        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

    def process_arbitrary_requests(self, proxy_web_socket, proxied_web_socket, connection):
        while True:
            request_for_proxy = yield from proxy_web_socket.recv()
            self.logger.log("Received request from CLIENT [" + request_for_proxy + "]")

            if self.is_close(request_for_proxy):
                self.logger.log("Received CLOSE from CLIENT [" + request_for_proxy + "]")
                return

            yield from proxied_web_socket.send(request_for_proxy)
            connection.request_count += 1

            if connection.request_count > self.requests_per_connection:
                connection_limit_error = "Unable to proxy  request, connection exceeds config limit of [" + str(
                    self.requests_per_connection) + "] requests per connection."
                self.logger.log(connection_limit_error)
                yield from proxy_web_socket.send(get_json_status_response("error", connection_limit_error))
                return

            self.logger.log(
                "Sending request [" + str(connection.request_count) + "] to PROXIED SERVER [" + request_for_proxy + "]")
            response_from_proxy = yield from proxied_web_socket.recv()
            self.logger.log("Received response from PROXIED SERVER [" + response_from_proxy + "]")
            yield from proxy_web_socket.send(response_from_proxy)
            self.logger.log("Sending response to CLIENT [" + response_from_proxy + "]")

    def load_authentication_config_from_yaml(self, config_yaml):
        authentication_configuration = config_yaml['configuration']['authenticationConfiguration']
        self.password = authentication_configuration['password']

    def load_server_config_from_yaml(self, config_yaml):
        server_config = config_yaml['configuration']['serverConfiguration']

        self.host = server_config['listenHost']
        self.port = int(server_config['port'])
        self.serverType = server_config['type']
        self.requests_per_connection = int(server_config['requestsPerConnection'])
        if not self.has_valid_server_type():
            self.logger.log("Server type value [" + self.serverType + "] in config is invalid. Can't start server")
            sys.exit(0)

        if self.is_forced_url_server() or self.is_forced_url_no_password_server():
            self.proxied_url = server_config['proxiedUrl']

            if self.proxied_url is None or self.proxied_url == "":
                self.logger.log("Proxied url in config is missing. It is invalid when running in FORCED_URL mode. Can't start server")
                sys.exit(0)

    def get_post_authentication_directions(self):
        authentication_message = "Authenticated. "

        if self.is_forced_url_server():
            authentication_message += "Socket open for arbitrary proxy requests."
        else:
            authentication_message += "Supply URL."

        return authentication_message

    def has_valid_server_type(self):
        return self.is_open_url_server() or self.is_forced_url_server() or self.is_forced_url_no_password_server()


class WebSocketConnection:
    request_count = 0
    credentials = ""

    def __init__(self):
        pass