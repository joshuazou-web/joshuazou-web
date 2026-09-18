"""Identifiers.

Four projects were merged into this one, and each had its own idea of what an
identifier looked like: `TXN-0012`, `wlt_889`, `SEC-SPY-497-2026:para1-20:c1`,
`input_id`. Having merged them, the cheapest way to stop them drifting apart
again is to make a malformed identifier impossible to construct rather than
merely discouraged in a document.

Every identifier here is `<prefix>_<body><check>`:

  * the **prefix** says what kind of object it is, so `beneficiary_id="biz_..."`
    fails at the boundary instead of three modules later;
  * the **body** is the caller's own slug, which keeps synthetic data readable
    (`biz_sz001` is the Shenzhen entity, and stays that in every screenshot);
  * the **check** character is derived from prefix and body, so an identifier
    that was typed by hand, truncated in a URL, or invented by a language model
    does not validate.

That last point is the load-bearing one. The copilot may cite `evidence_id`s;
the citation gate resolves them against the packet, and a fabricated identifier
does not even get as far as the lookup.
"""

from __future__ import annotations

import hashlib
import re

from .errors import IdError

# Kind -> prefix. The six identifiers the platform standardises on come first;
# the rest are internal objects that still deserve typed identifiers.
PREFIXES: dict[str, str] = {
    "business": "biz",
    "payment": "pay",
    "beneficiary": "ben",
    "case": "case",
    "evidence": "ev",
    "decision": "dec",
    # supporting objects
    "intent": "col",
    "ledger_entry": "led",
    "quote": "fxq",
    "assessment": "ra",
    "settlement": "stl",
    "exception": "exc",
    "event": "evt",
    "audit": "aud",
}

_BY_PREFIX: dict[str, str] = {prefix: kind for kind, prefix in PREFIXES.items()}

_BODY_RE = re.compile(r"^[a-z0-9]{3,32}$")
_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def _check_char(prefix: str, body: str) -> str:
    digest = hashlib.sha256(f"{prefix}:{body}".encode()).digest()
    return _ALPHABET[digest[0] % len(_ALPHABET)]


def make_id(kind: str, body: str) -> str:
    """Build a checked identifier of `kind` from a readable `body` slug."""
    if kind not in PREFIXES:
        raise IdError(f"unknown object kind {kind!r}; known kinds: {sorted(PREFIXES)}")
    slug = (body or "").strip().lower().replace("-", "").replace("_", "")
    if not _BODY_RE.match(slug):
        raise IdError(
            f"{body!r} is not a usable identifier body; use 3-32 characters of a-z0-9"
        )
    prefix = PREFIXES[kind]
    return f"{prefix}_{slug}{_check_char(prefix, slug)}"


def kind_of(identifier: str) -> str:
    """The object kind an identifier belongs to, validating it on the way."""
    validate(identifier)
    return _BY_PREFIX[identifier.split("_", 1)[0]]


def is_valid(identifier: object, kind: str | None = None) -> bool:
    try:
        validate(identifier, kind)
    except IdError:
        return False
    return True


def validate(identifier: object, kind: str | None = None) -> str:
    """Return `identifier` unchanged, or raise `IdError` explaining the problem."""
    if not isinstance(identifier, str) or "_" not in identifier:
        raise IdError(f"{identifier!r} is not an identifier of the form <prefix>_<body>")
    prefix, remainder = identifier.split("_", 1)
    if prefix not in _BY_PREFIX:
        raise IdError(f"{identifier!r} carries unknown prefix {prefix!r}")
    if kind is not None:
        if kind not in PREFIXES:
            raise IdError(f"unknown object kind {kind!r}")
        if PREFIXES[kind] != prefix:
            raise IdError(
                f"{identifier!r} is a {_BY_PREFIX[prefix]} identifier, "
                f"but a {kind} identifier was required"
            )
    body, check = remainder[:-1], remainder[-1:]
    if not _BODY_RE.match(body) or check != _check_char(prefix, body):
        raise IdError(
            f"{identifier!r} does not check out; it was mistyped, truncated or invented"
        )
    return identifier


class IdFactory:
    """Deterministic identifier sequence for the synthetic scenario.

    Seeded data has to reproduce exactly, or an evaluation number cannot be
    recomputed. A counter per kind gives stable identifiers without a random
    source, so the same seed produces the same `pay_...` in every run.
    """

    def __init__(self, namespace: str = "cos") -> None:
        self.namespace = namespace
        self._counters: dict[str, int] = {}

    def next(self, kind: str) -> str:
        count = self._counters.get(kind, 0) + 1
        self._counters[kind] = count
        return make_id(kind, f"{self.namespace}{count:05d}")
