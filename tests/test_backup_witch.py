import asyncio
import subprocess
from dataclasses import asdict, dataclass
from glob import glob
from pathlib import Path
from typing import Callable

import pytest

from src.main import main
from src.plugins.pre_backup_hooks.save_list_of_installed_apps import (
    SaveListOfInstalledAppsHook,
)
from src.settings import Configuration


@dataclass
class Paths:
    backup_witch_data_folder: Path
    backup_source: Path
    backup_destination: Path
    backup_destination_latest: Path
    backup_destination_previous: Path


@dataclass
class Utils:
    bootstrap_env: Callable[[Paths], None]
    config: Callable[..., Configuration]
    paths: Callable[[Configuration], Paths]


@pytest.fixture
def utils(tmp_path):
    backup_witch_data_folder = tmp_path / "backup-witch"
    backup_source = tmp_path / "backup_source"
    backup_destination = tmp_path / "backup-destination"

    _cfg = Configuration(
        BACKUP_SOURCE=backup_source.__str__(),
        BACKUP_DESTINATION=backup_destination.__str__(),
        BACKUP_INTERVAL=1,  # seconds
        BACKUP_WITCH_DATA_FOLDER=backup_witch_data_folder.__str__(),
        EXCEPTION_NOTIFY_COMMAND_COMPOSER=None,
        RCLONE_ADDITIONAL_FLAGS_LIST=pytest.testenv.RCLONE_FLAGS_LIST,
    )

    def _bootstrap_env(paths: Paths):
        paths.backup_source.mkdir()
        paths.backup_destination_latest.mkdir(parents=True)
        paths.backup_destination_previous.mkdir(parents=True)

    def _config(**kwargs):
        return Configuration(**{**asdict(_cfg), **kwargs})

    def _paths(cfg: Configuration):
        return Paths(
            backup_witch_data_folder=Path(cfg.BACKUP_WITCH_DATA_FOLDER),
            backup_source=Path(cfg.BACKUP_SOURCE),
            backup_destination=Path(cfg.BACKUP_DESTINATION),
            backup_destination_latest=Path(cfg.BACKUP_DESTINATION_LATEST),
            backup_destination_previous=Path(cfg.BACKUP_DESTINATION_PREVIOUS),
        )

    return Utils(bootstrap_env=_bootstrap_env, config=_config, paths=_paths)


async def test_normal_with_permission_error_ignore(utils):
    config = utils.config(
        RCLONE_FILTER_FLAGS_LIST=["--copy-links"],
    )
    paths = utils.paths(config)
    utils.bootstrap_env(paths)
    symlink_to_root = paths.backup_source / "root"
    symlink_to_root.symlink_to("/root")
    file_on_backup_source_name = "first-file.txt"
    file_on_backup_source = paths.backup_source / file_on_backup_source_name
    file_on_backup_source.touch()
    file_on_backup_source.write_text("first-file")
    # test copy on first run
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(main(config), config.BACKUP_INTERVAL)
    file_on_backup_destination_latest = (
        paths.backup_destination_latest / file_on_backup_source_name
    )
    assert file_on_backup_destination_latest.exists()
    assert (
        file_on_backup_destination_latest.read_text()
        == file_on_backup_source.read_text()
    )
    # test copy on second run, with new file on backup source
    await asyncio.sleep(1)
    second_file_on_source_name = "second-file.txt"
    second_file_on_source = paths.backup_source / second_file_on_source_name
    second_file_on_source.touch()
    second_file_on_source.write_text("second-file")
    second_file_on_destination_latest = (
        paths.backup_destination_latest / second_file_on_source_name
    )
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(main(config), config.BACKUP_INTERVAL)
    assert second_file_on_destination_latest.exists()
    assert (
        second_file_on_destination_latest.read_text()
        == second_file_on_source.read_text()
    )
    # test destination to source matching
    await asyncio.sleep(1)
    glob_result = glob(
        paths.backup_destination_previous.__str__() + "/**", recursive=True
    )
    assert len(glob_result) == 1
    assert glob_result[0] == paths.backup_destination_previous.__str__() + "/"
    file_on_backup_source.unlink()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(main(config), config.BACKUP_INTERVAL)
    assert file_on_backup_destination_latest.exists() is False
    glob_result = glob(
        paths.backup_destination_previous.__str__() + f"/*/{file_on_backup_source_name}"
    )
    assert len(glob_result) == 1
    file_on_destination_previous = Path(glob_result[0])
    assert file_on_destination_previous.name == file_on_backup_source_name


async def test_with_permission_error_respect(utils):
    config = utils.config(
        RCLONE_FILTER_FLAGS_LIST=["--copy-links"],
        IGNORE_PERMISSION_DENIED_ERRORS_ON_SOURCE=False,
    )
    paths = utils.paths(config)
    utils.bootstrap_env(paths)
    symlink_to_root = paths.backup_source / "root"
    symlink_to_root.symlink_to("/root")
    with pytest.raises(subprocess.CalledProcessError):
        await main(config)


