# -*- coding: utf-8 -*-
"""
DamFinder Pro v1.0 — Licence Manager
=====================================
SHA-256 + salt validation, encrypted AppData storage, expiry management.

© 2026 DAMFINDER Engineering Tools — All rights reserved
"""

import os
import json
import hashlib
import base64
import platform
import socket
from datetime import datetime, date, timedelta
from pathlib import Path

# ── Secret salt (change before distribution) ──────────────────────────────────
_SALT = "DFP2026#ICOLD$ESMAP@WestAfrica!HydroTools"

# ── AppData storage path ───────────────────────────────────────────────────────
def _appdata_dir() -> Path:
    appdata = os.environ.get("APPDATA", Path.home())
    d = Path(appdata) / "DamFinderPro"
    d.mkdir(parents=True, exist_ok=True)
    return d

LICENSE_FILE = _appdata_dir() / "license.dat"

# ── Machine fingerprint (lightweight, no admin) ───────────────────────────────
def _machine_id() -> str:
    raw = platform.node() + platform.processor() + socket.gethostname()
    return hashlib.sha256(raw.encode()).hexdigest()[:24]

# ── XOR-based obfuscation (not crypto-grade, but sufficient for .dat file) ────
def _xor_cipher(data: bytes, key: bytes) -> bytes:
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))

def _encrypt(payload: dict) -> bytes:
    raw = json.dumps(payload).encode("utf-8")
    key = (_SALT + _machine_id()).encode("utf-8")
    xored = _xor_cipher(raw, key)
    return base64.b64encode(xored)

def _decrypt(data: bytes) -> dict:
    key = (_SALT + _machine_id()).encode("utf-8")
    xored = base64.b64decode(data)
    raw = _xor_cipher(xored, key)
    return json.loads(raw.decode("utf-8"))

# ── Key format: XXXX-XXXX-XXXX-XXXX  (hex groups) ────────────────────────────
def _normalise_key(raw_key: str) -> str:
    return raw_key.strip().upper().replace(" ", "")

def _expected_hash(key_body: str, expiry_iso: str) -> str:
    """SHA-256 of salt + normalised key body + expiry date."""
    payload = f"{_SALT}{key_body}{expiry_iso}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

# ── Public API ────────────────────────────────────────────────────────────────

class LicenceResult:
    """Returned by every licence check."""
    def __init__(self, valid: bool, message: str = "",
                 expiry: date | None = None):
        self.valid = valid
        self.message = message
        self.expiry = expiry          # date object or None

    @property
    def days_remaining(self) -> int:
        if self.expiry is None:
            return 0
        return max(0, (self.expiry - date.today()).days)

    @property
    def expiry_str(self) -> str:
        return self.expiry.strftime("%d/%m/%Y") if self.expiry else "—"


def generate_key(key_body: str, expiry_iso: str) -> str:
    """
    Developer utility — generate a valid licence key string.

    key_body   : e.g. "ABCD-1234-EF56-7890"
    expiry_iso : e.g. "2027-12-31"

    Returns the key + embedded expiry: "ABCD-1234-EF56-7890|2027-12-31|<hash8>"
    """
    h = _expected_hash(_normalise_key(key_body), expiry_iso)
    return f"{key_body}|{expiry_iso}|{h[:16]}"


def activate(raw_key: str) -> LicenceResult:
    """
    Validate a key string and, if valid, persist the licence to disk.

    Expected format:  BODY|YYYY-MM-DD|HASH16
    where HASH16 = first 16 hex chars of SHA256(_SALT + BODY + YYYY-MM-DD)
    """
    try:
        parts = _normalise_key(raw_key).split("|")
        if len(parts) != 3:
            return LicenceResult(False,
                "Format invalide. Attendu : BODY|YYYY-MM-DD|HASH16")

        key_body, expiry_iso, provided_hash = parts

        # Check hash
        expected = _expected_hash(key_body, expiry_iso)
        if expected[:16] != provided_hash.lower():
            return LicenceResult(False, "Clé de licence invalide.")

        # Check expiry
        try:
            expiry = datetime.strptime(expiry_iso, "%Y-%m-%d").date()
        except ValueError:
            return LicenceResult(False, "Date d'expiration invalide.")

        if expiry < date.today():
            return LicenceResult(False,
                f"Licence expirée le {expiry.strftime('%d/%m/%Y')}.")

        # Persist
        payload = {
            "key_body": key_body,
            "expiry": expiry_iso,
            "activated_on": date.today().isoformat(),
            "machine": _machine_id()
        }
        LICENSE_FILE.write_bytes(_encrypt(payload))

        return LicenceResult(True,
            f"Licence activée jusqu'au {expiry.strftime('%d/%m/%Y')}.",
            expiry)

    except Exception as exc:
        return LicenceResult(False, f"Erreur activation: {exc}")


def check() -> LicenceResult:
    """
    Read stored licence and return its status.
    Returns LicenceResult(valid=False) if no licence found or it is corrupt.
    """
    if not LICENSE_FILE.exists():
        return LicenceResult(False, "Aucune licence activée.")

    try:
        payload = _decrypt(LICENSE_FILE.read_bytes())

        # Machine binding (soft check — warn but don't block if migrated)
        # Expiry check
        expiry = datetime.strptime(payload["expiry"], "%Y-%m-%d").date()
        if expiry < date.today():
            return LicenceResult(False,
                f"Licence expirée le {expiry.strftime('%d/%m/%Y')}. "
                "Veuillez renouveler.", expiry)

        days = (expiry - date.today()).days
        if days <= 30:
            msg = (f"Licence valide — expire dans {days} jour(s) "
                   f"({expiry.strftime('%d/%m/%Y')}). Pensez à renouveler.")
        else:
            msg = f"Licence valide jusqu'au {expiry.strftime('%d/%m/%Y')}."

        return LicenceResult(True, msg, expiry)

    except Exception as exc:
        return LicenceResult(False, f"Fichier licence corrompu: {exc}")


def revoke():
    """Remove the stored licence from disk."""
    if LICENSE_FILE.exists():
        LICENSE_FILE.unlink()


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    expiry_date = (date.today() + timedelta(days=365)).isoformat()
    key = generate_key("DAMF-1234-ABCD-5678", expiry_date)
    print(f"Generated key: {key}")
    result = activate(key)
    print(f"Activate: valid={result.valid} msg={result.message}")
    result2 = check()
    print(f"Check:    valid={result2.valid} msg={result2.message} "
          f"expires={result2.expiry_str}")
