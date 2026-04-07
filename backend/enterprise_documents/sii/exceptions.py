class SIIClientError(Exception):
    pass


class SIIConfigurationError(SIIClientError):
    pass


class SIIAuthError(SIIClientError):
    pass
