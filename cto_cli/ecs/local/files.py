import base64
import io
import json
import os
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence, Any

from cto_cli.ecs.local.commands import run_command
from cto_cli.ecs.local.settings import get_repo_path, get_hashes_path
from cto_cli.utils.errors import print_error

EXCLUDED_PATHS = ['*.idea/*', '*.git/*', '*.vscode/*']


class HashTypeUpdate:
    CURRENT = 'current'
    BOTH = 'both'


@dataclass
class ModifiedFiles:
    added: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    modified_only_locally: list[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return any(len(element) > 0 for element in (self.added, self.modified, self.deleted))

    def get_added_or_updated_paths(self) -> list[str]:
        return [*self.added, *self.modified]


class FilesHandler:
    def __init__(self):
        self._modified_files = self._get_modified_local_files()

    @staticmethod
    def _get_local_repo_hashes() -> dict[str, str]:
        file_hashes = {}

        excluded_paths = ''

        for excluded_path in EXCLUDED_PATHS:
            excluded_paths += f'-not -path {excluded_path} '
        result = run_command(
            f'find {get_repo_path()} -type f {excluded_paths} -exec sha256sum {{}} +', capture_output=True, output=True
        ).stdout.decode('utf-8')

        for line in result.split('\n'):
            if line:
                split_line = line.split('  ', maxsplit=1)

                hash = split_line[0]
                file = split_line[1].replace(f'{get_repo_path()}/', '')

                file_hashes[file] = hash

        return file_hashes

    @staticmethod
    def get_stored_remote_hashes() -> dict[str, Any]:
        try:
            with open(get_hashes_path(), 'r') as repo_hash_file:
                return json.load(repo_hash_file)
        except FileNotFoundError:
            print_error('Pull config first', exit=True)

    def _get_modified_local_files(self) -> ModifiedFiles:
        modified_file_paths = ModifiedFiles()

        local_repo_hashes = self._get_local_repo_hashes()
        remote_repo_hashes = self.get_stored_remote_hashes()
        current_remote_file_hashes = remote_repo_hashes['current']['files']
        before_remote_file_hashes = remote_repo_hashes['before']['files']

        for local_file_path, local_hash in local_repo_hashes.items():
            if local_file_path not in current_remote_file_hashes:
                modified_file_paths.added.append(local_file_path)

            else:
                if local_hash != current_remote_file_hashes[local_file_path]:
                    modified_file_paths.modified.append(local_file_path)
                    try:
                        hash_unchanged = (
                            current_remote_file_hashes[local_file_path] == before_remote_file_hashes[local_file_path]
                        )
                    except KeyError:
                        pass
                    else:
                        if hash_unchanged:
                            modified_file_paths.modified_only_locally.append(local_file_path)

        for remote_file_path, remote_hash in current_remote_file_hashes.items():
            if remote_file_path not in local_repo_hashes:
                modified_file_paths.deleted.append(remote_file_path)

        return modified_file_paths

    @property
    def modified_files(self) -> ModifiedFiles:
        return self._modified_files

    @staticmethod
    def update_remote_hashes(repo_hash: dict[str, Any], update_type: HashTypeUpdate):
        if update_type is HashTypeUpdate.BOTH:
            content = {'current': repo_hash, 'before': repo_hash}
        else:
            with open(get_hashes_path(), 'r') as repo_hash_file:
                content = json.load(repo_hash_file)
            content['current'] = repo_hash

        with open(get_hashes_path(), 'w') as repo_hash_file:
            repo_hash_file.write(json.dumps(content, indent=4))

    @staticmethod
    def zip_paths(paths: Sequence, root_path: str | Path | None = None) -> io.BytesIO:
        in_memory_buffer = io.BytesIO()
        with zipfile.ZipFile(in_memory_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for path in paths:
                if root_path:
                    source = Path(root_path) / path
                else:
                    source = path
                zipf.write(source, path)

        in_memory_buffer.seek(0)
        return in_memory_buffer

    @staticmethod
    def zip_path(path: str | Path) -> io.BytesIO:
        in_memory_buffer = io.BytesIO()
        with zipfile.ZipFile(in_memory_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(path):
                if '.git' in dirs:
                    dirs.remove('.git')

                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, path))

        in_memory_buffer.seek(0)
        return in_memory_buffer

    @staticmethod
    def remove_contents(path: str | Path) -> None:
        for content in os.listdir(path):
            full_path = os.path.join(path, content)
            if os.path.isfile(full_path):
                os.remove(full_path)
            else:
                shutil.rmtree(full_path)

    @staticmethod
    def remove_files(root_path: str | Path, paths_to_delete: list[str]) -> None:
        for path_to_delete in paths_to_delete:
            os.remove(os.path.join(root_path, path_to_delete))

    @staticmethod
    def unpack_remote_zip(remote_zip_path: str | Path, extract_path: str | Path):
        try:
            with zipfile.ZipFile(remote_zip_path, 'r') as zip_file:
                zip_file.extractall(path=extract_path)
        except zipfile.BadZipFile:
            with open(remote_zip_path, 'rb') as file:
                data = file.read()
                decoded_data = base64.b64decode(data)

                with zipfile.ZipFile(io.BytesIO(decoded_data), 'r') as zip_file:
                    zip_file.extractall(path=extract_path)
