class EOCanvasError(Exception):
    """Base class for EO Canvas exceptions."""


class CredentialsError(EOCanvasError):
    """Generic error regarding the credentials."""


class MalformedCredentialsError(CredentialsError):
    """Malformed credentials error."""


class CorruptedCredentialsError(CredentialsError):
    """Credentials file is bad YAML."""


class CredentialsNotFoundError(CredentialsError):
    """Missing credentials file."""


class HTTPError(EOCanvasError):
    """Exception on low level HTTP errors."""


class QuotaExceededError(EOCanvasError):
    """Exception on user quota exceeded."""


class MalformedSnapError(EOCanvasError):
    """Exception on malformed SNAP operators file."""


class SnapOperatorNotFound(EOCanvasError):
    """Exception on non-existent SNAP operator."""


class JobFailed(EOCanvasError):
    """Exception on a job that returns failed status."""


class InvalidChainError(EOCanvasError):
    """Exception on invalid YAML file for a DataTailor Chain."""
