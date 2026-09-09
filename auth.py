"""Authentication helpers for the Secure Code Scanner demo application.

The scanner service is protected by a single API key. Callers must present
that key before they are allowed to scan anything.
"""

import hmac

# ---------------------------------------------------------------------------
# KAN-5: DELIBERATE VULNERABILITY - hardcoded credential.
#
# This key is committed on purpose so that the Gitleaks job in
# .github/workflows/security.yml fails during the classroom demonstration
# (KAN-11). The value is a random placeholder string. It is not a real
# credential, it belongs to no service, and it grants access to nothing.
#
# KAN-12 replaces this line with an environment variable lookup.
# ---------------------------------------------------------------------------
SCANNER_API_KEY = "9Xq2LmT4pR7vZa1KcYb3Nd6HsJf0Wg8E"


def get_api_key():
    """Return the API key the scanner expects callers to present.

    Looked up on every call so that tests can replace it easily.
    """
    return SCANNER_API_KEY


def is_authorised(api_key):
    """Return True when ``api_key`` matches the configured key."""
    expected = get_api_key()
    if not expected or not api_key:
        return False
    # Constant-time comparison, so the check does not leak the key
    # one character at a time through its response time.
    return hmac.compare_digest(api_key, expected)
