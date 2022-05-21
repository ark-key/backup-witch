import asyncio
import logging
import subprocess

from backup_witch_service import BackupWitchService
from core.state import State
from utils.misc_utils import LoggedException

try:
    from config import CONFIG
except ImportError as err:
    raise RuntimeError('No config found. Check "How to run" section of readme') from err

logging.basicConfig(filename=CONFIG.PYTHON_LOG_FILE, level=logging.WARNING,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


async def main():
    try:
        state = State(CONFIG.STATE_FILE)
        backup_witch_service = BackupWitchService(
            run_interval=CONFIG.LIST_APPS_AND_COPY_FILES_INTERVAL,
            state=state,
            backup_source=CONFIG.BACKUP_SOURCE,
            destination_latest=CONFIG.BACKUP_DESTINATION_LATEST,
            destination_previous=CONFIG.BACKUP_DESTINATION_PREVIOUS,
            rclone_filter=CONFIG.RCLONE_FILTER,
            rclone_copy_log_file=CONFIG.RCLONE_COPY_LOG_FILE,
            rclone_match_log_file=CONFIG.RCLONE_MATCH_LOG_FILE,
            no_traverse_max_age=CONFIG.NO_TRAVERSE_MAX_AGE,
            rclone_additional_flags=CONFIG.RCLONE_FLAGS,
            apps_list_output_file=CONFIG.APPS_LIST_FILE,
            ignore_permission_denied_errors_on_source=CONFIG.IGNORE_PERMISSION_DENIED_ERRORS_ON_SOURCE,
        )
        await backup_witch_service.run()
    except BaseException as e:
        if CONFIG.DEBUG:
            raise e
        if type(e) != LoggedException:
            logging.critical(repr(e))
        subprocess.run(
            f'notify-send "backup_witch" "Exception Occurred\nCheck log -> {CONFIG.PYTHON_LOG_FILE}" -u critical',
            shell=True,
            check=False)
        raise e


if __name__ == '__main__':
    asyncio.run(main())
