from typer.testing import CliRunner
from importlib.metadata import version as metadata_version

runner = CliRunner()


def test_version(app):
    result = runner.invoke(app, '--version')
    assert result.exit_code == 0
    assert result.stdout.strip() == metadata_version('cto-cli')
