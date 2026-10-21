# spotify-playlist-builder

Builds Spotify playlists from an exact "Artist – Title" list. Ships a CLI (`spotify-playlist`) and an MCP
server (`spotify-playlist-mcp`) so Claude can call it as a connector.

## Commands
- Install: `pip install -e ".[dev]"`
- Test: `pytest`
- Lint: `ruff check .`
- CLI: `spotify-playlist setup` (saves Client ID), `spotify-playlist login`, then `spotify-playlist build tracks/skate1.txt --name "Skate 1" [--dry-run]`

## Layout
- `src/spotify_playlist_builder/auth.py`: PKCE browser login; token cached in `~/.spotify-playlist-builder/token.json`
- `client.py`: stdlib Web API client (search, create playlist, add items; retries on 429)
- `builder.py`: parse track lines, fuzzy-match on Spotify, create playlist, text report
- `cli.py`, `mcp_server.py`: the two front ends
- `tracks/`: track list files

## Gotchas
- Client ID comes from `SPOTIFY_CLIENT_ID` or `~/.spotify-playlist-builder/config.json` (written by `setup`).
  Every user makes their own Spotify app (dev mode: 5 users, owner needs Premium). The app must list `http://127.0.0.1:8888/callback` as a redirect URI.
- Uses post-Feb-2026 endpoints: `POST /me/playlists`, `POST /playlists/{id}/items`; search `limit` max is 10.
- Spotify dev-mode apps may require a Premium account; unverified here.
- Matching requires the artist to match and title similarity >= 0.6; unmatched tracks are reported, never guessed.

## Agent skills

### Issue tracker

Issues live in this repo's GitHub Issues, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
