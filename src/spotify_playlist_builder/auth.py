"""Spotify Authorization Code + PKCE login (no client secret needed)."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
REDIRECT_HOST = "127.0.0.1"
REDIRECT_PORT = 8888
REDIRECT_URI = f"http://{REDIRECT_HOST}:{REDIRECT_PORT}/callback"
SCOPES = "playlist-modify-private playlist-modify-public"
CONFIG_DIR = Path.home() / ".spotify-playlist-builder"
TOKEN_PATH = CONFIG_DIR / "token.json"
CONFIG_PATH = CONFIG_DIR / "config.json"


class AuthError(RuntimeError):
    pass


def save_client_id(client_id: str) -> None:
    client_id = client_id.strip()
    if not client_id:
        raise AuthError("Client ID is empty.")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps({"client_id": client_id}))


def get_client_id() -> str:
    """Client ID from SPOTIFY_CLIENT_ID, else from the file written by `spotify-playlist setup`."""
    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    if not client_id:
        try:
            client_id = json.loads(CONFIG_PATH.read_text()).get("client_id", "").strip()
        except (OSError, ValueError):
            client_id = ""
    if not client_id:
        raise AuthError(
            "No Spotify Client ID configured. Run `spotify-playlist setup` "
            "(see the README for how to create a Spotify app)."
        )
    return client_id


def _post_token(params: dict[str, str]) -> dict:
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        raise AuthError(f"Token request failed ({e.code}): {e.read().decode(errors='replace')}")


def _save(token: dict, previous: dict | None = None) -> dict:
    token = dict(token)
    token["expires_at"] = time.time() + int(token.get("expires_in", 3600))
    # Refresh responses may omit a new refresh_token; keep the old one.
    if "refresh_token" not in token and previous:
        token["refresh_token"] = previous.get("refresh_token", "")
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(token))
    return token


def _load() -> dict | None:
    try:
        return json.loads(TOKEN_PATH.read_text())
    except (OSError, ValueError):
        return None


def login(open_browser: bool = True, timeout: int = 180) -> dict:
    """Run the browser login flow and store the token."""
    client_id = get_client_id()
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    )
    state = secrets.token_urlsafe(16)
    result: dict[str, str] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in q or "error" in q:
                result.update({k: v[0] for k, v in q.items()})
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Login complete. You can close this tab.")
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *args):
            pass

    server = HTTPServer((REDIRECT_HOST, REDIRECT_PORT), Handler)
    server.timeout = 1
    url = AUTH_URL + "?" + urllib.parse.urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "state": state,
            "code_challenge_method": "S256",
            "code_challenge": challenge,
        }
    )
    print(f"Open this URL to log in to Spotify:\n{url}", flush=True)
    if open_browser:
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
    deadline = time.time() + timeout
    try:
        while not result and time.time() < deadline:
            server.handle_request()
    finally:
        server.server_close()
    if not result:
        raise AuthError("Timed out waiting for the Spotify login.")
    if "error" in result:
        raise AuthError(f"Spotify login failed: {result['error']}")
    if result.get("state") != state:
        raise AuthError("State mismatch in login callback; aborting.")
    token = _post_token(
        {
            "grant_type": "authorization_code",
            "code": result["code"],
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "code_verifier": verifier,
        }
    )
    return _save(token)


def get_access_token() -> str:
    """Return a valid access token, refreshing if needed. Raises AuthError if not logged in."""
    token = _load()
    if not token or not token.get("refresh_token"):
        raise AuthError("Not logged in. Run `spotify-playlist login` first.")
    if token["expires_at"] - 60 > time.time():
        return token["access_token"]
    refreshed = _post_token(
        {
            "grant_type": "refresh_token",
            "refresh_token": token["refresh_token"],
            "client_id": get_client_id(),
        }
    )
    return _save(refreshed, previous=token)["access_token"]
