import sys
from rich.console import Console

err_console = Console(stderr=True)


def print_error(message: str, exit: bool = False):
    err_console.print(f'[red]{message}[/red]')
    if exit:
        sys.exit(1)
