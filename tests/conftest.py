import pytest
from cto_cli.ecs.local import settings


@pytest.fixture
def mocked_validate_current_dir(mocker):
    from cto_cli.ecs.local import settings

    mocker.patch.object(settings, 'validate_workdir_in_ecs_repo_path', side_effect=lambda f: f)

    yield


@pytest.fixture
def files_handler():
    from cto_cli.ecs.local import files

    yield files


@pytest.fixture
def mocked_settings(mocker):
    mocker.patch.object(settings, 'load_ecs_settings').return_value = settings.ECSSettings(
        url='http://localhost:1234', ecs_path='/tmp', token='test_token'
    )


@pytest.fixture
def mocked_compatibility_check(mocked_settings, mocker):
    from cto_cli.ecs.local import validators

    mocker.patch.object(validators, 'check_versions_compatibility', new=lambda: None)

    yield


@pytest.fixture
def operations(mocked_settings):
    from cto_cli.ecs.local import operations

    yield operations


@pytest.fixture
def app(mocked_compatibility_check, mocked_validate_current_dir):
    from cto_cli.main import app

    yield app
