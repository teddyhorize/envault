"""Tests for envault.env_ttl."""

import time
import pytest

from envault.vault import Vault
from envault.env_ttl import (
    TTLError,
    set_ttl,
    get_ttl,
    is_expired,
    clear_ttl,
    list_ttl,
    purge_expired,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="secret")
    v.set("API_KEY", "abc123")
    v.set("DB_PASS", "hunter2")
    return v


def test_set_ttl_returns_future_timestamp(vault):
    expiry = set_ttl(vault, "API_KEY", 60)
    assert expiry > time.time()


def test_set_ttl_stores_seconds(vault):
    set_ttl(vault, "API_KEY", 120)
    info = get_ttl(vault, "API_KEY")
    assert info is not None
    assert info["ttl_seconds"] == 120


def test_get_ttl_returns_none_when_not_set(vault):
    assert get_ttl(vault, "DB_PASS") is None


def test_get_ttl_returns_info_after_set(vault):
    set_ttl(vault, "DB_PASS", 30)
    info = get_ttl(vault, "DB_PASS")
    assert info is not None
    assert "expires_at" in info


def test_is_expired_false_for_future_ttl(vault):
    set_ttl(vault, "API_KEY", 3600)
    assert not is_expired(vault, "API_KEY")


def test_is_expired_true_for_past_ttl(vault):
    set_ttl(vault, "API_KEY", -1)  # already expired
    # Manually backdated via monkey-patching expiry
    import json
    from pathlib import Path
    p = Path(vault.path).with_suffix(".ttl.json")
    data = json.loads(p.read_text())
    data["API_KEY"]["expires_at"] = time.time() - 10
    p.write_text(json.dumps(data))
    assert is_expired(vault, "API_KEY")


def test_is_expired_false_when_no_ttl(vault):
    assert not is_expired(vault, "API_KEY")


def test_clear_ttl_removes_entry(vault):
    set_ttl(vault, "API_KEY", 60)
    result = clear_ttl(vault, "API_KEY")
    assert result is True
    assert get_ttl(vault, "API_KEY") is None


def test_clear_ttl_returns_false_when_not_set(vault):
    assert clear_ttl(vault, "API_KEY") is False


def test_list_ttl_returns_all_entries(vault):
    set_ttl(vault, "API_KEY", 60)
    set_ttl(vault, "DB_PASS", 120)
    entries = list_ttl(vault)
    assert "API_KEY" in entries
    assert "DB_PASS" in entries


def test_purge_expired_removes_expired_keys(vault):
    import json
    from pathlib import Path
    set_ttl(vault, "API_KEY", 60)
    p = Path(vault.path).with_suffix(".ttl.json")
    data = json.loads(p.read_text())
    data["API_KEY"]["expires_at"] = time.time() - 5
    p.write_text(json.dumps(data))
    purged = purge_expired(vault)
    assert "API_KEY" in purged
    assert vault.get("API_KEY") is None


def test_purge_expired_leaves_valid_keys(vault):
    set_ttl(vault, "API_KEY", 3600)
    purged = purge_expired(vault)
    assert "API_KEY" not in purged
    assert vault.get("API_KEY") == "abc123"


def test_set_ttl_empty_key_raises(vault):
    with pytest.raises(TTLError):
        set_ttl(vault, "", 60)


def test_set_ttl_missing_key_raises(vault):
    with pytest.raises(TTLError):
        set_ttl(vault, "NONEXISTENT", 60)


def test_set_ttl_zero_seconds_raises(vault):
    with pytest.raises(TTLError):
        set_ttl(vault, "API_KEY", 0)
