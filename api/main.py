# provisório até a api com FastAPI ficar pronta
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("api provisória no ar\n".encode())


HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
