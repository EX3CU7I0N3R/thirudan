class ThirudanError(Exception):
    pass


class AuthenticationError(ThirudanError):
    pass


class SessionExpiredError(AuthenticationError):
    pass


class ScraperResponseError(ThirudanError):
    pass


class ParseError(ThirudanError):
    pass


class ConfigurationError(ThirudanError):
    pass
