class BuilderContextError(Exception):
    """Base exception for MessageBuilder context errors."""

    pass


class ContextNotSetError(BuilderContextError):
    """Raised when a MessageBuilder is used before its context is set."""

    def __init__(self, builder_name: str):
        super().__init__(f"{builder_name}: context not set, call set_context() first")
