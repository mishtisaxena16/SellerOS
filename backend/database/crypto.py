"""
crypto.py — transparent encryption-at-rest for sensitive JSON columns.

THE GAP THIS CLOSES
-----------------------------------------------------------------------
MarketplaceAccount.credentials was a plain `JSON` column: seller
marketplace passwords / API keys / tokens were written to selleros.db
as readable JSON. Anyone with read access to the DB file (a backup, a
misconfigured volume mount, an unrelated SQL-injection bug elsewhere,
a laptop with the sqlite file on it) gets every connected seller's
live marketplace credentials in plaintext.

FIX
-----------------------------------------------------------------------
`EncryptedJSON` is a SQLAlchemy TypeDecorator: same Python-side
interface as `JSON` (models/services still just assign and read a
plain dict), but the value is Fernet-encrypted before it touches the
database and decrypted after it comes back. No API/service/connector
code changes -- only the column type declaration in the model.

KEY SOURCE
-----------------------------------------------------------------------
Derived from `settings.SECRET_KEY` (already required to be a real,
random value in production by `assert_secret_key_is_safe` at startup
-- see backend/config/settings.py). Reusing that guard means there is
no separate "did you forget to set the encryption key" failure mode
to introduce; if SECRET_KEY is safe, the encryption key is safe.

BACKWARD COMPATIBILITY
-----------------------------------------------------------------------
Rows written before this change hold plain JSON text, not a Fernet
token. On read, if Fernet decryption fails (InvalidToken -- the
expected shape for old plaintext rows), fall back to parsing the raw
value as JSON directly rather than raising. The next `connect_marketplace`
call for that row re-encrypts it on write, so existing installs migrate
row-by-row on next use instead of needing a manual migration script.
"""
from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.types import String, TypeDecorator

from backend.config.settings import settings


def _derive_fernet_key(secret: str) -> bytes:
    """
    Fernet requires a 32-byte, urlsafe-base64-encoded key. SECRET_KEY
    is an arbitrary string (used elsewhere for JWT signing), so hash
    it down to 32 bytes first rather than requiring a second secret to
    configure and keep in sync.
    """
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _fernet() -> Fernet:
    return Fernet(_derive_fernet_key(settings.SECRET_KEY))


class EncryptedJSON(TypeDecorator):
    """
    Drop-in replacement for sqlalchemy.JSON that encrypts at rest.
    Python-side value is still a plain dict; only the DB-side
    representation changes (JSON blob -> encrypted text token).
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Any, dialect) -> Any:
        if value is None:
            return None
        plaintext = json.dumps(value)
        token = _fernet().encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def process_result_value(self, value: Any, dialect) -> Any:
        if value is None:
            return None
        try:
            plaintext = _fernet().decrypt(value.encode("utf-8"))
            return json.loads(plaintext)
        except InvalidToken:
            # Pre-existing plaintext row from before encryption was
            # added. Read it as-is; it will be re-encrypted the next
            # time this row is written.
            return json.loads(value)
