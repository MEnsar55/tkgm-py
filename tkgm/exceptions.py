"""TKGM API exception hierarchy."""


class TKGMError(Exception):
    """Base exception for all TKGM errors."""


class TKGMHTTPError(TKGMError):
    """Raised when the API returns a non-2xx status code."""

    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class TKGMNotFoundError(TKGMError):
    """Raised when the requested resource does not exist."""


class TKGMAuthError(TKGMError):
    """Raised when authentication is required but not provided."""


class TKGMRateLimitError(TKGMError):
    """Raised when the API rate limit is exceeded."""


class TKGMParseError(TKGMError):
    """Raised when an API response cannot be parsed."""
