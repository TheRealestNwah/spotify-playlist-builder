"""Thin Spotify Web API client (stdlib only)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable

API = "https://api.spotify.com/v1"


class SpotifyError(RuntimeError):
    pass


class SpotifyClient:
    def __init__(self, token_provider: Callable[[], str]):
        self._token = token_provider

    def _request(self, method: str, path: str, params: dict | None = None, body: dict | None = None):
        url = API + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(5):
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header("Authorization", f"Bearer {self._token()}")
            if data is not None:
                req.add_header("Content-Type", "application/json")
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw = resp.read()
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 4:
                    time.sleep(int(e.headers.get("Retry-After", "2")) + 1)
                    continue
                detail = e.read().decode(errors="replace")
                raise SpotifyError(f"{method} {path} failed ({e.code}): {detail}") from None
        raise SpotifyError(f"{method} {path} failed after retries")

    def search_tracks(self, query: str, limit: int = 10) -> list[dict]:
        # Search limit max is 10 (Feb 2026 API change).
        res = self._request("GET", "/search", {"q": query, "type": "track", "limit": min(limit, 10)})
        return res.get("tracks", {}).get("items", [])

    def create_playlist(self, name: str, description: str = "", public: bool = False) -> dict:
        return self._request(
            "POST", "/me/playlists", body={"name": name, "description": description, "public": public}
        )

    def add_items(self, playlist_id: str, uris: list[str]) -> None:
        for i in range(0, len(uris), 100):
            self._request("POST", f"/playlists/{playlist_id}/items", body={"uris": uris[i : i + 100]})
