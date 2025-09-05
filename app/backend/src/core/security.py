from __future__ import annotations

import hashlib
import hmac
import os
from typing import Optional


def sign_hmac_sha256(payload: bytes, *, secret_env: str = "WEBHOOK_SECRET") -> str:
    secret = os.getenv(secret_env, "dev-secret").encode()
    signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return signature


def safe_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)




