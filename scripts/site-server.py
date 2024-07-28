import os
from http.server import HTTPServer, SimpleHTTPRequestHandler


def startup_site_server():
    os.chdir("site")
    server = HTTPServer(("0.0.0.0", 8008), SimpleHTTPRequestHandler)
    print("Serving at: http://0.0.0.0:8008")
    server.serve_forever()


startup_site_server()
