from pathlib import PosixPath

import pytest


@pytest.mark.parametrize('repo_exist', [(True), (False)])
def test_handle_config_update(operations, files_handler, repo_exist, mocker):
    remote_zip_path = 'zip_location.zip'
    modified_local_files = {
        'added': ['/test/added1.yaml', '/test/added2.yaml'],
        'modified': ['/test/modified.yaml'],
        'deleted': ['/test/deleted.yaml'],
    }

    mocked_path = mocker.Mock(spec=operations.Path)
    mocked_path.exists.return_value = repo_exist

    if repo_exist:
        mocker.patch.object(
            files_handler.FilesHandler, '_get_modified_local_files'
        ).return_value = files_handler.ModifiedFiles(**modified_local_files)
        mocker.patch.object(files_handler.FilesHandler, 'zip_paths')

    mocker.patch.object(operations, 'get_repo_path').return_value = mocked_path
    mocker.patch.object(files_handler.FilesHandler, 'remove_contents')
    mocker.patch.object(files_handler.FilesHandler, 'unpack_remote_zip')
    mocker.patch.object(operations, 'run_command')

    if repo_exist:
        mocked_zip_file = mocker.patch.object(operations.zipfile, 'ZipFile')
    os_remove_mock = mocker.patch('os.remove')

    operations.handle_config_update(remote_zip_path)

    if repo_exist:
        files_handler.FilesHandler.zip_paths.assert_called_with(
            ['/test/added1.yaml', '/test/added2.yaml', '/test/modified.yaml'], root_path=mocked_path
        )
    files_handler.FilesHandler.remove_contents.assert_called_with(mocked_path)
    files_handler.FilesHandler.unpack_remote_zip.assert_called_with(remote_zip_path, mocked_path)

    if repo_exist:
        mocked_zip_file.assert_called_with(files_handler.FilesHandler.zip_paths.return_value, 'r')

    os_remove_mock.assert_called_with(remote_zip_path)


@pytest.mark.parametrize(
    'sys_exit,modified_local_files,server_response',
    [
        (
            True,
            {
                'added': [],
                'modified': [],
                'deleted': [],
            },
            {},
        ),
        (
            False,
            {
                'added': ['/test/added1.yaml', '/test/added2.yaml'],
                'modified': ['/test/modified.yaml'],
                'deleted': ['/test/deleted.yaml'],
            },
            {'server_modified_files': ['file1, file2'], 'skipped_files': ['file3']},
        ),
    ],
)
def test_handle_config_push(
    mocked_settings, files_handler, operations, mocker, capsys, sys_exit, modified_local_files, server_response
):
    api_connector_mock = mocker.Mock(spec=operations.APIConnector)
    api_connector_mock.push_config_changes.return_value = server_response
    mocker.patch.object(
        files_handler.FilesHandler, '_get_modified_local_files'
    ).return_value = files_handler.ModifiedFiles(**modified_local_files)
    mocker.patch.object(operations, '_restore_and_delete_stash')
    mocker.patch.object(files_handler.FilesHandler, 'get_stored_remote_hashes').return_value = {
        'current': {'repo_hash': 'test_hash'}
    }
    mocker.patch.object(files_handler.FilesHandler, 'remove_files')
    mocker.patch.object(operations, 'run_command')
    mocker.patch.object(operations, '_merge_remote_branch')
    mocker.patch.object(operations, '_restore_and_delete_stash')
    mocker.patch.object(operations.Confirm, 'ask')
    mocked_zip_file = mocker.patch.object(operations.zipfile, 'ZipFile')

    if sys_exit:
        with pytest.raises(SystemExit) as wrapped_error:
            result = operations.handle_config_push(mocker.Mock())
        assert wrapped_error.value.code == 0
        out, err = capsys.readouterr()
        assert out == 'There is nothing to be pushed\n'
    else:
        result = operations.handle_config_push(api_connector_mock)

    if 'skipped_files' in server_response:
        files_handler.FilesHandler.remove_files.assert_called_with(
            root_path=PosixPath('/tmp/repo'), paths_to_delete=server_response['skipped_files']
        )

    if 'server_modified_files' in server_response:
        assert result == server_response['server_modified_files']
