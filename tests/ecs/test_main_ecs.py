import pytest
from typer.testing import CliRunner
from cto_cli.ecs.local.settings import ECSSettings, SettingsNotFound

runner = CliRunner(mix_stderr=False)


@pytest.fixture
def main_ecs(mocked_validate_current_dir, mocked_settings):
    from cto_cli.ecs import main

    yield main


@pytest.mark.parametrize(
    'settings_exist,reinit',
    [
        (
            True,
            False,
        ),
        (
            True,
            True,
        ),
        (
            False,
            False,
        ),
    ],
)
def test_init(main_ecs, app, mocker, settings_exist, reinit):
    mocker.patch.object(main_ecs, 'check_installed_tools')
    mocker.patch.object(main_ecs, 'load_ecs_settings')

    mocker.patch.object(main_ecs, 'check_working_dir_is_empty')
    mocker.patch.object(main_ecs, 'store_and_validate_settings')
    mocker.patch.object(main_ecs, 'create_repo_dir')

    if settings_exist:
        main_ecs.load_ecs_settings.return_value = ECSSettings(
            url='test_url', token='test_token', ecs_path='ecs_local_path'
        )
    else:
        main_ecs.load_ecs_settings.side_effect = SettingsNotFound()

    if reinit:
        result = runner.invoke(app, ['ecs', 'init'], input='y')
    else:
        result = runner.invoke(app, ['ecs', 'init'], input='n')

    if reinit is False and settings_exist is True:
        assert (
            result.stdout == 'ECS has been already inited in path: ecs_local_path\n'
            'Do you want to re-init it? [y/N]: n\n'
        )
        assert result.exit_code == 1
        assert result.stderr.strip() in ('Aborted.', '\x1b[31mAborted.\x1b[0m')

    if settings_exist and reinit:
        assert result.exit_code == 0
        assert result.stdout.strip() == (
            'ECS has been already inited in path: ecs_local_path\n'
            'Do you want to re-init it? [y/N]: y\n'
            'Your credentials were saved, run cto ecs config pull to start'
        )
    elif settings_exist is False:
        assert result.stdout.strip() == 'Your credentials were saved, run cto ecs config pull to start'
