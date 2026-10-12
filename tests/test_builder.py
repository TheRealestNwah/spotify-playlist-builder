from pathlib import Path

import pytest

from spotify_playlist_builder.builder import (
    Entry,
    build_playlist,
    find_track,
    parse_tracks,
)


class FakeClient:
    def __init__(self, catalog):
        self.catalog = catalog  # list of (artist, title, uri)
        self.created = None
        self.added = []

    def search_tracks(self, query, limit=10):
        return [
            {"name": t, "uri": u, "artists": [{"name": a}]} for a, t, u in self.catalog
        ]

    def create_playlist(self, name, description="", public=False):
        self.created = (name, description, public)
        return {"id": "pl1", "external_urls": {"spotify": "https://open.spotify.com/playlist/pl1"}}

    def add_items(self, playlist_id, uris):
        self.added += uris


def test_parse_skips_comments_and_blanks():
    entries = parse_tracks(["# c", "", "Black Flag – Six Pack", "Gang Starr - Now You're Mine"])
    assert entries == [Entry("Black Flag", "Six Pack"), Entry("Gang Starr", "Now You're Mine")]


def test_parse_rejects_bad_line():
    with pytest.raises(ValueError):
        parse_tracks(["no separator here"])


def test_hyphenated_title_is_kept_whole():
    assert parse_tracks(["Artist – Half-Life"])[0].title == "Half-Life"


def test_skate1_file_parses_to_45():
    path = Path(__file__).parent.parent / "tracks" / "skate1.txt"
    assert len(parse_tracks(path.read_text(encoding="utf-8").splitlines())) == 45


def test_match_ignores_the_and_remaster_suffix():
    c = FakeClient([("Ramones", "Psycho Therapy (Remastered)", "spotify:track:1")])
    m = find_track(c, Entry("The Ramones", "Psycho Therapy"))
    assert m.uri == "spotify:track:1"


def test_match_split_title_half():
    c = FakeClient([("DEVO", "Gut Feeling", "spotify:track:2")])
    assert find_track(c, Entry("Devo", "Gut Feeling/Slap Your Mammy")).uri == "spotify:track:2"


def test_wrong_artist_is_rejected():
    c = FakeClient([("Someone Else", "Six Pack", "spotify:track:3")])
    assert find_track(c, Entry("Black Flag", "Six Pack")).uri is None


def test_build_creates_playlist_and_reports_missing():
    c = FakeClient([("Black Flag", "Six Pack", "spotify:track:4")])
    entries = [Entry("Black Flag", "Six Pack"), Entry("Nobody", "Nothing")]
    r = build_playlist(c, entries, "Skate")
    assert c.added == ["spotify:track:4"]
    assert [str(e) for e in r.missing] == ["Nobody – Nothing"]
    assert r.playlist_url.endswith("pl1")


def test_dry_run_creates_nothing():
    c = FakeClient([("Black Flag", "Six Pack", "spotify:track:4")])
    build_playlist(c, [Entry("Black Flag", "Six Pack")], "Skate", dry_run=True)
    assert c.created is None


def test_accent_folding():
    c = FakeClient([("Motörhead", "We Are Motörhead", "spotify:track:5")])
    assert find_track(c, Entry("Motorhead", "We Are Motorhead")).uri == "spotify:track:5"


def test_artist_spelling_variant():
    c = FakeClient([("Airbourne", "Let's Ride", "spotify:track:6")])
    assert find_track(c, Entry("Airborne", "Let's Ride")).uri == "spotify:track:6"


def test_demo_version_loses_to_original():
    c = FakeClient(
        [
            ("David Bowie", "Queen Bitch - Demo", "spotify:track:demo"),
            ("David Bowie", "Queen Bitch - 2015 Remaster", "spotify:track:orig"),
        ]
    )
    assert find_track(c, Entry("David Bowie", "Queen Bitch")).uri == "spotify:track:orig"
