import typer
from rich import print

from cto_cli.ecs import main
from cto_cli.ecs.local.validators import get_current_cli_version

app = typer.Typer(help='CTO CLI')
app.add_typer(main.app, name='ecs')


def main() -> None:
    app(prog_name='cto')


def version_callback(value: bool) -> None:
    if value:
        print(get_current_cli_version())
        raise typer.Exit()


@app.callback()
def version(
    version: bool = typer.Option(
        None,
        '--version',
        '-v',
        callback=version_callback,
        is_eager=True,
        help='Print the version and exit',
    ),
):
    return


if __name__ == '__main__':
    main()
