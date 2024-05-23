import logging
import tempfile

from ritual_arweave.types import ModelId

from .utils import FixtureType, TemporaryModel, mine_block, upload_model

log = logging.getLogger(__name__)


def test_upload_and_download_model(fund_account: FixtureType) -> None:
    model1 = TemporaryModel(
        name="model1",
        files_dict={
            "file1": "This is a mock model file. Henlo.",
            "file2": "This is another file.",
        },
    ).create()

    mm = upload_model(model1)

    with tempfile.TemporaryDirectory() as temp_dir:
        paths = mm.download_model(
            model_id=ModelId(name=model1.name, owner=mm.wallet.address),
            base_path=temp_dir,
        )
        model1.check_against(temp_dir)
        model1.check_paths(paths)

    model1.delete()


def test_uploading_model_twice_and_downloading_again_should_give_latest_version(
    fund_account: FixtureType,
) -> None:
    model_name = "model1"
    original_model = TemporaryModel(
        name=model_name,
        files_dict={
            "file1": "This is a mock model file. Henlo.",
            "file2": "This is another file.",
        },
    ).create()

    upload_model(original_model)

    updated_model = TemporaryModel(
        name=model_name,
        files_dict={
            "file1": "This is an updated mock model file. Henlo.",
            "file2": "This is another file.",
            "file3": "This is a new file.",
        },
    ).create()

    mm = upload_model(updated_model)

    # mine a block in arlocal to make the model available for download
    mine_block()

    with tempfile.TemporaryDirectory() as temp_dir:
        paths = mm.download_model(
            model_id=ModelId(name=model_name, owner=mm.wallet.address),
            base_path=temp_dir,
        )
        updated_model.check_against(temp_dir)
        updated_model.check_paths(paths)
        # assert that the same check against original model fails
        try:
            original_model.check_against(temp_dir)
            original_model.check_paths(paths)
            assert False
        except AssertionError:
            pass

    original_model.delete()
    updated_model.delete()


def test_versioned_model_download(fund_account: FixtureType) -> None:
    model_name = "model1"
    versioned_model = TemporaryModel(
        name=model_name,
        files_dict={
            "file1": "This is a mock model file. Henlo.",
            "file2": "This is another file.",
        },
    ).create()

    mm = upload_model(
        versioned_model,
        version_mapping={
            "file1": "1.0.0",
            "file2": "1.0.0",
        },
    )

    latest_model = TemporaryModel(
        name=model_name,
        files_dict={
            "file1": "This is an updated mock model file. Henlo.",
            "file2": "This is another file.",
            "file3": "This is a new file.",
        },
    ).create()
    upload_model(latest_model)

    with tempfile.TemporaryDirectory() as temp_dir:
        latest_file = mm.download_model_file(
            model_id=ModelId(name=model_name, owner=mm.wallet.address),
            file_name="file1",
            base_path=temp_dir,
        )

        latest_model.check_against_file(latest_file)

        versioned_file = mm.download_model_file(
            model_id=ModelId(name=model_name, owner=mm.wallet.address),
            file_name="file1",
            version="1.0.0",
            base_path=temp_dir,
        )
        versioned_model.check_against_file(versioned_file)

        # assert that versioned file isn't in the latest model
        try:
            latest_model.check_against_file(versioned_file)
            assert False
        except AssertionError:
            pass

        # assert that the latest file is not in the versioned model
        try:
            versioned_model.check_against_file(latest_file)
            assert False
        except AssertionError:
            pass

    versioned_model.delete()
    latest_model.delete()


def test_download_model_file(fund_account: FixtureType) -> None:
    model = TemporaryModel(
        name="model1",
        files_dict={
            "file1": "This is a mock model file. Henlo.",
            "file2": "This is another file.",
        },
    ).create()

    mm = upload_model(model)

    for file in model.files_dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = mm.download_model_file(
                model_id=ModelId(name=model.name, owner=mm.wallet.address),
                file_name=file,
                base_path=temp_dir,
            )
            model.check_against_file(file_path)

    model.delete()


def test_download_model_using_string_id(fund_account: FixtureType) -> None:
    model = TemporaryModel(
        name="model1",
        files_dict={
            "file1": "This is a mock model file. Henlo.",
            "file2": "This is another file.",
        },
    ).create()

    mm = upload_model(model)

    # download entire model
    with tempfile.TemporaryDirectory() as temp_dir:
        paths = mm.download_model(
            model_id=f"{mm.wallet.address}/{model.name}",
            base_path=temp_dir,
        )
        model.check_against(temp_dir)
        model.check_paths(paths)

    # download a specific file
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = mm.download_model_file(
            model_id=f"{mm.wallet.address}/{model.name}",
            file_name="file1",
            base_path=temp_dir,
        )
        model.check_against_file(file_path)

    model.delete()
