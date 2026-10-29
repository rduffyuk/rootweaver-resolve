"""Local synthetic demo server. Fixed assets/routes, bounded JSON, no executor."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from rootweaver_resolve.application import Application, Conflict

ASSETS = Path(__file__).with_name("web")
ROUTES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.mjs": ("app.mjs", "text/javascript; charset=utf-8"),
    "/presenter.mjs": ("presenter.mjs", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}


def make_server(port=8766, *, application=None):
    application = application or Application()

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, format, *args):
            pass  # No payload, URL, header or exception logging.

        def send(self, status, body, content_type="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; script-src 'self'; style-src 'self'; "
                "connect-src 'self'; img-src 'self'; frame-ancestors 'none'; "
                "base-uri 'none'; form-action 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def answer(self, status, value):
            self.send(status, json.dumps(value, allow_nan=False).encode())

        def valid_host(self):
            port = self.server.server_address[1]
            return self.headers.get("Host") in {
                f"127.0.0.1:{port}",
                f"localhost:{port}",
            }

        def do_GET(self):
            if not self.valid_host():
                return self.answer(403, {"error": "loopback host required"})
            if self.path == "/api/state":
                return self.answer(200, application.snapshot())
            if self.path == "/favicon.ico":
                return self.send(204, b"")
            if self.path in ROUTES:
                filename, mime = ROUTES[self.path]
                return self.send(200, (ASSETS / filename).read_bytes(), mime)
            return self.answer(404, {"error": "unknown route"})

        def do_POST(self):
            origin = self.headers.get("Origin")
            if (
                not self.valid_host()
                or (origin is not None and origin != f"http://{self.headers['Host']}")
                or self.headers.get("Sec-Fetch-Site") == "cross-site"
            ):
                return self.answer(
                    403, {"error": "same-origin loopback request required"}
                )
            if self.path not in {"/api/reset", "/api/step"}:
                return self.answer(404, {"error": "unknown route"})
            if self.headers.get_content_type() != "application/json":
                return self.answer(415, {"error": "application/json required"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 4096 or self.headers.get("Transfer-Encoding"):
                    raise ValueError("body bound")
                data = json.loads(self.rfile.read(size))
                expected = {"investigation_id", "revision"}
                if self.path == "/api/reset":
                    expected.add("scenario")
                if not isinstance(data, dict) or set(data) != expected:
                    raise ValueError("request schema")
                if self.path == "/api/reset":
                    value = application.reset(
                        data["scenario"], data["investigation_id"], data["revision"]
                    )
                else:
                    value = application.step(data["investigation_id"], data["revision"])
                return self.answer(200, value)
            except Conflict:
                return self.answer(
                    409, {"error": "workspace changed; reload to continue"}
                )
            except (ValueError, TypeError, KeyError):
                return self.answer(400, {"error": "invalid bounded request"})

    return HTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument(
        "--controller-led",
        action="store_true",
        help="Offline controller-owned acquisition; no provider or credentials",
    )
    args = parser.parse_args()
    with make_server(
        args.port, application=Application(controller_led=args.controller_led)
    ) as server:
        print(
            f"Resolve synthetic replay: http://127.0.0.1:{server.server_address[1]}",
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
