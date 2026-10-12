# spotify-playlist-builder

Create a Spotify playlist from an exact track list. Includes a CLI and an MCP connector for Claude.

## Setup
1. Create an app at https://developer.spotify.com/dashboard. Add redirect URI `http://127.0.0.1:8888/callback`.
2. Copy its Client ID and set it: `setx SPOTIFY_CLIENT_ID your_client_id` (Windows; reopen the terminal).
3. `pip install -e .`
4. `spotify-playlist login` (opens your browser once).

## Use
```
spotify-playlist build tracks/skate1.txt --name "Skate 1 Soundtrack" --dry-run
spotify-playlist build tracks/skate1.txt --name "Skate 1 Soundtrack"
```
Track files have one `Artist – Title` per line. Tracks not on Spotify are listed at the end.

## Connector (Claude)
Add an MCP server running `spotify-playlist-mcp` with `SPOTIFY_CLIENT_ID` in its environment. Tools: `login`,
`create_playlist_from_tracks`.
