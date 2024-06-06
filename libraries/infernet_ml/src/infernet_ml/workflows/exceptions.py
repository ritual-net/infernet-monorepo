class RetryableException(Exception):
    """Marker exception that should be thrown when it can be retried"""

    pass


class ServiceException(Exception):
    """Marker exception for service specific exceptions that should
    be thrown. Use RetryableException if the exception can be retried
    """

    pass


class InfernetMLException(Exception):
    """Base exception for all infernet_ml exceptions"""

    pass


class APIKeyMissingException(InfernetMLException):
    """Exception for when an API key is missing"""

    pass
