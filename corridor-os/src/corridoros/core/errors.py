"""Errors that every module raises, so a caller never has to catch four different
exception hierarchies to find out that a thing was not allowed."""

from __future__ import annotations


class CorridorError(Exception):
    """Base class for every refusal this platform makes on purpose."""


class IdError(CorridorError):
    """An identifier is malformed, or belongs to the wrong kind of object."""


class AuthorityError(CorridorError):
    """An actor attempted something its role may not do.

    This is the error that carries the AI boundary. It is raised *before* any
    state changes, so a refused action leaves nothing half-applied behind.
    """


class EventError(CorridorError):
    """An event cannot be accepted: unknown type, replayed, or out of order."""


class LedgerError(CorridorError):
    """A posting would break double-entry, or edit history that is immutable."""


class LifecycleError(CorridorError):
    """A state transition that the machine does not define."""


class FxError(CorridorError):
    """A quote is expired, unknown, or being executed at a rate it did not quote."""


class EvidenceError(CorridorError):
    """A citation does not resolve, or a packet is missing what it claims to hold."""
