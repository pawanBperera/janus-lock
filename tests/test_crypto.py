from januslock import crypto


def test_roundtrip():
    salt = crypto.generate_salt()
    key = crypto.derive_key("correct horse battery staple", salt)
    plaintext = b"my secret notes"

    blob = crypto.encrypt(plaintext, key)
    recovered = crypto.decrypt(blob, key)

    assert recovered == plaintext


def test_wrong_password_fails():
    salt = crypto.generate_salt()
    key_good = crypto.derive_key("right-password", salt)
    key_bad = crypto.derive_key("wrong-password", salt)

    blob = crypto.encrypt(b"top secret", key_good)

    import pytest
    with pytest.raises(Exception):   # InvalidTag, specifically
        crypto.decrypt(blob, key_bad)


def test_tampered_data_fails():
    salt = crypto.generate_salt()
    key = crypto.derive_key("pw", salt)

    blob = bytearray(crypto.encrypt(b"important", key))
    blob[-1] ^= 0x01   # flip one bit at the end

    import pytest
    with pytest.raises(Exception):
        crypto.decrypt(bytes(blob), key)