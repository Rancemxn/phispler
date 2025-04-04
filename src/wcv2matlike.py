import json
import typing
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import uilts

callback: typing.Callable[[bytes], typing.Any] = lambda x: None

class ArrayBufferHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()
        data = self.rfile.read(int(self.headers["Content-Length"]))
        callback(data)
        self.wfile.write(json.dumps({"status": 0}).encode())
        
    def log_request(self, *args, **kwargs) -> None: ...
    
def createServer():
    port = uilts.getNewPort()
    server_address = ("", port)
    httpd = HTTPServer(server_address, ArrayBufferHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    
    return httpd, port
