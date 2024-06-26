import typer
from rich import print

from cto_cli.ecs.api.connector import APIConnector, ApiTokenError, ApiConnectionError
from cto_cli.ecs.commands import users, config
from cto_cli.ecs.local.settings import (
    store_settings,
    load_ecs_settings,
    SettingsNotFound,
    check_working_dir_is_empty,
    create_repo_dir,
)
from cto_cli.ecs.local.validators import check_installed_tools, check_versions_compatibility
from cto_cli.utils.errors import print_error

app = typer.Typer(help='ECS CLI')
app.add_typer(users.app, name='users')
app.add_typer(config.app, name='config')


def create_admin_account(api_connector: APIConnector) -> str:
    print("This is the very first use of ECS, let's create the admin account")
    username = typer.prompt("What's your user name?")
    given_name = typer.prompt("What's your user given name?")
    family_name = typer.prompt("What's your user family name?")
    email = typer.prompt("What's your email?")
    response = api_connector.create_user(
        username=username, given_name=given_name, family_name=family_name, email=email, admin=True, return_as_dict=True
    )
    return response['token']


def ask_and_store_settings() -> None:
    try:
        settings = load_ecs_settings()
    except SettingsNotFound:
        settings = None

    saas_token = None

    saas = typer.confirm(
        "If you're using ECS Cloud type Y, if you're using your own on-prem ECS server, type N", abort=False
    )
    if saas:
        saas_token = typer.prompt(
            "What's your ECS Cloud token?", default=settings.saas_token if settings and settings.saas_token else None
        )
        api_url = 'https://api.enterpriseconfigurationservice.com'
        repo_name = typer.prompt(
            "What's your repo name you want to use?",
            default=settings.repo_name if settings and settings.repo_name else None,
        )
        api_connector = APIConnector(
            load_settings=False,
            url=api_url,
            headers={
                'Authorization': 'very_first_user',
                'x-saas-token': saas_token,
                **({'x-repo-name': repo_name} if repo_name else {}),
            },
        )
    else:
        api_url = typer.prompt("What's the API url?", default=settings.url if settings else None)

        while not (api_url.startswith('http://') or api_url.startswith('https://')):
            print_error("URL doesn't include the protocol")
            api_url = typer.prompt("What's the API url?", default=settings.url if settings else None)

        repo_name = typer.prompt(
            "What's your repo name you want to use?",
            default=settings.repo_name if settings and settings.repo_name else None,
        )

        api_connector = APIConnector(
            load_settings=False,
            url=api_url,
            headers={
                'Authorization': 'very_first_user',
                **({'x-repo-name': repo_name} if repo_name else {}),
            },
        )

    try:
        api_connector.check_api_connectivity()
    except ApiConnectionError as e:
        print_error(str(e))
        ask_and_store_settings()
    except ApiTokenError:
        # admin account already exist
        user_token = typer.prompt("What's your User token?", default=settings.token if settings else None)
        store_settings(api_url, user_token, saas_token)
    else:
        # create admin account
        user_token = create_admin_account(api_connector)
        store_settings(api_url, user_token, saas_token)


def store_and_validate_settings() -> None:
    ask_and_store_settings()
    try:
        APIConnector().check_api_connectivity()
    except ApiTokenError as e:
        print_error(str(e))
        store_and_validate_settings()


@app.command(name='init')
def init() -> None:
    check_installed_tools()
    reinit = False

    try:
        current_settings = load_ecs_settings()
    except SettingsNotFound:
        current_settings = None

    if current_settings:
        check_versions_compatibility()
        print(f'ECS has been already inited in path: [b]{current_settings.ecs_path}[/b]')
        reinit = typer.confirm('Do you want to re-init it?', abort=True)

    if reinit is True or current_settings is None:
        check_working_dir_is_empty()
        store_and_validate_settings()
        check_versions_compatibility()
        create_repo_dir()
        config.pull_remote_repo(APIConnector())
        print(
            '[green]Your credentials were saved and config has been downloaded, [b]cd repo[/b] to work with it['
            '/green]'
        )
