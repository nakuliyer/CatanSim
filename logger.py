# Static global verbosity
verbosity = -1

# Static global verbosity levels
SILENT = 0
ERROR = 1
INFO = 2
DEBUG = 3

messages = []


def log(message, level=INFO) -> None:
    """Log a message with a given verbosity level."""
    if level <= verbosity:
        messages.append(message)


def flush() -> list[str]:
    """Print all logged messages and clear the log."""
    global messages
    output = "\n".join(messages)
    messages = []
    return output


def set_verbosity(level):
    """Set the global verbosity level."""
    global verbosity
    verbosity = level


def silent(message):
    """Log a silent message."""
    log(message, SILENT)


def error(message):
    """Log an error message."""
    log(message, ERROR)


def info(message):
    """Log an info message."""
    log(message, INFO)


def debug(message):
    """Log a debug message."""
    log(message, DEBUG)
