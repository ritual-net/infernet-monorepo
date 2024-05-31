import logging
import tempfile

from ritual_arweave.types import RepoId

from .utils import FixtureType, TemporaryRepo, mine_block, upload_repo

log = logging.getLogger(__name__)


def test_upload_and_download_repo(fund_account: FixtureType) -> None:
    repo1 = TemporaryRepo(
        name="repo1",
        files_dict={
            "file1": "This is a mock repo file. Henlo.",
            "file2": "This is another file.",
        },
    ).create()

    mm = upload_repo(repo1)

    with tempfile.TemporaryDirectory() as temp_dir:
        paths = mm.download_repo(
            repo_id=RepoId(name=repo1.name, owner=mm.wallet.address),
            base_path=temp_dir,
        )
        repo1.check_against_directory(temp_dir)
        repo1.check_paths(paths)

    repo1.delete()


def test_uploading_repo_twice_and_downloading_again_should_give_latest_version(
    fund_account: FixtureType,
) -> None:
    repo_name = "repo1"
    original_repo = TemporaryRepo(
        name=repo_name,
        files_dict={
            "file1": "This is a mock repo file. Henlo.",
            "file2": "This is another file.",
        },
    ).create()

    upload_repo(original_repo)

    updated_repo = TemporaryRepo(
        name=repo_name,
        files_dict={
            "file1": "This is an updated mock repo file. Henlo.",
            "file2": "This is another file.",
            "file3": "This is a new file.",
        },
    ).create()

    mm = upload_repo(updated_repo)

    # mine a block in arlocal to make the repo available for download
    mine_block()

    with tempfile.TemporaryDirectory() as temp_dir:
        paths = mm.download_repo(
            repo_id=RepoId(name=repo_name, owner=mm.wallet.address),
            base_path=temp_dir,
        )
        updated_repo.check_against_directory(temp_dir)
        updated_repo.check_paths(paths)
        # assert that the same check against original repo fails
        try:
            original_repo.check_against_directory(temp_dir)
            original_repo.check_paths(paths)
            assert False
        except AssertionError:
            pass

    original_repo.delete()
    updated_repo.delete()


def test_versioned_repo_download(fund_account: FixtureType) -> None:
    repo_name = "repo1"
    versioned_repo = TemporaryRepo(
        name=repo_name,
        files_dict={
            "file1": "This is a mock repo file. Henlo.",
            "file2": "This is another file.",
        },
    ).create()

    mm = upload_repo(
        versioned_repo,
        version_mapping={
            "file1": "1.0.0",
            "file2": "1.0.0",
        },
    )

    latest_repo = TemporaryRepo(
        name=repo_name,
        files_dict={
            "file1": "This is an updated mock repo file. Henlo.",
            "file2": "This is another file.",
            "file3": "This is a new file.",
        },
    ).create()
    upload_repo(latest_repo)

    with tempfile.TemporaryDirectory() as temp_dir:
        latest_file = mm.download_artifact_file(
            repo_id=RepoId(name=repo_name, owner=mm.wallet.address),
            file_name="file1",
            base_path=temp_dir,
        )

        latest_repo.check_against_file(latest_file)

        versioned_file = mm.download_artifact_file(
            repo_id=RepoId(name=repo_name, owner=mm.wallet.address),
            file_name="file1",
            version="1.0.0",
            base_path=temp_dir,
        )
        versioned_repo.check_against_file(versioned_file)

        # assert that versioned file isn't in the latest repo
        try:
            latest_repo.check_against_file(versioned_file)
            assert False
        except AssertionError:
            pass

        # assert that the latest file is not in the versioned repo
        try:
            versioned_repo.check_against_file(latest_file)
            assert False
        except AssertionError:
            pass

    versioned_repo.delete()
    latest_repo.delete()


def test_download_repo_file(fund_account: FixtureType) -> None:
    repo = TemporaryRepo(
        name="repo1",
        files_dict={
            "file1": "This is a mock repo file. Henlo.",
            "file2": "This is another file.",
        },
    ).create()

    mm = upload_repo(repo)

    for file in repo.files_dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = mm.download_artifact_file(
                repo_id=RepoId(name=repo.name, owner=mm.wallet.address),
                file_name=file,
                base_path=temp_dir,
            )
            repo.check_against_file(file_path)

    repo.delete()


def test_download_repo_using_string_id(fund_account: FixtureType) -> None:
    repo = TemporaryRepo(
        name="repo1",
        files_dict={
            "file1": "This is a mock repo file. Henlo.",
            "file2": "This is another file.",
        },
    ).create()

    mm = upload_repo(repo)

    # download entire repo
    with tempfile.TemporaryDirectory() as temp_dir:
        paths = mm.download_repo(
            repo_id=f"{mm.wallet.address}/{repo.name}",
            base_path=temp_dir,
        )
        repo.check_against_directory(temp_dir)
        repo.check_paths(paths)

    # download a specific file
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = mm.download_artifact_file(
            repo_id=f"{mm.wallet.address}/{repo.name}",
            file_name="file1",
            base_path=temp_dir,
        )
        repo.check_against_file(file_path)

    repo.delete()
