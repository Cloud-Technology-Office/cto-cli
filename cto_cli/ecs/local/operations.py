import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any, Optional

from rich import print
from rich.prompt import Confirm

from cto_cli.ecs.api.connector import APIConnector
from cto_cli.ecs.local.commands import run_command
from cto_cli.ecs.local.files import FilesHandler, ModifiedFiles, HashTypeUpdate
from cto_cli.ecs.local.settings import get_repo_path, get_hashes_path
from cto_cli.utils.errors import print_error

LOCAL_BRANCH = 'local'
REMOTE_BRANCH = 'remote'
MERGE_BRANCH = 'merge'

STASH_NAME = 'ECS'

EXCLUDED_COMMIT_LOCATIONS = ['.idea/', '.vscode/']

GIT_CONFLICTS_DETECTED_ERROR_MSG = (
    '[red]There are conflicts that have to be manually solved. To view details run [yellow]git status[/yellow]. '
    'Once conflicts are solved [yellow]git commit -am "anything"[/yellow] and then [yellow]ecs config push[/yellow] again[/red]'
)


def show_modified_local_files(modified_files: ModifiedFiles):
    print(f'[green]Added:[/green]\n[green]{json.dumps(modified_files.added, indent=4)}[/green]\n')
    print(f'[yellow]Modified:[/yellow]\n[yellow]{json.dumps(modified_files.modified, indent=4)}[/yellow]\n')
    print(f'[red]Deleted:[/red]\n[red]{json.dumps(modified_files.deleted, indent=4)}[/red]\n')


def is_repo_update_needed(repo_hashes: dict[str, Any]) -> bool:
    if get_hashes_path().exists() is False:
        FilesHandler.update_remote_hashes(repo_hashes, update_type=HashTypeUpdate.BOTH)
        return True

    if FilesHandler.get_stored_remote_hashes()['current']['repo_hash'] == repo_hashes['repo_hash']:
        return False

    return True


def update_server_modified_files(server_modified_files: list[str]) -> None:
    run_command(f'cd {get_repo_path()} && git checkout {" ".join(server_modified_files)}')


def handle_config_update(remote_zip_path: str | Path) -> None:
    repo_exists = get_repo_path().exists()
    zipped_local_changes = None

    if repo_exists:
        modified_files = FilesHandler().modified_files.get_added_or_updated_paths()
        zipped_local_changes = FilesHandler.zip_paths(modified_files, root_path=get_repo_path())

    try:
        FilesHandler.remove_contents(get_repo_path())
    except FileNotFoundError:
        pass

    # create remote repo with empty commit and local branch out of it
    run_command(
        f'cd {get_repo_path()} && git init -b remote && git commit --allow-empty -m "empty commit" &&'
        f' git checkout -b local && git checkout remote',
        output=False,
    )

    # unzip content from serer to remote branch
    FilesHandler.unpack_remote_zip(remote_zip_path, get_repo_path())

    # commit remote changes and switch to local branch
    run_command(f'cd {get_repo_path()} && git add -A && git commit -m "remote" || true && git checkout local')

    # unzip content from serer to local branch
    FilesHandler.unpack_remote_zip(remote_zip_path, get_repo_path())

    run_command(f'cd {get_repo_path()} && git add -A && git commit -m "remote state" || true')

    if repo_exists:
        with zipfile.ZipFile(zipped_local_changes, 'r') as zip:
            zip.extractall(path=get_repo_path())

    os.remove(remote_zip_path)


def _are_branches_merged() -> bool:
    return (
        run_command(
            f'cd {get_repo_path()} && git checkout {MERGE_BRANCH} || true && MERGED_BRANCHES=$(git branch --merged) '
            f'&& echo $MERGED_BRANCHES | grep {REMOTE_BRANCH} && echo $MERGED_BRANCHES | grep {LOCAL_BRANCH}',
            check=False,
            output=False,
        ).returncode
        == 0
    )


def _merge_remote_branch() -> None:
    if (
        run_command(
            f'cd {get_repo_path()} && git merge {REMOTE_BRANCH} -m "merge {REMOTE_BRANCH}"', check=False, output=False
        ).returncode
        == 0
    ):
        return
    print_error(GIT_CONFLICTS_DETECTED_ERROR_MSG, exit=True)


def _commit_merge_branch_changes() -> None:
    # check if merge branch is not in merging mode
    if (
        run_command(
            f'cd {get_repo_path()} && git checkout {MERGE_BRANCH} || true && git status | grep "You have unmerged paths"',
            check=False,
            output=False,
        ).returncode
        == 0
    ):
        print_error(GIT_CONFLICTS_DETECTED_ERROR_MSG, exit=True)

    run_command(
        f'cd {get_repo_path()} && git checkout {MERGE_BRANCH} || true && git add -A && commit -m "changes before push" || true'
    )


def _restore_and_delete_stash(commit: bool = False):
    stash = (
        run_command(f'git stash list | grep {STASH_NAME} | cut -d: -f1', capture_output=True)
        .stdout.decode('utf-8')
        .strip()
    )

    if stash:
        run_command(f'git stash apply {stash} && git stash drop {stash}')

        if commit:
            run_command('git commit -a -m "changes before push"')


def handle_config_push(api_connector: APIConnector) -> Optional[list[str]]:
    _restore_and_delete_stash()

    commit_hash = FilesHandler.get_stored_remote_hashes()['current']['repo_hash']
    modified_files = FilesHandler().modified_files

    if not modified_files.has_changes():
        print('[yellow]There is nothing to be pushed[/yellow]')
        sys.exit(0)

    show_modified_local_files(modified_files)

    if modified_files.modified_only_locally:
        full_path_files = [
            str(get_repo_path() / modified_file) for modified_file in modified_files.modified_only_locally
        ]
        run_command(f'git stash push -m {STASH_NAME} -- {" ".join(full_path_files)}')

    # check if merge branch exists
    merge_branch_exists = (
        run_command(
            f'cd {get_repo_path()} && git branch -a | grep merge',
            check=False,
        ).returncode
        == 0
    )

    if merge_branch_exists:
        _commit_merge_branch_changes()
    else:
        print('Creating new merge branch')
        # create a new merge branch that has code from the local branch
        run_command(
            f'cd {get_repo_path()} && git checkout {LOCAL_BRANCH} || true && git add --all :/ &&'
            f' git reset -- {" ".join(EXCLUDED_COMMIT_LOCATIONS)} && git commit -a -m "changes before push" || true &&'
            f' git checkout -b merge '
        )

    if not _are_branches_merged():
        _merge_remote_branch()

    _restore_and_delete_stash(commit=True)
    zipped_local_changes = FilesHandler.zip_paths(
        modified_files.get_added_or_updated_paths(), root_path=get_repo_path()
    )

    response = api_connector.push_config_changes(zipped_local_changes, modified_files.deleted, commit_hash)

    if response and (skipped_files := response.get('skipped_files')):
        skipped_files_json = json.dumps(skipped_files, indent=4)
        delete_files = Confirm.ask(
            f"These paths were skipped on ecs push as you haven't been authed against them: "
            f'[yellow]{skipped_files_json}[/yellow]\n Do you want to [red]delete[/red] them?'
        )

        if delete_files:
            FilesHandler.remove_files(root_path=get_repo_path(), paths_to_delete=skipped_files)
            print('[green]Files have been deleted[/green]')

    if response and (server_modified_files := response.get('server_modified_files')):
        return server_modified_files
