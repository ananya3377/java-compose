#!/usr/bin/env python3
"""Minimal offline Rekor v1 mock for verifier tests."""

from __future__ import annotations

import base64
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ARTIFACT_HASH = os.environ.get(
    "REKOR_MOCK_ARTIFACT_HASH",
    "656bde7e1569713382a6d1c57cd88e059e30bac5b2d8ab31f6ea1d0702ae0691",
)
SERVE_WRONG_HASH = os.environ.get("REKOR_MOCK_WRONG_HASH", "0") == "1"
HOST = os.environ.get("REKOR_MOCK_HOST", "127.0.0.1")
PORT = int(os.environ.get("REKOR_MOCK_PORT", "8787"))


def build_entry(log_index: int) -> dict:
    digest = "deadbeef" * 8 if SERVE_WRONG_HASH else ARTIFACT_HASH
    body = {
        "apiVersion": "0.0.1",
        "kind": "hashedrekord",
        "metadata": {
            "annotations": {
                "software.reproducibility": "true",
            }
        },
        "spec": {
            "data": {
                "hash": {
                    "algorithm": "sha256",
                    "value": digest,
                }
            },
            "signature": {
                "content": "c2ln",
                "publicKey": {"content": "cHVi"},
            },
        },
    }
    encoded = base64.b64encode(json.dumps(body, separators=(",", ":")).encode()).decode()
    uuid = f"mock-entry-{log_index}"
    return {
        uuid: {
            "logIndex": log_index,
            "body": encoded,
            "integratedTime": 1710000000,
        }
    }


class RekorHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/v1/log/entries":
            self.send_error(404)
            return
        params = parse_qs(parsed.query)
        if "logIndex" not in params:
            self.send_error(400, "logIndex required")
            return
        log_index = int(params["logIndex"][0])
        payload = build_entry(log_index)
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def start_server() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((HOST, PORT), RekorHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


if __name__ == "__main__":
    srv = start_server()
    print(f"rekor mock listening on http://{HOST}:{PORT}")
    threading.Event().wait()
