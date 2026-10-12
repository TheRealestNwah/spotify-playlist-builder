import pytest

from spotify_playlist_builder import auth


@pytest.fixture(autouse=True)
def tmp_config(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(auth, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)


def test_missing_client_id_raises():
    with pytest.raises(auth.AuthError):
        auth.get_client_id()


def test_saved_client_id_is_used():
    auth.save_client_id("  abc123 ")
    assert auth.get_client_id() == "abc123"


def test_env_overrides_saved(monkeypatch):
    auth.save_client_id("saved")
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "fromenv")
    assert auth.get_client_id() == "fromenv"
