from functools import lru_cache
from importlib.metadata import version as metadata_version
from subprocess import CalledProcessError

import typer

from cto_cli.ecs.api.connector import APIConnector
from cto_cli.ecs.local.commands import run_command
from cto_cli.utils.errors import print_error


def check_installed_tools() -> None:
    try:
        run_command('git --version', check=True)
    except CalledProcessError:
        print_error('Please install [b]git[/b][/red]', exit=True)

    try:
        run_command('sha256sum --version', check=True)
    except CalledProcessError:
        print_error('Please install [b]sha256sum[/b]', exit=True)


def get_current_cli_version() -> str:
    return metadata_version('cto-cli')


@lru_cache
def check_versions_compatibility() -> None:
    current_cli_version = get_current_cli_version()
    cli_major, cli_minor, cli_patch = current_cli_version.split('.')

    server_response = APIConnector().get_version_details()

    server_version = server_response['version']
    compatible_versions = server_response['compatibility']['cli_versions']

    version_compatible = False
    for compatible_version in compatible_versions:
        server_major, server_minor, server_patch = compatible_version.split('.')

        if server_major == cli_major:
            if server_minor == cli_minor or server_minor == '*':
                if server_patch == cli_patch or server_patch == '*':
                    version_compatible = True
            break

    if version_compatible is False:
        print_error(
            f'The current cli version: [red]{current_cli_version}[/red] is not compatible with the server '
            f'version: [red]{server_version}[/red]. Please use one of these cli versions: '
            f'[b]{compatible_versions}[/b]'
        )
        raise typer.Exit()
