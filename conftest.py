"""
Root conftest.py — exists mainly so SellerOS/ (this file's own
directory) ends up on sys.path before any test module is collected.

Why this matters: backend/, backend/auth/, backend/tests/, etc. have
no __init__.py, and every test file in them uses absolute imports like
`from backend.service.marketplace_service import MarketplaceService`.
That only resolves if SellerOS/ itself (backend's parent) is
importable as a path root. pytest's default "prepend" import mode
inserts a conftest.py's own directory into sys.path when it loads that
conftest — which, since SellerOS/ has no __init__.py either, happens
automatically the moment this file is discovered. The explicit insert
below is just a defensive belt-and-suspenders in case pytest is ever
invoked with a different --import-mode.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SELLEROS_ROOT = Path(__file__).resolve().parent
if str(_SELLEROS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SELLEROS_ROOT))
