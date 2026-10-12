#!/usr/bin/env python3
"""Build or serve ignored local ProtoMotions documentation."""

import argparse
from datetime import datetime, timezone
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "external" / "ProtoMotions"
LOCAL = ROOT / ".local-docs" / "protomotions"


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def build():
    source = UPSTREAM / "docs" / "source"
    if not (source / "conf.py").is_file():
        raise SystemExit("Missing ProtoMotions sources. Run python3 scripts/setup.py first.")
    if shutil.which("uv") is None:
        raise SystemExit("Install uv first; see docs/installation.md.")
    LOCAL.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, UV_CACHE_DIR=str(LOCAL / "uv-cache"))
    env.pop("PYTHONPATH", None)
    python = LOCAL / "venv" / "bin" / "python"
    if not python.exists():
        run("uv", "venv", "--python", sys.executable, str(LOCAL / "venv"), env=env)
    run("uv", "pip", "install", "--python", str(python), "-r",
        str(UPSTREAM / "docs" / "requirements.txt"), env=env)
    # An old manifest must not imply that an interrupted rebuild completed.
    (LOCAL / "build-info.json").unlink(missing_ok=True)
    for builder in ("html", "text"):
        log = LOCAL / f"{builder}.log"
        print(f"Building {builder}; full output: {log}", flush=True)
        with log.open("w") as output:
            result = subprocess.run(
                [str(python), "-m", "sphinx", "-E", "-a", "-b", builder,
                 "-d", str(LOCAL / "doctrees" / builder), str(source),
                 str(LOCAL / builder)],
                cwd=source, env=env, stdout=output, stderr=subprocess.STDOUT,
            )
        if result.returncode:
            raise SystemExit(f"Sphinx failed. Inspect {log}")
        warnings = sum("WARNING:" in line for line in log.read_text().splitlines())
        print(f"Built {builder} ({warnings} warnings; see log).", flush=True)
    revision = subprocess.check_output(
        ["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(
        ["git", "-C", str(UPSTREAM), "status", "--porcelain"], text=True)
    packages = subprocess.check_output(
        ["uv", "pip", "freeze", "--python", str(python)], env=env, text=True)
    (LOCAL / "build-packages.txt").write_text(packages)
    (LOCAL / "build-info.json").write_text(json.dumps({
        "upstream_url": "https://github.com/NVlabs/ProtoMotions",
        "upstream_commit": revision,
        "upstream_dirty": bool(status.strip()),
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "builders": ["html", "text"],
    }, indent=2) + "\n")
    print(f"HTML: {LOCAL / 'html' / 'index.html'}\nText: {LOCAL / 'text'}")


def serve(port):
    directory = LOCAL / "html"
    if not (directory / "index.html").exists():
        raise SystemExit("Build first: python3 scripts/protomotions_docs.py build")
    from functools import partial
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"ProtoMotions docs: http://127.0.0.1:{server.server_port}/ (Ctrl+C to stop)", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build", help="Build HTML and searchable plain text")
    server = commands.add_parser("serve", help="Serve HTML on loopback only")
    server.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.command == "build":
        build()
    else:
        serve(args.port)


if __name__ == "__main__":
    main()
