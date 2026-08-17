"""Simple server that serves galaxy_explorer.html and proxies Pulsar AI requests.

The API key stays on the server - never sent to the browser.

Usage:
    python server.py
    # Opens at http://localhost:8780
"""

import http.server
import json
import os
import urllib.request

PORT = int(os.environ.get("PORT", 8780))

env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/chat":
            self._proxy_chat()
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.path = "/galaxy_explorer.html"
        super().do_GET()

    def _proxy_chat(self):
        if not API_KEY:
            self.send_error(500, "No API key configured on server")
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as resp:
                result = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(result)
        except urllib.error.HTTPError as e:
            error_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(error_body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


if __name__ == "__main__":
    if not API_KEY:
        print("WARNING: No ANTHROPIC_API_KEY found. Pulsar AI will not work.")
    else:
        print("API key loaded from .env")

    server = http.server.HTTPServer(("", PORT), ProxyHandler)
    print(f"Serving at http://localhost:{PORT}")
    server.serve_forever()
