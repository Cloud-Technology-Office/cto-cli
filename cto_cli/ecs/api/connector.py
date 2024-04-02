import sys
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from requests import HTTPError, ConnectionError, Timeout
from rich import print, print_json
from rich.syntax import Syntax

from cto_cli.ecs.local.settings import load_ecs_settings, SettingsNotFound
from cto_cli.utils.errors import print_error


class ApiError(Exception):
    pass


class APIConnector:
    def __init__(self, load_settings: bool = True, url: str | None = None, headers: dict | None = None):
        self._headers = headers
        self._url = url

        if load_settings:
            self._set_api_details()

    @staticmethod
    def _handle_response(response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            try:
                print_error(f'{e.response.json()["detail"]}', exit=True)
            except Exception:
                print_error(f'{e.response.text}', exit=True)

    def _set_api_details(self) -> None:
        try:
            settings = load_ecs_settings()
        except SettingsNotFound:
            print_error('Credentials not found, run [b]cto ecs init[b]', exit=True)
            sys.exit(1)

        self._headers = {'Authorization': settings.token}
        self._url = settings.url

    @staticmethod
    def _print_response(response: requests.Response) -> None:
        if response.headers['content-type'] == 'application/json':
            response_json = response.json()
            print_json(data=response_json)
        elif response.headers['content-type'] == 'application/yaml':
            print(Syntax(response.text, 'yaml'))
        else:
            print(response.text)

    def _make_request(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        json: dict | None = None,
        params: dict | None = None,
        files: dict | None = None,
        **kwargs,
    ):
        if not headers:
            headers = {}

        try:
            return requests.request(
                method,
                url=f'{self._url}/{url}',
                headers={**self._headers, **headers},
                json=json,
                files=files,
                params=params,
                **kwargs,
            )
        except requests.exceptions.RequestException:
            print_error('Cannot connect to ECS API', exit=True)

    # USERS
    def create_user(
        self,
        username: str,
        given_name: str,
        family_name: str,
        admin: bool = False,
        return_as_dict: bool = False,
        read_secrets: bool = False,
        edit_strategies: bool = False,
    ) -> dict | None:
        response = self._make_request(
            'post',
            'users',
            json={
                'username': username,
                'given_name': given_name,
                'family_name': family_name,
                'admin': admin,
                **({'read_secrets': read_secrets} if admin is False else {}),
                **({'edit_strategies': edit_strategies} if admin is False else {}),
            },
            headers=self._headers,
        )
        self._handle_response(response)

        if return_as_dict:
            return response.json()
        else:
            print(response.text)

    def list_users(self):
        response = self._make_request('get', 'users')
        self._handle_response(response)
        print_json(data=response.json())

    def add_auth(self, username: str, allowed_path: str | Path) -> None:
        response = self._make_request(
            'post',
            f'users/{username}/auth',
            json={
                'allowed_path': str(allowed_path),
            },
        )
        self._handle_response(response)
        if response.status_code == 204:
            print('[green]Auth has been added[/green]')

    def list_auth(self, username: str) -> None:
        response = self._make_request(
            'get',
            f'users/{username}/auth',
        )
        self._handle_response(response)
        print_json(data=response.json())

    def delete_auth(self, username: str, path: str | Path) -> None:
        response = self._make_request(
            'delete',
            f'users/{username}/auth',
            params={'path': str(path)},
        )
        self._handle_response(response)
        if response.status_code == 204:
            print('[green]Auth has been deleted[/green]')

    # CONFIG
    def get_raw_content(self, output_path: str | Path) -> None:
        with self._make_request('get', 'config/raw', stream=True) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    def get_config_hashes(self) -> dict[str, Any]:
        response = self._make_request('get', 'config/hashes')
        self._handle_response(response)

        return response.json()

    def push_config_changes(
        self, file_with_changes: BytesIO, deleted_files: list[str], commit_hash: str
    ) -> None | dict:
        response = self._make_request(
            'post',
            'config',
            headers={'commit-hash': commit_hash},
            files={'file': file_with_changes},
            data={'deleted_files': deleted_files},
        )

        self._handle_response(response)

        response_json = response.json()
        print_json(data=response_json)

        return response_json

    def build_config(
        self,
        path: str | Path,
        strategy_name: str | None = None,
        recursive: bool = False,
        show_secrets: bool = False,
        format: str | None = None,
        filter: str | None = None,
    ):
        response = self._make_request(
            'post',
            'config/build',
            json={
                'path': path,
                'recursive': recursive,
                **({'show_secrets': show_secrets} if show_secrets else {}),
                **({'strategy_name': strategy_name} if strategy_name else {}),
                **({'format': format} if format else {}),
                **({'filter': filter} if filter else {}),
            },
        )

        self._handle_response(response)
        self._print_response(response)

    def decrypt_file(
        self,
        path: str | Path,
    ):
        response = self._make_request(
            'post',
            'config/decrypt',
            json={
                'path': path,
            },
        )

        self._handle_response(response)
        self._print_response(response)

    # GENERAL

    def get_version_details(self) -> dict[str, Any]:
        response = self._make_request(
            'get',
            '',
        )
        self._handle_response(response)

        return response.json()

    def check_api_connectivity(self):
        try:
            response = requests.request('get', f'{self._url}/users', headers=self._headers)
        except (ConnectionError, Timeout):
            raise ApiError('Could not connect to the API, validate URL')
        try:
            response.raise_for_status()
        except HTTPError:
            raise ApiError('Token is not valid')
