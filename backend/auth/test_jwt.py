import time

import pytest
from jose import jwt

from backend.auth.jwt import create_access_token, decode_access_token
from backend.config.settings import settings


def test_create_and_decode_round_trip():
    payload = {"user_id": 1, "seller_id": 100}
    token = create_access_token(payload)

    decoded = decode_access_token(token)

    assert decoded["user_id"] == 1
    assert decoded["seller_id"] == 100
    assert "exp" in decoded


def test_token_is_signed_with_configured_secret_and_algorithm():
    token = create_access_token({"user_id": 1})

    # Decoding with the correct secret/algorithm must succeed --
    # confirms create_access_token actually used settings.SECRET_KEY /
    # settings.JWT_ALGORITHM rather than some other value.
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert decoded["user_id"] == 1


def test_garbage_token_returns_empty_dict():
    assert decode_access_token("this.is.not.a.valid.jwt") == {}


def test_token_signed_with_wrong_secret_is_rejected():
    forged = jwt.encode(
        {"user_id": 1, "exp": time.time() + 3600},
        "some-other-secret-the-server-never-configured",
        algorithm=settings.JWT_ALGORITHM,
    )
    assert decode_access_token(forged) == {}


def test_expired_token_is_rejected():
    expired = jwt.encode(
        {"user_id": 1, "exp": time.time() - 60},  # expired one minute ago
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    assert decode_access_token(expired) == {}


def test_token_with_wrong_algorithm_is_rejected():
    # HS256 is the configured algorithm; signing with HS384 instead
    # (still symmetric, same secret) must not verify.
    if settings.JWT_ALGORITHM == "HS384":
        pytest.skip("configured algorithm already HS384")
    wrong_alg = jwt.encode(
        {"user_id": 1, "exp": time.time() + 3600},
        settings.SECRET_KEY,
        algorithm="HS384",
    )
    assert decode_access_token(wrong_alg) == {}
