"""
AOP Wiki API Exceptions
=======================

Custom exceptions for the AOP Wiki API client.
"""


class AOPWikiError(Exception):
    """Base exception for AOP Wiki API errors."""
    pass


class AOPNotFoundError(AOPWikiError):
    """Exception raised when an AOP is not found."""
    pass


class APIConnectionError(AOPWikiError):
    """Exception raised when there's a connection error to the AOP Wiki API."""
    pass


class APITimeoutError(AOPWikiError):
    """Exception raised when the API request times out."""
    pass


class InvalidAPIResponseError(AOPWikiError):
    """Exception raised when the API response is invalid or malformed."""
    pass