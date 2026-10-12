"""Command line interface: `spotify-playlist login | build`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import auth
from .builder import build_playlist, format_report, parse_tracks
from .client import SpotifyClient, SpotifyError


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="spotify-playlist")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login", help="Log in to Spotify in your browser (one time)")
    b = sub.add_parser("build", help="Create a playlist from a track list file")
    b.add_argument("file", type=Path, help="Text file with one 'Artist – Title' per line")
    b.add_argument("--name", required=True, help="Playlist name")
    b.add_argument("--description", default="")
    b.add_argument("--public", action="store_true", help="Make the playlist public (default private)")
    b.add_argument("--dry-run", action="store_true", help="Match tracks but don't create anything")
    args = p.parse_args(argv)

    try:
        if args.cmd == "login":
            auth.login()
            print("Logged in.")
            return 0
        entries = parse_tracks(args.file.read_text(encoding="utf-8").splitlines())
        client = SpotifyClient(auth.get_access_token)
        result = build_playlist(
            client, entries, args.name, args.description, args.public, args.dry_run
        )
        print(format_report(result))
        return 0 if not result.missing else 2
    except (auth.AuthError, SpotifyError, ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
