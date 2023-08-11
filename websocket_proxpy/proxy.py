import sys
from websocket_proxpy.util import base

try:
    import websockets
except ImportError:
    base.fatal_fail("'websockets' library required (pip install websockets). Exiting.")
    sys.exit()

from websocket_proxpy.util.jsonutils import get_json_status_response
import asyncio
import json


async def send_to_web_socket_connection_aware(proxy_web_socket, proxied_web_socket, request_for_proxy):
    try:
        await proxied_web_socket.send(request_for_proxy)
    except websockets.exceptions.InvalidState:
        proxy_web_socket.send(get_json_status_response("ok", "Proxied connection closed."))


class WebSocketProxpy:
    logger = None
    host = "localhost"
    port = 1111
    serverType = "OPEN_URL"
    proxied_url = ""
    password = ""
    send_suffix = ""
    send_prefix = ""
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
        try:
            self.load_server_config_from_yaml(config_yaml)
            self.load_authentication_config_from_yaml(config_yaml)
            self.load_transport_config_from_yaml(config_yaml)
            return True
        except TypeError:
            return False

    async def proxy_dispatcher(self, proxy_web_socket, path):
        self.logger.log("Connection established with CLIENT")

        connection = WebSocketConnection()

        if not self.is_forced_url_no_password_server():
            connection.credentials = await self.get_credentials(proxy_web_socket)

            if self.authenticate(connection):
                authenticated_message = "Authenticated " + self.get_post_authentication_directions()
                await proxy_web_socket.send(get_json_status_response("ok", f"{authenticated_message}'"))
                if self.is_open_url_server():
                    proxied_url_value = await self.get_proxy_url_from_client(proxy_web_socket)
                    if proxied_url_value is None:
                        return
                else:
                    proxied_url_value = self.proxied_url

                proxied_web_socket = await self.connect_to_proxy_server(proxied_url_value, proxy_web_socket)
                await self.process_arbitrary_requests(proxy_web_socket, proxied_web_socket, connection)
            else:
                auth_failed_message = "Authentication failed. Password invalid [" + connection.credentials + "]"
                await proxy_web_socket.send(get_json_status_response("error", auth_failed_message + "'}"))
                self.logger.log("CLIENT authentication credentials [%s] rejected.", connection.credentials)
        else:
            proxied_url_value = self.proxied_url
            proxied_web_socket = await self.connect_to_proxy_server(proxied_url_value, proxy_web_socket)
            await self.process_arbitrary_requests(proxy_web_socket, proxied_web_socket, connection)

    async def respond_with_proxy_connect_error(self, proxied_url_value, proxy_web_socket):
        error_message = "Unable to connect with proxied url [" + proxied_url_value + "]. Connection closed."
        await proxy_web_socket.send(get_json_status_response("error", error_message + "'}"))
        self.logger.log(error_message)

    async def get_credentials(self, web_socket):
        credentials = await web_socket.recv()
        self.logger.log("Credentials received from CLIENT [%s]", credentials)

        return credentials

    def run(self, config_yaml):
        is_config_loaded = self.load_config_from_yaml(config_yaml)

        if not is_config_loaded:
            base.fatal_fail("Unable to load config file, can't parse the YAML!")

        server = websockets.serve(self.proxy_dispatcher, self.host, self.port)
        self.logger.log("Initializing PROXY SERVER")
        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

    async def process_arbitrary_requests(self, proxy_web_socket, proxied_web_socket, connection):
        while True:
            request_for_proxy = await proxy_web_socket.recv()
            self.logger.log("Received request from CLIENT [" + request_for_proxy + "]")

            if self.is_close(request_for_proxy):
                self.logger.log("Received CLOSE from CLIENT [" + request_for_proxy + "]")
                return

            if self.send_prefix is not None and self.send_suffix is not None:
                request_for_proxy = self.send_prefix + request_for_proxy + self.send_suffix
            await send_to_web_socket_connection_aware(proxy_web_socket, proxied_web_socket, request_for_proxy)
            connection.request_count += 1

            if connection.request_count > self.requests_per_connection:
                connection_limit_error = "Unable to proxy request, connection exceeds config limit of [" + str(
                    self.requests_per_connection) + "] requests per connection."
                self.logger.log(connection_limit_error)
                await proxy_web_socket.send(get_json_status_response("error", connection_limit_error))
                return

            self.logger.log(
                "Sending request [" + str(connection.request_count) + "] to PROXIED SERVER [" + request_for_proxy + "]")
            response_from_proxy = await proxied_web_socket.recv()
            self.logger.log("Received response from PROXIED SERVER [" + response_from_proxy + "]")
            await proxy_web_socket.send(response_from_proxy)
            self.logger.log("Sending response to CLIENT [" + response_from_proxy + "]")

    def load_authentication_config_from_yaml(self, config_yaml):
        authentication_configuration = config_yaml['configuration']['authenticationConfiguration']
        self.password = authentication_configuration['password']

    def load_transport_config_from_yaml(self, config_yaml):
        transport_configuration = config_yaml['configuration']['transportConfiguration']
        self.send_prefix = transport_configuration['sendPrefix']
        self.send_suffix = transport_configuration['sendSuffix']

    def load_server_config_from_yaml(self, config_yaml):
        server_config = config_yaml['configuration']['serverConfiguration']

        self.host = server_config['listenHost']
        self.port = int(server_config['port'])
        self.serverType = server_config['type']
        self.requests_per_connection = int(server_config['requestsPerConnection'])
        if not self.has_valid_server_type():
            self.logger.log("Server type value [" + self.serverType + "] in config is invalid. Can't start server")
            base.fatal_fail(None)

        if self.is_forced_url_server() or self.is_forced_url_no_password_server():
            self.proxied_url = server_config['proxiedUrl']

            if self.proxied_url is None or self.proxied_url == "":
                error_message = "Proxied url in config missing--required when running in FORCED_URL mode."
                self.logger.log(error_message)
                base.fatal_fail(None)

    def get_post_authentication_directions(self):
        authentication_message = "Authenticated. "

        if self.is_forced_url_server():
            authentication_message += "Socket open for arbitrary proxy requests."
        else:
            authentication_message += "Supply URL."

        return authentication_message

    def has_valid_server_type(self):
        return self.is_open_url_server() or self.is_forced_url_server() or self.is_forced_url_no_password_server()

    async def get_proxy_url_from_client(self, proxy_web_socket, ):
        proxied_url_json = await proxy_web_socket.recv()
        proxied_url_value = self.parse_destination_url(proxied_url_json)
        self.logger.log("PROXIED SERVER url received [" + proxied_url_value + "]")

        if proxied_url_value is None:
            url_missing_message = "Couldn't establish proxy. Url not provided in [" + proxied_url_json + "]"
            await proxy_web_socket.send(get_json_status_response("error", url_missing_message + "'}"))

        return proxied_url_value

    async def connect_to_proxy_server(self, proxied_url_value, proxy_web_socket):
        try:
            proxied_web_socket = await websockets.connect(proxied_url_value)
        except ConnectionRefusedError:
            await self.respond_with_proxy_connect_error(proxied_url_value, proxy_web_socket)
            return
        self.logger.log("Established proxied connection with PROXIED SERVER [" + proxied_url_value + "]")

        connection_open_message = "Proxied connection [" + proxied_url_value + "] open for arbitrary requests.'"
        await proxy_web_socket.send(get_json_status_response("ok", connection_open_message))

        return proxied_web_socket


class WebSocketConnection:
    request_count = 0
    credentials = ""
