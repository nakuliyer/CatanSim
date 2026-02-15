# Static global verbosity
verbosity = -1

# Static global verbosity levels
GAME = 0
DEBUG = 1

# Static global message log
messages: list[str] = []


def log(message, level=DEBUG) -> None:
    """Log a message with a given verbosity level."""

    def level_to_prefix(level):
        if level == GAME:
            return "[GAME] "
        elif level == DEBUG:
            return "[DEBUG] "

    if level <= verbosity:
        messages.append(f"{level_to_prefix(level)}{message}")


def print_all() -> None:
    """Print all logged messages without clearing the log."""
    if not messages:
        return
    output = "\n".join(messages)
    print(output)


def flush():
    """Clear the log."""
    global messages
    messages = []


def set_verbosity(level):
    """Set the global verbosity level."""
    global verbosity
    verbosity = level


def game(message):
    """Log a game message."""
    log(message, GAME)


def debug(message):
    """Log a debug message."""
    log(message, DEBUG)
