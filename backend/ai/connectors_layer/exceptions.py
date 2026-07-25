"""
exceptions.py — shared connector exception hierarchy.

Lives in its own module (not inside marketplace_connector.py) so that
individual connector implementations (connectors/meesho_connector.py,
connectors/amazon_connector.py, ...) can raise these without importing
marketplace_connector.py itself, which would create a circular import
(marketplace_connector.py imports the connectors to build its registries).
"""


class ConnectorError(Exception):
    """Base exception for all marketplace connector errors."""
    pass


class AuthenticationError(ConnectorError):
    """Raised when authentication fails with the marketplace."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when provided marketplace credentials or tokens are invalid/expired."""
    pass


class RateLimitError(ConnectorError):
    """Raised when marketplace API rate limits are exceeded."""
    pass


class MarketplaceUnavailableError(ConnectorError):
    """Raised when the target marketplace service is down or unreachable."""
    pass
