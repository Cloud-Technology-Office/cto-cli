from enum import Enum
from typing import Annotated

import typer
from rich.prompt import Confirm

from cto_cli.ecs.api.connector import APIConnector
from cto_cli.ecs.local.settings import get_current_working_dir_relative_path_to_ecs_repo
from cto_cli.ecs.local.validators import check_versions_compatibility

app = typer.Typer(callback=check_versions_compatibility)


@app.command(name='list')
def list_users() -> None:
    APIConnector().list_users()


@app.command(name='create')
def create(
    username: Annotated[str, typer.Option()],
    given_name: Annotated[str, typer.Option()],
    family_name: Annotated[str, typer.Option()],
    admin: bool = False,
    read_secrets: bool = False,
    edit_strategies: bool = False,
):
    APIConnector().create_user(
        username=username,
        given_name=given_name,
        family_name=family_name,
        admin=admin,
        read_secrets=read_secrets,
        edit_strategies=edit_strategies,
    )


class UserAuthOptions(Enum):
    add = 'add'
    delete = 'delete'
    list = 'list'


@app.command(name='auth')
def auth(username: Annotated[str, typer.Option()], action: Annotated[UserAuthOptions, typer.Option()]) -> None:
    api_connector = APIConnector()

    match action:
        case UserAuthOptions.add:
            current_path = get_current_working_dir_relative_path_to_ecs_repo()
            if Confirm.ask(
                f'Are you sure you want to add [b]{current_path}[/b] as allowed path for user: [b]{username}[/b]'
            ):
                api_connector.add_auth(username, current_path)

        case UserAuthOptions.list:
            api_connector.list_auth(username)

        case UserAuthOptions.delete:
            current_path = get_current_working_dir_relative_path_to_ecs_repo()
            if Confirm.ask(
                f'Are you sure you want to delete allowed path: [b]{current_path}[/b] for user: [b]{username}[/b]'
            ):
                api_connector.delete_auth(username, current_path)
