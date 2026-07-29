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


class SessionExpiredError(AuthenticationError):
    """
    Raised when a previously-valid session (cookies/tokens) is no longer
    accepted by the marketplace and a fresh login also failed or wasn't
    attempted — distinct from InvalidCredentialsError, which is a first
    login attempt failing outright. Callers can use this distinction to
    decide whether prompting "reconnect your account" (session expired)
    or "check your username/password" (invalid credentials) is the
    right message to show a seller.
    """
    pass


class RateLimitError(ConnectorError):
    """Raised when marketplace API rate limits are exceeded."""
    pass


class MarketplaceUnavailableError(ConnectorError):
    """Raised when the target marketplace service is down or unreachable."""
    pass


class NavigationError(ConnectorError):
    """
    Raised when a page navigation (goto / wait_for_url / wait_for_load_state)
    fails for transient reasons — timeout, DNS blip, temporary network
    error. Deliberately separate from SelectorError: a NavigationError
    means "we don't know what's on the page yet" and IS worth retrying;
    a SelectorError means "we loaded the page and the thing we expected
    on it isn't there," which a retry won't fix.
    """
    pass


class SelectorError(ConnectorError):
    """
    Raised when a page loaded successfully but an expected element
    (row, input, button) wasn't found on it — most likely because the
    real site's DOM/selectors don't match what a connector assumed.
    Not retryable: running the same selector again won't produce a
    different DOM.
    """
    pass


# Kept as an alias for existing call sites written against the older,
# less specific name — new code should prefer SelectorError/ParsingError.
ScrapingError = SelectorError


class ParsingError(ConnectorError):
    """
    Raised when a value was found on the page but couldn't be parsed
    into the expected type (e.g. a revenue string that isn't a number).
    Also not retryable — the page content, not the network, is the
    problem.
    """
    pass
