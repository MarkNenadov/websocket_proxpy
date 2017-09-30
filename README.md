WebSocketProxpy
=========

A simple WebSocket Proxy Server implemented in Python 3.

This server can run in one of three modes:

1. OPEN_URL, where the connecting client provides a url to connect to via the proxy
2. FORCED_URL, where the server is hardwired to connect to one and only one url
2. FORCED_URL_NO_PASSWORD, where the server is hardwired to connect to one and only one url and no password is required.

== Requirements ==

1. Python 3 (tested on Python 3.4, 3.6)
2. The 'websockets' module (pip install websockets)
3. The 'yaml' module (pip install pyyaml)

== Instructions ==

1. In config.yaml, ensure serverType is set to OPEN_URL, FORCED_URL, or FORCED_URL_NO_PASSWORD

2. If you are using FORCED_URL or FORCED_URL_NO_PASSWORD, uncomment and set proxiedUrl to a valid websocket url.
   Otherwise it should be commented out with a "#"

3. Set the other configuration options, such as host, post, passphrase

4. From within the project root, launch proxy.py and connect from a websocket client to the host/port in config.yaml.

5. If you are using FORCED_URL_NO_PASSWORD, skip to step 7. Otherwise, send the password in json like so:

    {"password": "12345"}

    You will receive a json response where "status" is either "ok" or "error" with an elaboration in "message.

6. If you are using FORCED_URL or FORCED_URL_NO_PASSWORD, skip this step. Otherwise send the url you wish to connect
   to in json, like so:

    {"url": "ws://localhost:8081/test"}

    You will receive a json response where "status" is either "ok" or "error"  with an elaboration in "message.

7. Send X amount of websocket requests, which will be passed along to the proxied websocket.

8. When you are done and want to connection terminated, send:
    {"action": "close"}
