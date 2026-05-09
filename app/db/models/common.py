import enum

__all__ = ["Currency"]


class Currency(str, enum.Enum):
    USD = "USD"
    GEL = "GEL"
