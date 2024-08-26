"""Global logging infrastructure for BigDBM."""
from contextlib import contextmanager


try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False


class LoggingManager:
    """Manages the global logging configuration for BigDBM."""

    def __init__(self):
        self.logging_enabled = LOGFIRE_AVAILABLE
        self.logger = logfire if LOGFIRE_AVAILABLE else None

    def enable_logging(self):
        """Enable logging if Logfire is available."""
        self.logging_enabled = LOGFIRE_AVAILABLE

    def disable_logging(self):
        """Disable logging."""
        self.logging_enabled = False

    def log(self, level: str, message: str, **kwargs):
        """Log a message if logging is enabled."""
        if self.logging_enabled and self.logger:
            self.logger.log(level, message, **kwargs)

    @contextmanager
    def log_span(self, name: str, **kwargs):
        """Create a logging span if logging is enabled."""
        if self.logging_enabled and self.logger:
            with self.logger.span(name, **kwargs):
                yield
        else:
            yield


# Global instance of LoggingManager
logging_manager = LoggingManager()


def log(level: str, message: str, **kwargs):
    """Global function to log a message."""
    logging_manager.log(level, message, **kwargs)


@contextmanager
def log_span(name: str, **kwargs):
    """Global function to create a logging span."""
    with logging_manager.log_span(name, **kwargs):
        yield


def enable_logging():
    """Enable global logging."""
    logging_manager.enable_logging()


def disable_logging():
    """Disable global logging."""
    logging_manager.disable_logging()
    