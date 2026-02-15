# Static global verbosity
verbosity = -1

# Static global verbosity levels
GAME = 0
DEBUG = 1


class Message:
    def __init__(self, message: str, level: int):
        self.message = message
        self.level = level


# Static global message log
messages = []


def log(message, level=DEBUG) -> None:
    """Log a message with a given verbosity level."""
    if level <= verbosity:
        messages.append(Message(message, level))


def print_all() -> None:
    """Print all logged messages without clearing the log."""
    if not messages:
        return

    def level_to_prefix(level):
        if level == GAME:
            return "[GAME] "
        elif level == DEBUG:
            return "[DEBUG] "

    output = "\n".join(
        [f"{level_to_prefix(msg.level)}{msg.message}" for msg in messages]
    )
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
