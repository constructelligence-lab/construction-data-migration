"""Schedule readers (Primavera P6 XER, Microsoft Project XML) and a conversion check."""

from .model import Activity, Relationship, Schedule
from .mspdi import read_mspdi
from .xer import read_xer


def read_schedule(path):
    """Read a schedule file, choosing the reader from the extension."""
    suffix = str(path).lower().rsplit(".", 1)[-1]
    if suffix == "xer":
        return read_xer(path)
    if suffix == "xml":
        return read_mspdi(path)
    raise ValueError(f"unsupported schedule file {path}: expected .xer or .xml (Microsoft Project XML)")


__all__ = ["Activity", "Relationship", "Schedule", "read_mspdi", "read_schedule", "read_xer"]
