class CineRocketError(Exception):
    pass


class ConfigurationError(CineRocketError):
    pass


class DatabaseNotFoundError(CineRocketError):
    pass


class UnsafeQueryError(CineRocketError):
    pass


class QueryExecutionError(CineRocketError):
    pass


class QueryTimeoutError(QueryExecutionError):
    pass


class InvalidQuestionError(CineRocketError):
    pass


class SemanticIndexUnavailableError(CineRocketError):
    pass


class LLMUnavailableError(CineRocketError):
    pass


class AgentFailureError(CineRocketError):
    pass


class SessionNotFoundError(CineRocketError):
    pass
