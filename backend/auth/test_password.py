from backend.auth.password import hash_password, verify_password


def test_hash_is_not_the_plaintext_password():
    password = "selleros123"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


def test_correct_password_verifies():
    password = "selleros123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_wrong_password_does_not_verify():
    hashed = hash_password("selleros123")

    assert verify_password("not-the-password", hashed) is False


def test_same_password_hashed_twice_produces_different_hashes():
    # bcrypt salts each hash independently -- two hashes of the same
    # password should never be byte-identical, even though both verify.
    password = "selleros123"
    hashed_a = hash_password(password)
    hashed_b = hash_password(password)

    assert hashed_a != hashed_b
    assert verify_password(password, hashed_a) is True
    assert verify_password(password, hashed_b) is True


def test_empty_password_is_rejected_on_verify():
    hashed = hash_password("selleros123")
    assert verify_password("", hashed) is False
