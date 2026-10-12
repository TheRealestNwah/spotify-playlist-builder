"""Parse a track list, match each entry on Spotify, and build the playlist."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .client import SpotifyClient

_SEP = re.compile(r"\s+[–—-]\s+")
MIN_TITLE_SCORE = 0.6


@dataclass
class Entry:
    artist: str
    title: str

    def __str__(self) -> str:
        return f"{self.artist} – {self.title}"


@dataclass
class Match:
    entry: Entry
    uri: str | None = None
    found: str = ""


@dataclass
class BuildResult:
    matches: list[Match] = field(default_factory=list)
    playlist_url: str | None = None

    @property
    def missing(self) -> list[Entry]:
        return [m.entry for m in self.matches if m.uri is None]

    @property
    def uris(self) -> list[str]:
        return [m.uri for m in self.matches if m.uri]


def parse_tracks(lines: list[str]) -> list[Entry]:
    """Parse 'Artist – Title' lines. Blank lines and '#' comments are skipped."""
    entries = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = _SEP.split(line, maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"Expected 'Artist – Title', got: {line!r}")
        entries.append(Entry(parts[0].strip(), parts[1].strip()))
    return entries


_ALT_VERSION = re.compile(
    r"(?<![a-z])(demo|live|remix|karaoke|instrumental|acoustic|cover|tribute)(?![a-z])", re.IGNORECASE
)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))  # Motörhead -> Motorhead
    s = s.lower()
    s = re.sub(r"\(.*?\)|\[.*?\]", " ", s)  # drop "(Remastered)" style suffixes
    s = re.sub(r"\bthe\b", " ", s)
    return re.sub(r"[^a-z0-9]", "", s)


def _artist_matches(want: str, got: str) -> bool:
    # Substring match, or near-identical spelling (e.g. "Airborne" vs "Airbourne").
    return want in got or got in want or SequenceMatcher(None, want, got).ratio() >= 0.88


def _score(entry: Entry, track: dict) -> float:
    want_artist = _norm(entry.artist)
    artists = [_norm(a["name"]) for a in track.get("artists", [])]
    if not any(_artist_matches(want_artist, a) for a in artists if a):
        return 0.0
    title = _norm(entry.title)
    got = _norm(track["name"])
    score = SequenceMatcher(None, title, got).ratio()
    # Titles like "Gut Feeling/Slap Your Mammy" may match on either half.
    for half in re.split(r"[/]", entry.title):
        score = max(score, SequenceMatcher(None, _norm(half), got).ratio())
    # Prefer the original recording over demos/live/remixes unless the entry asks for one.
    if _ALT_VERSION.search(track["name"]) and not _ALT_VERSION.search(entry.title):
        score -= 0.3
    return score


def find_track(client: SpotifyClient, entry: Entry) -> Match:
    queries = [
        f'track:"{entry.title}" artist:"{entry.artist}"',
        f"{entry.title} {entry.artist}",
    ]
    best, best_score = None, 0.0
    for q in queries:
        for track in client.search_tracks(q):
            score = _score(entry, track)
            if score > best_score:
                best, best_score = track, score
        if best_score >= 0.95:
            break
    if best and best_score >= MIN_TITLE_SCORE:
        names = ", ".join(a["name"] for a in best["artists"])
        return Match(entry, best["uri"], f"{names} – {best['name']}")
    return Match(entry)


def build_playlist(
    client: SpotifyClient,
    entries: list[Entry],
    name: str,
    description: str = "",
    public: bool = False,
    dry_run: bool = False,
) -> BuildResult:
    result = BuildResult(matches=[find_track(client, e) for e in entries])
    if dry_run or not result.uris:
        return result
    playlist = client.create_playlist(name, description, public)
    client.add_items(playlist["id"], result.uris)
    result.playlist_url = playlist.get("external_urls", {}).get("spotify")
    return result


def format_report(result: BuildResult) -> str:
    lines = []
    for m in result.matches:
        lines.append(f"  ✓ {m.entry}  →  {m.found}" if m.uri else f"  ✗ {m.entry}  (not found)")
    found = len(result.uris)
    lines.append(f"\nMatched {found}/{len(result.matches)} tracks.")
    if result.missing:
        lines.append("Not on Spotify (or no confident match):")
        lines += [f"  - {e}" for e in result.missing]
    if result.playlist_url:
        lines.append(f"\nPlaylist: {result.playlist_url}")
    return "\n".join(lines)
