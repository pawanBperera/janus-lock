from pathlib import Path
from januslock import storage


def test_create_and_load(tmp_path: Path):
    vault = tmp_path / "my.janus"

    key, salt = storage.create_vault(vault, "hunter2")
    plaintext, key2, salt2 = storage.load_vault(vault, "hunter2")

    assert plaintext == b""
    assert key == key2
    assert salt == salt2


def test_save_and_reload_roundtrip(tmp_path: Path):
    vault = tmp_path / "my.janus"
    key, salt = storage.create_vault(vault, "pw")

    storage.save_vault(vault, b"hello vault", key, salt)
    plaintext, _, _ = storage.load_vault(vault, "pw")

    assert plaintext == b"hello vault"


def test_wrong_password(tmp_path: Path):
    vault = tmp_path / "my.janus"
    storage.create_vault(vault, "correct")

    import pytest
    with pytest.raises(Exception):
        storage.load_vault(vault, "wrong")


def test_not_a_janus_file(tmp_path: Path):
    fake = tmp_path / "random.janus"
    fake.write_bytes(b"this is not a vault")

    import pytest
    with pytest.raises(ValueError):
        storage.load_vault(fake, "anything")