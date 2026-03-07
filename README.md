# websocket-proxpy

A lightweight WebSocket proxy server written in Python 3.

## Modes

| Mode | Description |
|---|---|
| `OPEN_URL` | Client specifies the upstream URL to connect to |
| `FORCED_URL` | Server is hardwired to one upstream URL; client must authenticate |
| `FORCED_URL_NO_PASSWORD` | Server is hardwired to one upstream URL; no authentication required |

## Requirements

- Python 3.9+
- `websockets` — `pip install websockets`
- `pyyaml` — `pip install pyyaml`

## Configuration

Edit `config.yaml` before starting the server:

```yaml
configuration:
    authenticationConfiguration:
        password: "yourpassword"
    serverConfiguration:
        type: "FORCED_URL_NO_PASSWORD"   # OPEN_URL | FORCED_URL | FORCED_URL_NO_PASSWORD
        listenHost: "localhost"
        port: "1111"
        requestsPerConnection: "10000"
        proxiedUrl: "ws://localhost:9001" # required for FORCED_URL and FORCED_URL_NO_PASSWORD
    transportConfiguration:
        sendPrefix: ""
        sendSuffix: ""
```

## Running

```bash
python3 launch.py
```

## Protocol

Once connected, the exchange depends on the server mode.

### OPEN_URL and FORCED_URL — authenticate first

```json
→ {"password": "yourpassword"}
← {"status": "ok", "message": "..."}
```

### OPEN_URL — then provide the upstream URL

```json
→ {"url": "ws://upstream-host:port/path"}
← {"status": "ok", "message": "..."}
```

### Send requests / receive responses

```json
→ "your message"
← "proxied response"
```

### Close the connection

```json
→ {"action": "close"}
```

All error responses have the form `{"status": "error", "message": "..."}`.

## Running Tests

```bash
python3 -m unittest test.proxy_tests test.loggers_tests -v
```
