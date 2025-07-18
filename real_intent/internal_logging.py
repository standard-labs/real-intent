"""Global logging infrastructure."""
from contextlib import contextmanager


try:
    import logfire
    from logfire._internal.config import GLOBAL_CONFIG, ConsoleOptions
    LOGFIRE_AVAILABLE = True
except ImportError:
    logfire = None
    LOGFIRE_AVAILABLE = False


class DummyLogger:
    """A dummy logger that does nothing."""
    def log(self, *args, **kwargs):
        pass

    @contextmanager
    def span(self, *args, **kwargs):
        yield


# Global logger object
logger = logfire if LOGFIRE_AVAILABLE else DummyLogger()


def enable_logging():
    """Enable global logging."""
    if LOGFIRE_AVAILABLE:
        GLOBAL_CONFIG.console = ConsoleOptions()


def disable_logging():
    """Disable global logging."""
    if LOGFIRE_AVAILABLE:
        GLOBAL_CONFIG.console = False


# ---- Instrumentations ----

def instrument_openai(openai_client=None):
    """Instrument the OpenAI client.

    Raises:
        ImportError: If the OpenAI package is not installed.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Please install this package with the 'ai' extra.")

    if openai_client is not None and not isinstance(openai_client, OpenAI):
        raise ValueError("OpenAI client must be an instance of OpenAI.")

    if LOGFIRE_AVAILABLE:
        logfire.instrument_openai(openai_client)


# Expose log and log_span methods directly
log = logger.log
log_span = logger.span
