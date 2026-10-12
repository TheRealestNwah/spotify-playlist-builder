# Contributing

Bug reports and pull requests are welcome.

1. Open an issue describing the bug or idea first (use the templates).
2. Fork, then create a branch: `git checkout -b my-change`.
3. Set up: `pip install -e ".[dev]"`
4. Make your change and add a test in `tests/` where it makes sense.
5. Check: `ruff check .` and `pytest` must both pass (CI runs the same).
6. Open a pull request that says `Closes #<issue number>`.

Matching bugs ("this song should have matched") are the most useful reports. Please include the exact
`Artist – Title` line and what Spotify has it listed as.

Never commit tokens, `config.json`, or `token.json`.
