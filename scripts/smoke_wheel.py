"""Install the wheel in a fresh environment and exercise its loopback UI."""
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    wheels = list((ROOT / "dist").glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit("Build exactly one wheel in dist/ before running the smoke check.")
    with tempfile.TemporaryDirectory(prefix="resolve-wheel-") as temporary:
        work = Path(temporary)
        environment = work / "venv"
        venv.create(environment, with_pip=True)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        subprocess.run([str(python), "-m", "pip", "install", "--no-deps", "--no-index", str(wheels[0])],
                       cwd=work, env=env, check=True)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        with (work / "server.log").open("w") as log:
            process = subprocess.Popen([str(python), "-m", "rootweaver_resolve.retained_workspace", "--port", str(port)],
                                       cwd=work, env=env, stdout=log, stderr=log)
            try:
                base = f"http://127.0.0.1:{port}"
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                for _ in range(100):
                    if process.poll() is not None:
                        raise RuntimeError((work / "server.log").read_text())
                    try:
                        with opener.open(base + "/", timeout=2) as response:
                            assert response.status == 200
                            assert b"workbench" in response.read().lower()
                        break
                    except urllib.error.URLError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError("Installed wheel server did not become ready")
                for path in ["/cases.html", "/workbench.mjs", "/workbench.css", "/data/http.json", "/data/investigation/session.json"]:
                    with opener.open(base + path, timeout=5) as response:
                        data = response.read()
                        assert response.status == 200 and data, path
                        if path.endswith(".json"):
                            json.loads(data)
                print("PASS: clean installed wheel serves workbench, console and complete data without private services")
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    main()
