import http.server
import urllib.request
import urllib.error
import os
import sys

BACKEND = "http://127.0.0.1:8001"


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def should_proxy(self, path):
        clean_path = path.split("?")[0]
        prefixes = ["/auth", "/requests", "/admin", "/attachments", "/webhook"]
        return any(clean_path == p or clean_path.startswith(p + "/") for p in prefixes)

    def do_GET(self):
        if self.should_proxy(self.path):
            return self._proxy("GET")
        return super().do_GET()

    def do_POST(self):
        if self.should_proxy(self.path):
            return self._proxy("POST")
        self.send_error(501, "Unsupported method ('POST')")

    def do_PATCH(self):
        if self.should_proxy(self.path):
            return self._proxy("PATCH")
        self.send_error(501, "Unsupported method ('PATCH')")

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
                content = resp.read()
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            body = e.read()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), ProxyHandler)
    print(f"Proxy server on port {port}")
    server.serve_forever()
