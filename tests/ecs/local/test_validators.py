import pytest
import responses
from typer import Exit

from constants import API_URL


@pytest.fixture
def validators(mocked_settings):
    from cto_cli.ecs.local import validators

    yield validators


@pytest.mark.parametrize(
    'server_response,current_cli_version,cli_response,should_error',
    [
        (
            {
                'status': 'healthy',
                'version': '0.1.0',
                'compatibility': {'cli_versions': ['0.2.*']},
            },
            '0.0.1',
            (
                'The current cli version: 0.0.1 is not compatible with the server version: '
                '0.1.0.\n'
                "Please use one of these cli versions: ['0.2.*']\n"
            ),
            True,
        ),
        (
            {
                'status': 'healthy',
                'version': '0.1.0',
                'compatibility': {'cli_versions': ['0.1.*']},
            },
            '0.1.4',
            None,
            False,
        ),
    ],
)
@responses.activate
def test_check_versions_compatibility(
    validators, mocker, server_response, current_cli_version, should_error, cli_response, capsys
):
    responses.add(responses.GET, f'{API_URL}/', json=server_response, status=200)
    mocker.patch.object(validators, 'get_current_cli_version').return_value = current_cli_version

    if should_error:
        with pytest.raises(Exit):
            validators.check_versions_compatibility()
        out, err = capsys.readouterr()
        assert err == cli_response
    else:
        validators.check_versions_compatibility()
