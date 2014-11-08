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
        parsedJson = json.loads(connection.credentials)

        if ('password' not in parsedJson):
            return False
        elif parsedJson['password'] != self.password:
            return False;
        else:
            self.logger.log( "User authenticated." )
            return True

    def parse_destination_url(self, json_content ):
        # expects {"url": "ws://localhost:8081/test"}
        parsedJson = json.loads(json_content)

        if ('url' not in parsedJson):
            return None
        return parsedJson['url']

    def is_close(self, json_content):
        # expects {"action": "close"}
        parsedJson = json.loads(json_content)

        if ('action' not in parsedJson):
            return False

        if parsedJson['action'] != "close":
            return False

        return True

    def loadConfigFromYaml(self, configYaml):
        self.loadServerConfigFromYaml(configYaml)
        self.loadAuthenticationConfigFromYaml(configYaml)

    @asyncio.coroutine
    def proxy_dispatcher(self, proxy_web_socket, path):
        self.logger.log("Connection established with CLIENT")

        connection = WebSocketConnection()

        if not self.is_forced_url_no_password_server():
            connection.credentials = yield from self.get_credentials(proxy_web_socket)

            if self.authenticate( connection ):
                yield from proxy_web_socket.send( get_json_status_response( "ok", "Authenticated " + self.get_post_authentication_directions() + "'}" ) )
                proxied_url_value = ""
                if self.is_open_url_server():
                    proxied_url_json = yield from proxy_web_socket.recv()
                    proxied_url_value = self.parse_destination_url( proxied_url_json )
                    self.logger.log("PROXIED SERVER url received [" + proxied_url_value + "]")

                    if (proxied_url_value == None):
                        yield from proxy_web_socket.send( get_json_status_response( "error", "Could not establish proxy. Url not provided in [" + proxied_url_json + "]'}" ) )
                        return
                else:
                    proxied_url_value = self.proxied_url

                proxied_web_socket = yield from websockets.connect( proxied_url_value )
                self.logger.log("Established connection with PROXIED SERVER [" + proxied_url_value + "]")
                yield from proxy_web_socket.send( get_json_status_response( "ok", "Proxied connection [" + proxied_url_value + "] open for arbitrary requests.'" ) )

                yield from self.process_arbitrary_requests(proxy_web_socket, proxied_web_socket, connection)
            else:
                yield from self.proxy_web_socket.send( get_json_status_response( "error", "Could not authenticate. Valid password not provided in [" + connection.credentials + "]'}" ) )
                self.logger.log( "CLIENT authentication credentials [" + connection.credentials + "] rejected.")
        else:
            proxied_url_value = self.proxied_url
            proxied_web_socket = yield from websockets.connect( proxied_url_value )
            self.logger.log("Established connection with PROXIED SERVER [" + proxied_url_value + "]")

            yield from self.process_arbitrary_requests(proxy_web_socket, proxied_web_socket, connection)

    def get_credentials(self, web_socket):
        credentials = yield from web_socket.recv()
        self.logger.log("Credentials received from CLIENT [" + credentials + "]")
        return credentials

    def run(self, configYaml):
        self.loadConfigFromYaml(configYaml)
        server = websockets.serve(self.proxy_dispatcher, self.host, self.port)
        self.logger.log("Initializing PROXY SERVER")
        asyncio.get_event_loop().run_until_complete( server )
        asyncio.get_event_loop().run_forever()

    def process_arbitrary_requests(self, proxy_web_socket, proxied_web_socket, connection):
            while True:
                request_for_proxy = yield from proxy_web_socket.recv()
                self.logger.log("Received request from CLIENT [" + request_for_proxy + "]")

                if self.is_close(request_for_proxy):
                    self.logger.log("Received CLOSE from CLIENT [" + request_for_proxy + "]")
                    return

                yield from proxied_web_socket.send( request_for_proxy )
                connection.request_count += 1

                if connection.request_count > self.requests_per_connection:
                    connection_limit_error = "Unable to proxy  request, connection exceeds config limit of [" + str(self.requests_per_connection) + "] requests per connection."
                    self.logger.log( connection_limit_error )
                    yield from proxy_web_socket.send( get_json_status_response( "error", connection_limit_error ) )
                    return

                self.logger.log( "Sending request [" + str(connection.request_count) + "] to PROXIED SERVER [" + request_for_proxy + "]")
                response_from_proxy = yield from proxied_web_socket.recv()
                self.logger.log( "Received response from PROXIED SERVER [" + response_from_proxy + "]")
                yield from proxy_web_socket.send( response_from_proxy )
                self.logger.log( "Sending response to CLIENT [" + response_from_proxy + "]")

    def loadAuthenticationConfigFromYaml(self, configYaml):
        authenticationConfiguration = configYaml['configuration']['authenticationConfiguration']
        self.password = authenticationConfiguration['password']

    def loadServerConfigFromYaml(self, configYaml):
        serverConfiguration = configYaml['configuration']['serverConfiguration']

        self.host = serverConfiguration['listenHost']
        self.port = int(serverConfiguration['port'])
        self.serverType = serverConfiguration['type']
        self.requests_per_connection = int(serverConfiguration['requestsPerConnection'])
        if not self.has_valid_server_type():
            self.logger.log("Server type value [" + self.serverType + "] in config is invalid. Can't start server")
            sys.exit(0)

        if (self.is_forced_url_server() or self.is_forced_url_no_password_server()):
            self.proxied_url = serverConfiguration['proxiedUrl']

            if ( self.proxied_url == None or self.proxied_url == ""):
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