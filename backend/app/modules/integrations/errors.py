from __future__ import annotations


class IntegrationError(Exception):
    """
    Base exception for external connector failures.
    """

    def __init__(self, *, provider: str, message: str, code: str = "integration_error") -> None:
        super().__init__(message)
        self.provider = provider
        self.message = message
        self.code = code


class IntegrationProviderError(IntegrationError):
    def __init__(self, *, provider: str, message: str, code: str = "provider_error") -> None:
        super().__init__(provider=provider, message=message, code=code)

