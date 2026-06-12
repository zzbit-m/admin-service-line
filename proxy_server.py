import http.server
import urllib.request
import urllib.error
import os
import sys

BACKEND = "http://localhost:8001"


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/auth/"):
            return self._proxy("GET")
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/auth/"):
            return self._proxy("POST")
        return super().do_POST()

    def do_PATCH(self):
        if self.path.startswith("/admin/") or self.path.startswith("/requests/") or self.path.startswith("/attachments/"):
            return self._proxy("PATCH")
        return super().do_PATCH()

    def _proxy(self, method):
        body = None
        if method == "POST" or method == "PATCH":
            cl = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(cl) if cl > 0 else None

        req = urllib.request.Request(
            f"{BACKEND}{self.path}",
            data=body,
            headers={k: v for k, v in self.headers.items() if k.lower() not in ("host", "connection", "transfer-encoding")},
            method=method,
        )
        try:
            with urllib.request.urlopen(req) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding", "content-encoding", "content-length"):
                        self.send_header(k, v)
                self.send_header("Content-Length", str(len(resp.read())))
                self.end_headers()
                resp.seek(0)
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            body = e.read()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    server = http.server.HTTPServer(("0.0.0.0", port), ProxyHandler)
    print(f"Proxy server on port {port}")
    server.serve_forever()
