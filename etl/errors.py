"""Pipeline failures that callers should treat as data-contract breaks."""


class DataQualityError(RuntimeError):
    """Raised when a publish gate finds rows that violate the core contract."""
