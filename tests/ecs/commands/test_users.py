import json
from pathlib import PosixPath

import pytest
import responses
from typer.testing import CliRunner

from constants import API_URL

runner = CliRunner(mix_stderr=False)


@pytest.fixture
def users(mocked_compatibility_check, mocked_validate_current_dir, mocked_settings):
    from cto_cli.ecs.commands import users

    yield users


@responses.activate
def test_user_create(app):
    server_response = {'token': 'test_token'}
    responses.add(responses.POST, f'{API_URL}/users', json=server_response, status=200)
    result = runner.invoke(
        app,
        [
            'ecs',
            'users',
            'create',
            '--username',
            'test',
            '--family-name',
            'family',
            '--given-name',
            'surname',
            '--email',
            'test@email.com',
        ],
    )
    assert result.exit_code == 0
    assert result.stdout.strip() == '{\n  "token": "test_token"\n}'


@responses.activate
def test_user_edit(app):
    responses.add(responses.PATCH, f'{API_URL}/users/test', status=204)
    result = runner.invoke(
        app,
        [
            'ecs',
            'users',
            'edit',
            '--username',
            'test',
            '--given-name',
            'surname',
            '--email',
            'test@email.com',
        ],
    )
    assert result.exit_code == 0
    assert result.stdout.strip() == 'User has been modified'


@responses.activate
def test_user_delete(app):
    responses.add(responses.DELETE, f'{API_URL}/users/test', status=204)
    result = runner.invoke(
        app,
        [
            'ecs',
            'users',
            'delete',
            '--username',
            'test',
        ],
    )
    assert result.exit_code == 0
    assert result.stdout.strip() == 'User has been deleted'


@responses.activate
def test_user_list(app):
    server_response = {'user': 'details'}
    responses.add(responses.GET, f'{API_URL}/users', json=server_response, status=200)
    result = runner.invoke(app, ['ecs', 'users', 'list'])
    assert result.exit_code == 0
    assert result.stdout.strip() == json.dumps(server_response, indent=2)


@responses.activate
def test_user_add_auth(users, app, mocker):
    mocker.patch.object(users, 'get_current_working_dir_relative_path_to_ecs_repo').return_value = PosixPath('/')
    responses.add(responses.POST, f'{API_URL}/users/user/auth', status=204)
    result = runner.invoke(app, ['ecs', 'users', 'auth', '--username', 'user', '--action', 'add'], input='y')
    assert result.exit_code == 0
    assert (
        result.stdout.strip()
        == 'Are you sure you want to add / as allowed path for user: user [y/n]: Auth has been added'
    )


@responses.activate
def test_user_list_auth(users, app):
    server_response = {'users': 'details'}
    responses.add(responses.GET, f'{API_URL}/users/user/auth', json=server_response, status=200)
    result = runner.invoke(app, ['ecs', 'users', 'auth', '--username', 'user', '--action', 'list'])
    assert result.exit_code == 0
    assert result.stdout.strip() == json.dumps(server_response, indent=2)


@responses.activate
def test_user_delete_auth(users, app, mocker):
    mocker.patch.object(users, 'get_current_working_dir_relative_path_to_ecs_repo').return_value = PosixPath('/')
    responses.add(responses.DELETE, f'{API_URL}/users/user/auth', status=204)
    result = runner.invoke(app, ['ecs', 'users', 'auth', '--username', 'user', '--action', 'delete'], input='y')
    print(result.stdout)
    print(result.stderr)
    assert result.exit_code == 0
    assert (
        result.stdout.strip()
        == 'Are you sure you want to delete allowed path: / for user: user [y/n]: Auth has been deleted'
    )
