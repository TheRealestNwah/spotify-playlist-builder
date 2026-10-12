# Spotify Playlist Builder

[![CI](https://github.com/TheRealestNwah/spotify-playlist-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/TheRealestNwah/spotify-playlist-builder/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Turn a plain text list of songs into a Spotify playlist. You give it `Artist – Title` lines; it finds each
song on Spotify and builds a private playlist in your own account, in order.

> **Built with AI.** This project's code, tests and documentation were written by
> Claude, an AI model from Anthropic, directed and tested by the maintainer.
> See [AI disclosure](#ai-disclosure).

It works two ways:

- **Command line:** `spotify-playlist build my-songs.txt --name "My Playlist"`
- **Claude connector (MCP):** ask Claude "make a playlist from this exact track list" and it calls the tool for you.

Handy for game, film and festival soundtracks, DJ sets, album tracklists, or any list you have written down.
An example is included: the [Skate (2007) soundtrack](tracks/skate1.txt).

## What you need

- Python 3.10 or newer
- A Spotify account. Spotify requires **Premium** for the app owner (that's you, see below).
- About 5 minutes for the one-time setup

## Install

```bash
pipx install git+https://github.com/TheRealestNwah/spotify-playlist-builder.git
```

No `pipx`? `pip install git+https://github.com/TheRealestNwah/spotify-playlist-builder.git` works too.

## One-time setup

Spotify only lets an app serve a handful of users unless it is a large company, so **everyone creates their
own free Spotify app** (it's just a Client ID, there is no password or secret to store).

1. Go to the [Spotify developer dashboard](https://developer.spotify.com/dashboard) and click **Create app**.
2. Name it anything. Under **Redirect URIs** add exactly: `http://127.0.0.1:8888/callback` and save.
3. Copy the app's **Client ID**.
4. Run:
   ```bash
   spotify-playlist setup
   spotify-playlist login
   ```
   Paste the Client ID when asked. `login` opens your browser so you can approve access.

Your Client ID and login token are saved in `~/.spotify-playlist-builder/` on your computer and nowhere else.

## Make a playlist

Write your songs in a text file, one per line, as `Artist – Title` (a normal hyphen with spaces also works):

```text
# lines starting with # are ignored
Black Flag – Six Pack
Gang Starr – Now You're Mine
Nirvana – Lounge Act
```

Preview the matches first, which creates nothing:

```bash
spotify-playlist build my-songs.txt --name "My Playlist" --dry-run
```

Then create it:

```bash
spotify-playlist build my-songs.txt --name "My Playlist"
```

The playlist is **private** unless you add `--public`. Songs that can't be found with confidence are listed at
the end and skipped, never guessed. Other options: `--description "text"`.

### How matching works

Each line is searched on Spotify. A result is accepted only if the artist matches (ignoring "The", accents and
small spelling differences) and the title is similar enough. Demo, live and remix versions are avoided unless
your line asks for one. Remasters are fine.

## Use it from Claude

Install as above, then register the connector.

**Claude Code:**
```bash
claude mcp add spotify-playlist -- spotify-playlist-mcp
```

**Claude Desktop:** add this to `claude_desktop_config.json` and restart:
```json
{ "mcpServers": { "spotify-playlist": { "command": "spotify-playlist-mcp" } } }
```

Do the one-time setup above first (`setup` and `login` in a terminal). Then ask Claude something like
*"Create a Spotify playlist called Road Trip from these tracks: ..."*. The tools are:

| Tool | What it does |
| --- | --- |
| `create_playlist_from_tracks` | Builds a playlist from `Artist – Title` strings. Supports `dry_run`, `public`, `description`. |
| `login` | Opens the Spotify login if you are logged out. |

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `INVALID_CLIENT: Invalid redirect URI` | The redirect URI in your Spotify app must be exactly `http://127.0.0.1:8888/callback`, and you must click Save. |
| `No Spotify Client ID configured` | Run `spotify-playlist setup`. |
| `Not logged in` | Run `spotify-playlist login`. |
| `403` errors from Spotify | The app owner needs Premium, and your account must be the app owner or on the app's user allowlist (Dashboard → your app → User Management). |
| Login page never opens | Copy the URL printed in the terminal into your browser. Port 8888 must be free. |
| A song is "not found" | It may not be on Spotify, or the spelling differs a lot. Try the title as Spotify spells it. |

## Limitations

- Only songs that exist in Spotify's catalog can be added.
- Spotify's development mode allows up to 5 users per app, which is why you use your own app.
- Spotify's API rules change; this uses the post-February-2026 endpoints.

## Development

```bash
git clone https://github.com/TheRealestNwah/spotify-playlist-builder.git
cd spotify-playlist-builder
pip install -e ".[dev]"
pytest
ruff check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Not affiliated with Spotify.

## AI disclosure

This project was built with [Claude Code](https://claude.com/claude-code), Anthropic's
AI coding assistant. Claude wrote the code, tests and documentation. The
maintainer ([@TheRealestNwah](https://github.com/TheRealestNwah)) decided what
it should do, tested it, and made the release decisions. Commits written with
Claude carry a `Co-Authored-By: Claude` trailer, so the git history shows which
changes were AI-written.

## Support

Everything on my GitHub is free of charge and open source. If you find it
useful and want to leave a tip or buy me a coffee, you can do that at
[ko-fi.com/morrowheat23](https://ko-fi.com/morrowheat23). It's appreciated,
never expected.

## License

MIT. See [LICENSE](LICENSE).
