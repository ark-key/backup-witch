from src.utils import BashScript


class RcloneCopyFilesScript(BashScript):
    def __init__(self,
                 source: str,
                 destination: str,
                 backup_dir: str,
                 time_stamp: str,
                 log_file: str,
                 filters: str = '',
                 additional_rclone_flags: str = ''):
        code = f'''
        rclone copy "{source}" "{destination}" \
        --backup-dir "{backup_dir}/{time_stamp}" \
        --links \
        {filters} \
        {additional_rclone_flags}\
        2>&1 \
        | tee "{log_file}"
        '''
        super().__init__('rclone-copy-files', code)
