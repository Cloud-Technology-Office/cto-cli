from cto_cli.ecs.local.settings import load_ecs_settings, ECSSettings
from unittest.mock import mock_open


def test_load_ecs_settings_from_env(monkeypatch):
    monkeypatch.setenv('ECS_URL', 'test_url')
    monkeypatch.setenv('ECS_TOKEN', 'test_token')
    monkeypatch.setenv('ECS_LOCAL_PATH', 'ecs_local_path')

    result = load_ecs_settings()

    assert result == ECSSettings(url='test_url', token='test_token', ecs_path='ecs_local_path')


def test_load_ecs_settings_from_file(mocker):
    mocker.patch(
        'builtins.open', mock_open(read_data='{"token": "test_token", "url": "test_url", "ecs_path": "ecs_local_path"}')
    )

    result = load_ecs_settings()

    assert result == ECSSettings(url='test_url', token='test_token', ecs_path='ecs_local_path')
