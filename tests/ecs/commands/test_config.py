import json
from pathlib import PosixPath

import pytest
import responses
from typer.testing import CliRunner

from constants import API_URL

runner = CliRunner(mix_stderr=False)


class TypeMatcher:
    def __init__(self, expected_type):
        self.expected_type = expected_type

    def __eq__(self, other):
        return isinstance(other, self.expected_type)


@pytest.fixture
def config(mocked_validate_current_dir, mocked_settings):
    from cto_cli.ecs.commands import config

    yield config


@pytest.mark.parametrize(
    'cmd,api_response,api_response_type,api_error,cli_response,cli_exit_code',
    [
        (
            ['ecs', 'config', 'build', '--path', '/', '--strategy-name', 'strategy'],
            {'all': 'good'},
            'json',
            False,
            json.dumps({'all': 'good'}, indent=2),
            0,
        ),
        (
            ['ecs', 'config', 'build', '--path', '/', '--strategy-name', 'strategy', '--format', 'yaml'],
            'all: good',
            'yaml',
            False,
            'all: good',
            0,
        ),
        (
            ['ecs', 'config', 'build', '--path', '/', '--strategy-name', 'broken_strategy'],
            {'detail': 'Specified strategy is not correct'},
            'json',
            True,
            'Specified strategy is not correct',
            1,
        ),
        (
            ['ecs', 'config', 'build', '--path', '/', '--strategy-name', 'a'],
            {'detail': 'Specified strategy is not correct'},
            'json',
            True,
            'Invalid value: strategy-name must have at least 2 characters',
            2,
        ),
    ],
)
@responses.activate
def test_build(app, cmd, api_response, api_response_type, api_error, cli_response, cli_exit_code):
    if api_response_type == 'json':
        responses.add(responses.POST, f'{API_URL}/config/build', json=api_response, status=400 if api_error else 200)
    elif api_response_type == 'yaml':
        responses.add(
            responses.POST,
            f'{API_URL}/config/build',
            body=api_response,
            status=400 if api_error else 200,
            headers={'content-type': 'application/yaml'},
        )

    result = runner.invoke(app, cmd)
    assert result.exit_code == cli_exit_code
    if cli_exit_code != 0:
        assert cli_response in result.stderr.strip()
    else:
        assert result.stdout.strip() == cli_response


@pytest.mark.parametrize(
    'is_updated_needed,exit_code,server_modified_files,cli_response',
    [
        (True, 1, None, 'Repo is not up-to-date, run cto ecs config pull to update'),
        (False, 0, None, ''),
        (False, 0, ['file1', 'file2'], ''),
    ],
)
@responses.activate
def test_push(config, files_handler, app, mocker, is_updated_needed, exit_code, server_modified_files, cli_response):
    server_hashes_response = {'test': 'test_hash'}
    server_response_config = {
        'status': 'Changes were pushed',
        'warning': None,
        'skipped_files': [],
        'server_modified_files': [],
    }
    mocker.patch.object(config, 'is_repo_update_needed').return_value = is_updated_needed

    if is_updated_needed is False:
        mocker.patch.object(config, 'handle_config_push').return_value = server_modified_files
        mocker.patch.object(config, 'pull_remote_repo')
        mocker.patch.object(config, 'update_server_modified_files')

    responses.add(responses.GET, f'{API_URL}/config/hashes', json=server_hashes_response, status=200)
    responses.add(responses.POST, f'{API_URL}/config', json=server_response_config, status=200)

    result = runner.invoke(app, ['ecs', 'config', 'push'])

    config.is_repo_update_needed.assert_called_with(server_hashes_response)
    if is_updated_needed is False:
        config.handle_config_push.assert_called_with(TypeMatcher(config.APIConnector))
        config.pull_remote_repo.assert_called_with(
            TypeMatcher(config.APIConnector), **{'show_status': False, 'update_type': 'both'}
        )

    if server_modified_files:
        config.update_server_modified_files.assert_called_with(server_modified_files)

    assert result.exit_code == exit_code
    if exit_code == 1:
        assert result.stderr.strip() == cli_response
    else:
        assert result.stdout.strip() == cli_response


@pytest.mark.parametrize(
    'is_updated_needed,cli_response',
    [
        (False, 'Config is already up-to-date'),
        (True, 'Config has been updated'),
    ],
)
@responses.activate
def test_pull(config, files_handler, app, mocker, is_updated_needed, cli_response):
    get_hashes_response_json = {'/file.yaml': 'hash'}
    mocker.patch.object(config, 'is_repo_update_needed').return_value = is_updated_needed

    if is_updated_needed:
        mocker.patch.object(config, 'handle_config_update')
        mocker.patch.object(files_handler.FilesHandler, 'update_remote_hashes')

    responses.add(responses.GET, f'{API_URL}/config/hashes', json=get_hashes_response_json, status=200)
    responses.add(responses.GET, f'{API_URL}/config/raw', body='files_body', status=200)
    result = runner.invoke(app, ['ecs', 'config', 'pull'])

    config.is_repo_update_needed.assert_called_with(get_hashes_response_json)
    if is_updated_needed:
        config.handle_config_update.assert_called_with(PosixPath('/tmp/repo.zip'))
        files_handler.FilesHandler.update_remote_hashes.assert_called_with(get_hashes_response_json, 'current')
    print(result.stdout)
    assert result.exit_code == 0
    assert result.stdout.strip() == cli_response


@pytest.mark.parametrize(
    'modified_local_files,cli_result',
    [
        ({}, 'No modified files'),
        (
            {
                'added': ['/test/added1.yaml', '/test/added2.yaml'],
                'modified': ['/test/modified.yaml'],
                'deleted': ['/test/deleted.yaml'],
            },
            (
                'Added:\n'
                '[\n'
                '    "/test/added1.yaml",\n'
                '    "/test/added2.yaml"\n'
                ']\n'
                '\n'
                'Modified:\n'
                '[\n'
                '    "/test/modified.yaml"\n'
                ']\n'
                '\n'
                'Deleted:\n'
                '[\n'
                '    "/test/deleted.yaml"\n'
                ']'
            ),
        ),
    ],
)
def test_status(files_handler, app, mocker, modified_local_files, cli_result):
    mocker.patch.object(
        files_handler.FilesHandler, '_get_modified_local_files'
    ).return_value = files_handler.ModifiedFiles(**modified_local_files)
    result = runner.invoke(app, ['ecs', 'config', 'status'])
    assert result.exit_code == 0
    assert result.stdout.strip() == cli_result


@responses.activate
def test_decrypt(app):
    responses.add(responses.POST, f'{API_URL}/config/decrypt', json={'decrypted': 'content'}, status=200)
    result = runner.invoke(app, ['ecs', 'config', 'decrypt', '--path', '/encrypted.yaml'])
    assert result.exit_code == 0
    assert result.stdout.strip() == json.dumps({'decrypted': 'content'}, indent=2)
