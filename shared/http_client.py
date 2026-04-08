"""HTTP session and proxy factory helpers for all collectors.

Provides convenience functions for building proxy dictionaries compatible with
``curl_cffi`` (datacenter and residential) and Camoufox, as well as a factory
for creating authenticated ``AsyncSession`` objects with browser impersonation.
"""
import random
from curl_cffi.requests import AsyncSession
from . import config


def _session_token() -> str:
    """Generate a random session token string for sticky-session proxies.

    Returns:
        A string representation of a random float, used as a unique session
        identifier in proxy usernames.
    """
    return str(random.random())


def make_dc_proxy(sticky: bool = False, slot: int | None = None) -> dict:
    """Build a datacenter proxy dict for Jacob and IT Market collectors.

    Uses port 22225 on the configured superproxy host. When ``sticky`` is
    True, a session identifier is appended to the username so that all
    requests in the session share the same exit node.

    Args:
        sticky: If True, add a session tag to the proxy username to pin
            requests to the same datacenter exit node.
        slot: Optional fixed slot number for the sticky session. When
            provided alongside ``sticky=True``, uses a deterministic
            ``slot<N>`` label instead of a random token.

    Returns:
        A dict with ``"http"`` and ``"https"`` keys containing the fully
        qualified proxy URL for use with ``requests``-compatible clients.
    """
    user = config.PROXY_USER
    if sticky and slot is not None:
        user = f"{user}-session-slot{slot}"
    elif sticky:
        user = f"{user}-session-{_session_token()}"
    return {
        "http": f"http://{user}:{config.PROXY_PASS}@{config.PROXY_HOST}:{config.PROXY_PORT_DC}",
        "https": f"http://{user}:{config.PROXY_PASS}@{config.PROXY_HOST}:{config.PROXY_PORT_DC}",
    }


def make_residential_proxy(sticky: bool = True) -> dict:
    """Build a residential proxy dict for IT Resell and Tonitrus collectors.

    Uses port 33335 on the configured superproxy host. Sticky sessions are
    enabled by default so that multi-page scrapes share the same IP.

    Args:
        sticky: If True (default), append a random session token to the
            proxy username to pin requests to the same residential exit node.

    Returns:
        A dict with ``"http"`` and ``"https"`` keys containing the fully
        qualified proxy URL for use with ``requests``-compatible clients.
    """
    user = config.PROXY_USER
    if sticky:
        user = f"{user}-session-{_session_token()}"
    return {
        "http": f"http://{user}:{config.PROXY_PASS}@{config.PROXY_HOST}:{config.PROXY_PORT_RESIDENTIAL}",
        "https": f"http://{user}:{config.PROXY_PASS}@{config.PROXY_HOST}:{config.PROXY_PORT_RESIDENTIAL}",
    }


def camoufox_proxy(sticky: bool = True) -> dict:
    """Build a Camoufox-compatible proxy configuration dict for Tonitrus.

    Returns a dict in the format expected by the Camoufox browser automation
    library, which differs from the standard ``requests`` proxy format.

    Args:
        sticky: If True (default), append a random session token to the
            proxy username to maintain the same residential exit node across
            requests within a session.

    Returns:
        A dict with keys ``"server"``, ``"username"``, ``"password"``, and
        ``"bypass"`` as required by the Camoufox proxy configuration schema.
    """
    user = config.PROXY_USER
    if sticky:
        user = f"{user}-session-{_session_token()}"
    return {
        "server": f"http://{config.PROXY_HOST}:{config.PROXY_PORT_RESIDENTIAL}",
        "username": user,
        "password": config.PROXY_PASS,
        "bypass": [],
    }


def make_curl_session(proxy: dict, impersonate: str = "chrome124") -> AsyncSession:
    """Create a curl_cffi AsyncSession with proxy and browser impersonation.

    Args:
        proxy: Proxy dict with ``"http"`` and ``"https"`` keys as returned by
            :func:`make_dc_proxy` or :func:`make_residential_proxy`.
        impersonate: Browser fingerprint string passed to ``curl_cffi``.
            Defaults to ``"chrome124"``.

    Returns:
        A configured :class:`curl_cffi.requests.AsyncSession` instance ready
        for use in async HTTP scraping contexts.
    """
    return AsyncSession(impersonate=impersonate, proxies=proxy)
