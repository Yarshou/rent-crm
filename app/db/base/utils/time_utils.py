from datetime import UTC, datetime, tzinfo

__all__ = ["now"]


def now(tz: tzinfo = None) -> datetime:
    if tz is None:
        tz = UTC
    return datetime.now(tz=tz)
