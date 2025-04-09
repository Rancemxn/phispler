import typing
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import utils

callback: typing.Callable[[bytes], typing.Any] = lambda x: None

class ArrayBufferHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        data = self.rfile.read(int(self.headers["Content-Length"]))
        callback(data)
        self.end_headers()
        
    def log_request(self, *args, **kwargs) -> None: ...
    
def createServer():
    port = utils.getNewPort()
    server_address = ("", port)
    httpd = HTTPServer(server_address, ArrayBufferHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    
    return httpd, port
