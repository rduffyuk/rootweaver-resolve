"""Loopback investigation viewer. Fresh retained-evidence analysis is explicit opt-in."""

import argparse
import functools
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .fresh_analysis import FreshAnalysis
from .nebius import ProviderError


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # No arbitrary request strings or provider details in access logs.

    def trusted_request(self, *, write=False):
        host = self.headers.get("Host")
        allowed = {
            f"127.0.0.1:{self.server.server_port}",
            f"localhost:{self.server.server_port}",
        }
        if host not in allowed:
            return False
        if write and self.headers.get("Origin") != "http://" + host:
            return False
        return self.headers.get("Sec-Fetch-Site") not in {"cross-site"}

    def json_response(self, status, body):
        wire = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(wire)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(wire)

    def do_GET(self):
        if not self.trusted_request():
            self.send_error(403)
            return
        path = urlsplit(self.path).path
        if path.startswith("/api/"):
            engine = self.server.analysis
            try:
                if path == "/api/analysis":
                    self.json_response(200, engine.status())
                elif path == "/api/analysis/input":
                    self.json_response(
                        200, {"request": engine.request, "sha256": engine.digest}
                    )
                elif path.startswith("/api/analysis/runs/"):
                    self.json_response(200, engine.result(path.rsplit("/", 1)[1]))
                else:
                    self.json_response(404, {"error": "unknown_endpoint"})
            except (ProviderError, ValueError, OSError):
                self.json_response(404, {"error": "record_unavailable"})
            return
        super().do_GET()

    def do_POST(self):
        engine = self.server.analysis
        if (
            not self.trusted_request(write=True)
            or self.headers.get("X-Resolve-Token") != engine.token
        ):
            self.json_response(403, {"error": "same_origin_required"})
            return
        if (
            self.path != "/api/analysis"
            or self.headers.get("Content-Type") != "application/json"
        ):
            self.json_response(400, {"error": "request_denied"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 1 <= size <= 512 or self.headers.get("Transfer-Encoding"):
                raise ValueError
            self.connection.settimeout(5)
            body = json.loads(self.rfile.read(size))
            if set(body) != {"case", "request_sha256"} or body["case"] != "http":
                raise ValueError
            run_id = engine.submit(body["request_sha256"])
            self.json_response(202, {"id": run_id})
        except ProviderError as error:
            self.json_response(409, {"error": str(error)})
        except (ValueError, TypeError, OSError):
            self.json_response(400, {"error": "invalid_request"})

    def list_directory(self, path):
        self.send_error(403, "Directory listing disabled")

    def end_headers(self):
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument(
        "--enable-live",
        action="store_true",
        help="Opt into at most two fresh Ultra calls on the fixed sanitised HTTP case",
    )
    parser.add_argument("--key-file", type=Path)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--freeze-sha256")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Choose an unprivileged port")
    assets = Path(__file__).with_name("workspace")
    if args.enable_live and not all(
        (args.key_file, args.state_dir, args.freeze_sha256)
    ):
        parser.error(
            "Live mode requires key-file, private state-dir and explicit freeze-sha256"
        )
    if not args.enable_live and any(
        (args.key_file, args.state_dir, args.freeze_sha256)
    ):
        parser.error("Credential and budget settings require explicit --enable-live")
    analysis = FreshAnalysis(
        assets, args.state_dir, key_file=args.key_file, freeze=args.freeze_sha256
    )
    serve(assets, args.port, analysis)


def serve(assets, port, analysis):
    server = ThreadingHTTPServer(
        ("127.0.0.1", port), functools.partial(Handler, directory=str(assets))
    )
    server.analysis = analysis
    print(
        f"Resolve 0.5.0 local review: http://127.0.0.1:{port}/ ; fresh analysis opt-in={bool(analysis.key_file)}; no cluster connection",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
