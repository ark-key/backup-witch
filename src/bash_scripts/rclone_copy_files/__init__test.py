import pytest

from src.utils.bash_utils import run_bash_script
from src.utils.time_utils import time_stamp
from . import RcloneCopyFilesToDestinationScript


def test(tmp_path):
    source = tmp_path / "source"
    destination_latest = tmp_path / "destination" / "latest"
    destination_previous = tmp_path / "destination" / "previous"
    t_stamp = time_stamp()
    log_file = source / "rclone-copy.log"
    test_file = "test-file.txt"
    filter_flags = f"--include {test_file}"
    additional_rclone_flags = pytest.testenv.RCLONE_FlAGS_STR
    source.mkdir()
    destination_latest.mkdir(parents=True)
    test_file_on_source = source / f"{test_file}"
    test_file_on_destination = destination_latest / f"{test_file}"
    test_file_on_destination_content = "DESTINATION"
    test_file_on_destination.write_text(test_file_on_destination_content)
    test_file_on_source_content = "SOURCE"
    test_file_on_source.write_text(test_file_on_source_content)
    test_file_on_backup_dir = destination_previous / f"{t_stamp}" / f"{test_file}"
    print(test_file_on_backup_dir.__str__())
    run_bash_script(
        RcloneCopyFilesToDestinationScript(
            source=source.__str__(),
            destination=destination_latest.__str__(),
            backup_dir=destination_previous.__str__(),
            time_stamp=t_stamp,
            log_file=log_file.__str__(),
            filter_flags=filter_flags,
            additional_rclone_flags=additional_rclone_flags,
        )
    )
    assert test_file_on_destination.exists()
    assert test_file_on_destination.read_text() == test_file_on_source_content
    assert test_file_on_backup_dir.exists()
    assert test_file_on_backup_dir.read_text() == test_file_on_destination_content
    assert log_file.exists()
    assert log_file.read_text()
