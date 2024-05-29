import sys

if sys.version_info < (3, 11):
    from typing_extensions import Annotated
else:
    from typing import Annotated
import typer
from rich import print

from cto_cli.ecs.api.connector import APIConnector
from cto_cli.ecs.local.files import FilesHandler, HashTypeUpdate
from cto_cli.ecs.local.operations import (
    handle_config_update,
    is_repo_update_needed,
    handle_config_push,
    show_modified_local_files,
    update_server_modified_files,
)
from cto_cli.ecs.local.settings import (
    validate_workdir_in_ecs_repo_path,
    get_ecs_path,
)
from cto_cli.ecs.local.validators import check_versions_compatibility
from cto_cli.utils.errors import print_error
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(callback=check_versions_compatibility)


def pull_remote_repo(
    api_connector: APIConnector, show_status: bool = True, update_type: HashTypeUpdate = HashTypeUpdate.CURRENT
) -> None:
    repo_path = get_ecs_path() / 'repo.zip'
    repo_hashes = api_connector.get_config_hashes()

    if is_repo_update_needed(repo_hashes):
        api_connector.get_raw_content(repo_path)
        handle_config_update(repo_path)
        FilesHandler.update_remote_hashes(repo_hashes, update_type)
        if show_status:
            print('[green]Config has been updated[/green]')
    else:
        if show_status:
            print('[green]Config is already up-to-date[/green]')


@app.command(name='pull')
@validate_workdir_in_ecs_repo_path
def pull() -> None:
    pull_remote_repo(APIConnector())


@app.command(name='push')
@validate_workdir_in_ecs_repo_path
def push(tag: Annotated[str, typer.Option()] = None) -> None:
    api_connector = APIConnector()

    repo_hashes = api_connector.get_config_hashes()
    if is_repo_update_needed(repo_hashes):
        print_error('[red]Repo is not up-to-date, run [b]cto ecs config pull[/b] to update[/red]', exit=True)

    server_modified_files = handle_config_push(api_connector, tag)
    pull_remote_repo(api_connector, show_status=False, update_type=HashTypeUpdate.BOTH)
    if server_modified_files:
        update_server_modified_files(server_modified_files)


def validate_strategy_name(value: str):
    if value is None or len(value) < 2:
        raise typer.BadParameter('strategy-name must have at least 2 characters')
    return value


@app.command(name='build')
def build(
    path: Annotated[str, typer.Option()],
    strategy_name: Annotated[str, typer.Option()] = None,
    format: Annotated[str, typer.Option()] = None,
    filter: Annotated[str, typer.Option(help='filter result using JMESPath')] = None,
    config_id: Annotated[str, typer.Option()] = None,
    detect_drift: bool = False,
    recursive: bool = False,
    show_secrets: bool = False,
) -> None:
    if strategy_name:
        validate_strategy_name(strategy_name)

    APIConnector().build_config(
        path=path,
        strategy_name=strategy_name,
        format=format,
        filter=filter,
        recursive=recursive,
        show_secrets=show_secrets,
        config_id=config_id,
        detect_drift=detect_drift,
    )


@app.command(name='decrypt')
def decrypt(path: Annotated[str, typer.Option()]) -> None:
    APIConnector().decrypt_file(path)


@app.command(name='generate-schema')
def generate_schema(
    path: Annotated[str, typer.Option()], strategy_name: Annotated[str, typer.Option()], write: bool = False
) -> None:
    with Progress(
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
        transient=True,
    ) as progress:
        progress.add_task(description='AI is generating schema for you...', total=None)
        APIConnector().generate_schema(path=path, strategy_name=strategy_name, write=write)


@app.command(name='status')
@validate_workdir_in_ecs_repo_path
def status() -> None:
    modified_files = FilesHandler().modified_files

    if not modified_files.has_changes():
        print('[green]No modified files[/green]')
    else:
        show_modified_local_files(modified_files)
