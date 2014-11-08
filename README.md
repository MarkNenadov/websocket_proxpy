websocket_proxpy
================

A simple WebSocket proxy server implemented in Python 3.

--------------------------------------------------------

This server can run in one of two different modes:

1. OPEN_URL, where the connecting client provides a url to connect to via the proxy
2. FORCED_URL, where the server is hardwired to connect to one and only one url

== Requirements ==

1. Python 3 (tested on Python 3.4)
2. The 'websockets' module
3. The 'yaml' module

== Instructions ==

1. In config.yaml, ensure serverType is set to "OPEN_URL" (to allow clients to choose which URL to connect to) or
   "FORCED_URL" (to make the proxy always connect the client to the same url)

2. If you are using FORCED_URL, uncomment and set proxiedUrl to a valid websocket url. Otherwise it should be commented out with a "#"

3. Set the other configuration options, such as host, post, passphrase

4. From within the project root, launch proxy.py

5. Connect from a websocket client to the host/port in config.yaml, and send the password in json like so:

    {"password": "12345"}

    You will receive a json response where "status" is either "ok" or "error" with an elaboration in "message.

6. If you are using FORCED_URL, skip this step. Otherwise send the url you wish to connect to in json, like so:

    {"url": "ws://localhost:8081/test"}

    You will receive a json response where "status" is either "ok" or "error"  with an elaboration in "message.

7. Send X amount of further requests to pass along whatever you intend to send to the proxied websocket.
