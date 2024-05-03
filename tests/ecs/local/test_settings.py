import pytest

from cto_cli.ecs.local.settings import load_ecs_settings, ECSSettings
from unittest.mock import mock_open


def test_load_ecs_settings_from_env(monkeypatch):
    monkeypatch.setenv('ECS_URL', 'test_url')
    monkeypatch.setenv('ECS_TOKEN', 'test_token')
    monkeypatch.setenv('ECS_LOCAL_PATH', 'ecs_local_path')

    result = load_ecs_settings()

    assert result == ECSSettings(url='test_url', token='test_token', ecs_path='ecs_local_path')


def test_load_saas_ecs_settings_from_env(monkeypatch):
    monkeypatch.setenv('ECS_URL', 'test_url')
    monkeypatch.setenv('ECS_TOKEN', 'test_token')
    monkeypatch.setenv('ECS_LOCAL_PATH', 'ecs_local_path')
    monkeypatch.setenv('ECS_SAAS_TOKEN', 'ecs_saas_token')

    result = load_ecs_settings()

    assert result == ECSSettings(url='test_url', token='test_token', ecs_path='ecs_local_path', saas_token='ecs_saas_token')


@pytest.mark.parametrize(
    'file_content,loaded_instance',
    [
        (
            '{"token": "test_token", "url": "test_url", "ecs_path": "ecs_local_path"}',
            ECSSettings(url='test_url', token='test_token', ecs_path='ecs_local_path'),
        ),
        (
            '{"token": "test_token", "url": "test_url", "ecs_path": "ecs_local_path", "saas_token": "ecs_saas_token"}',
            ECSSettings(url='test_url', token='test_token', ecs_path='ecs_local_path', saas_token='ecs_saas_token'),
        ),
    ],
)
def test_load_ecs_settings_from_file(mocker, file_content, loaded_instance):
    mocker.patch('builtins.open', mock_open(read_data=file_content))

    result = load_ecs_settings()

    assert result == loaded_instance