async def test_with_no_errors_ignore(utils):
    config = utils.config(
        RCLONE_FILTER_FLAGS_LIST=["--copy-links"],
        IGNORE_PERMISSION_DENIED_ERRORS_ON_SOURCE=False,
        IGNORE_PARTIALLY_WRITTEN_FILES_UPLOAD_ERRORS=False,
    )
    paths = utils.paths(config)
    utils.bootstrap_env(paths)
    symlink_to_root = paths.backup_source / "root"
    symlink_to_root.symlink_to("/root")
    with pytest.raises(subprocess.CalledProcessError):
        await main(config)


async def test_exception_notify_command_composer(utils):
    config = utils.config(
        RCLONE_FILTER_FLAGS_LIST=["--copy-links"],
        IGNORE_PERMISSION_DENIED_ERRORS_ON_SOURCE=False,
    )
    paths = utils.paths(config)
    utils.bootstrap_env(paths)
    output_file_name = "out.txt"
    output_file_path = paths.backup_witch_data_folder / output_file_name
    config.EXCEPTION_NOTIFY_COMMAND_COMPOSER = (
        lambda c: f'echo -n "{c.BACKUP_SOURCE}" > {output_file_path}'
    )
    # we need to remake config object, as __post__init__ in dataclass is run only after __init__
    config = utils.config(**asdict(config))
    symlink_to_root = paths.backup_source / "root"
    symlink_to_root.symlink_to("/root")
    with pytest.raises(subprocess.CalledProcessError):
        await main(config)
    assert output_file_path.exists()
    assert output_file_path.read_text() == config.BACKUP_SOURCE


async def test_invalid_argument_error(utils):
    # covers empty rclone log file case of rclone_log_contains_not_ignored_errors
    config = utils.config(
        RCLONE_FILTER_FLAGS_LIST=["--filter-from />.folder/filter.txt"]
    )
    paths = utils.paths(config)
    utils.bootstrap_env(paths)
    with pytest.raises(subprocess.CalledProcessError):
        await main(config)


async def test_unparseable_rclone_error_handling(utils):
    # covers unparseable rclone error case of rclone_log_contains_not_ignored_errors
    config = utils.config(RCLONE_ADDITIONAL_FLAGS_LIST=["-vv", "--log-level INFO"])
    paths = utils.paths(config)
    utils.bootstrap_env(paths)
    with pytest.raises(subprocess.CalledProcessError):
        await main(config)


async def test_oneshot_runner(utils):
    config = utils.config(
        RCLONE_FILTER_FLAGS_LIST=["--copy-links"],
        BACKUP_INTERVAL=None,
    )
    paths = utils.paths(config)
    utils.bootstrap_env(paths)
    symlink_to_root = paths.backup_source / "root"
    symlink_to_root.symlink_to("/root")
    file_on_backup_source_name = "first-file.txt"
    file_on_backup_source = paths.backup_source / file_on_backup_source_name
    file_on_backup_source.touch()
    file_on_backup_source.write_text("first-file")
    await asyncio.wait_for(main(config), 1)
    file_on_backup_destination_latest = (
        paths.backup_destination_latest / file_on_backup_source_name
    )
    assert file_on_backup_destination_latest.exists()
    assert (
        file_on_backup_destination_latest.read_text()
        == file_on_backup_source.read_text()
    )


def test_backup_interval_invalid_error(utils):
    with pytest.raises(RuntimeError):
        utils.config(
            BACKUP_INTERVAL=-1,
        )
    with pytest.raises(RuntimeError):
        utils.config(
            BACKUP_INTERVAL=0,
        )


def test_prohibited_rclone_flags_error(utils):
    with pytest.raises(RuntimeError):
        utils.config(
            RCLONE_ADDITIONAL_FLAGS_LIST=["--max-age 10s", "--min-age 1s"],
            RCLONE_FILTER_FLAGS_LIST=["--max-age 10s", "--min-age 1s"],
        )


async def test_pre_backup_hooks_run(utils):
    config = utils.config()
    paths = utils.paths(config)
    utils.bootstrap_env(paths)
    apps_list_file = paths.backup_source / "list-of-installed-apps.txt"
    config.PRE_BACKUP_HOOKS = [SaveListOfInstalledAppsHook(apps_list_file.__str__())]
    # we need to remake config object, as __post__init__ in dataclass is run only after __init__
    config = utils.config(**asdict(config))
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(main(config), config.BACKUP_INTERVAL)
    assert apps_list_file.exists()
    assert apps_list_file.read_text()
    apps_list_file.unlink()
    config.PRE_BACKUP_HOOKS = []
    config.POST_BACKUP_HOOKS = [SaveListOfInstalledAppsHook(apps_list_file.__str__())]
    config = utils.config(**asdict(config))  # remake for post_backup_hooks
    with pytest.raises(asyncio.TimeoutError):
        # give more time to run, so that post backup hook could run
        await asyncio.wait_for(main(config), config.BACKUP_INTERVAL * 2)
    assert apps_list_file.exists()
    assert apps_list_file.read_text()
