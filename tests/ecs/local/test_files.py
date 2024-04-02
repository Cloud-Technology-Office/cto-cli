import zipfile

import pytest


class TestFilesHandler:
    def test_unpack_remote_zip(self, files_handler, mocker):
        mock_zipfile = mocker.patch('cto_cli.ecs.local.files.zipfile.ZipFile')
        mock_zipfile.return_value.__enter__.side_effect = lambda: mock_zipfile.return_value
        mock_zipfile.return_value.extractall.side_effect = mocker.Mock()

        mocker.patch('builtins.open', mocker.mock_open(read_data=b'mocked_zip_content'))
        mocker.patch('cto_cli.ecs.local.files.base64.b64decode', return_value=b'decoded_content')

        files_handler.FilesHandler.unpack_remote_zip('mocked_remote_zip_path', 'mocked_extract_path')

        mock_zipfile.assert_called_once_with('mocked_remote_zip_path', 'r')
        mock_zipfile.return_value.extractall.assert_called_once_with(path='mocked_extract_path')

    def test_unpack_remote_zip_bad_zip_file(self, files_handler, mocker):
        mock_zipfile = mocker.patch('cto_cli.ecs.local.files.zipfile.ZipFile')
        mock_zipfile.side_effect = zipfile.BadZipFile
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'mocked_zip_content'))
        mocker.patch('cto_cli.ecs.local.files.base64.b64decode', return_value=b'decoded_content')

        with pytest.raises(zipfile.BadZipFile):
            files_handler.FilesHandler.unpack_remote_zip('mocked_remote_zip_path', 'mocked_extract_path')
