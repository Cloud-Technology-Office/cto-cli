import sys
from enum import Enum

if sys.version_info < (3, 11):
    from typing_extensions import Annotated
    from typing import Optional
else:
    from typing import Annotated, Optional

import typer
from rich.prompt import Confirm

from cto_cli.ecs.api.connector import APIConnector
from cto_cli.ecs.local.settings import get_current_working_dir_relative_path_to_ecs_repo
from cto_cli.ecs.local.validators import check_versions_compatibility

app = typer.Typer(callback=check_versions_compatibility)


@app.command(name='list')
def list_users() -> None:
    APIConnector().list_users()


@app.command(name='regenerate-token')
def regenerate_token(username: Annotated[str, typer.Option()]):
    APIConnector().regenerate_user_token(username)


@app.command(name='create')
def create(
    username: Annotated[str, typer.Option()],
    given_name: Annotated[str, typer.Option()],
    family_name: Annotated[str, typer.Option()],
    email: Annotated[str, typer.Option()],
    admin: bool = False,
    read_secrets: bool = False,
    edit_strategies: bool = False,
    edit_webhooks: bool = False,
):
    APIConnector().create_user(
        username=username,
        given_name=given_name,
        family_name=family_name,
        email=email,
        admin=admin,
        read_secrets=read_secrets,
        edit_strategies=edit_strategies,
        edit_webhooks=edit_webhooks,
    )


@app.command(name='delete')
def delete(username: Annotated[str, typer.Option()]):
    APIConnector().delete_user(
        username=username,
    )


@app.command(name='edit')
def edit(
    username: Annotated[str, typer.Option()],
    given_name: Annotated[str, typer.Option()] = None,
    family_name: Annotated[str, typer.Option()] = None,
    email: Annotated[str, typer.Option()] = None,
    admin: Annotated[Optional[bool], typer.Option('--admin/--no-admin')] = None,
    read_secrets: Annotated[Optional[bool], typer.Option('--read-secrets/--no-read-secrets')] = None,
    edit_strategies: Annotated[Optional[bool], typer.Option('--edit-strategies/--no-edit-strategies')] = None,
    edit_webhooks: Annotated[Optional[bool], typer.Option('--edit-webhooks/--no-edit-webhooks')] = None,
):
    APIConnector().edit_user(
        username=username,
        given_name=given_name,
        family_name=family_name,
        email=email,
        admin=admin,
        read_secrets=read_secrets,
        edit_strategies=edit_strategies,
        edit_webhooks=edit_webhooks,
    )


class UserAuthOptions(Enum):
    add = 'add'
    delete = 'delete'
    list = 'list'


@app.command(name='auth')
def auth(username: Annotated[str, typer.Option()], action: Annotated[UserAuthOptions, typer.Option()]) -> None:
    api_connector = APIConnector()

    if action is UserAuthOptions.add:
        current_path = get_current_working_dir_relative_path_to_ecs_repo()
        if Confirm.ask(
            f'Are you sure you want to add [b]{current_path}[/b] as allowed path for user: [b]{username}[/b]'
        ):
            api_connector.add_auth(username, current_path)

    elif action is UserAuthOptions.list:
        api_connector.list_auth(username)

    elif action is UserAuthOptions.delete:
        current_path = get_current_working_dir_relative_path_to_ecs_repo()
        if Confirm.ask(
            f'Are you sure you want to delete allowed path: [b]{current_path}[/b] for user: [b]{username}[/b]'
        ):
            api_connector.delete_auth(username, current_path)
