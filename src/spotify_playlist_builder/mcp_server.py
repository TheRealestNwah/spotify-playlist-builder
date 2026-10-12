"""MCP connector: lets Claude build playlists from an exact track list."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import auth
from .builder import build_playlist, format_report, parse_tracks
from .client import SpotifyClient, SpotifyError

mcp = FastMCP("spotify-playlist-builder")


@mcp.tool()
def login() -> str:
    """Log in to Spotify. Opens a browser window; call once, or if other tools say you're logged out."""
    try:
        auth.login()
    except auth.AuthError as e:
        return f"Login failed: {e}"
    return "Logged in to Spotify."


@mcp.tool()
def create_playlist_from_tracks(
    name: str,
    tracks: list[str],
    description: str = "",
    public: bool = False,
    dry_run: bool = False,
) -> str:
    """Create a Spotify playlist containing specific tracks.

    `tracks` is a list of "Artist – Title" strings. Each is searched on Spotify and the best
    match is added in order. With dry_run=true nothing is created; the matches are just reported.
    Returns a report listing matched tracks, tracks not found, and the playlist URL.
    """
    try:
        entries = parse_tracks(tracks)
        client = SpotifyClient(auth.get_access_token)
        result = build_playlist(client, entries, name, description, public, dry_run)
    except (auth.AuthError, SpotifyError, ValueError) as e:
        return f"Error: {e}"
    return format_report(result)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
