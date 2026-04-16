"""TKGM API exception hierarchy."""
# TKGM API hata sınıfları hiyerarşisi.


class TKGMError(Exception):
    """Base exception for all TKGM errors."""
    # Tüm TKGM hatalarının temel sınıfı.


class TKGMHTTPError(TKGMError):
    """Raised when the API returns a non-2xx status code."""
    # API 2xx dışı bir HTTP durum kodu döndürdüğünde fırlatılır.

    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class TKGMNotFoundError(TKGMError):
    """Raised when the requested resource does not exist."""
    # İstenen kaynak (il, ilçe, mahalle, parsel) bulunamadığında fırlatılır.


class TKGMAuthError(TKGMError):
    """Raised when authentication is required but not provided."""
    # Kimlik doğrulama (e-Devlet token) gerekli fakat sağlanmadığında fırlatılır.


class TKGMRateLimitError(TKGMError):
    """Raised when the API rate limit is exceeded."""
    # API istek limiti aşıldığında (HTTP 429) fırlatılır.


class TKGMParseError(TKGMError):
    """Raised when an API response cannot be parsed."""
    # API yanıtı JSON olarak ayrıştırılamadığında fırlatılır.
