import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

STATUS_OK = 200
STATUS_NOT_FOUND = 404
POLL_INTERVAL = 0.01


def make_server(routes):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = routes.get(self.path)
            if body is None:
                self.send_response(STATUS_NOT_FOUND)
                self.end_headers()
                return
            if not isinstance(body, bytes):
                body = json.dumps(body).encode("utf-8")
            self.send_response(STATUS_OK)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(
        target=server.serve_forever, args=(POLL_INTERVAL,), daemon=True
    )
    thread.start()
    return server


def server_url(server):
    return f"http://127.0.0.1:{server.server_address[1]}"


def stop_server(server):
    server.shutdown()
    server.server_close()
