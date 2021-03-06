<h1 align="center" style="border-bottom: none;">backup-witch</h1>
<h3 align="center">rclone backup automation tool</h3>

<p align="center">
  <a href="https://lgtm.com/projects/g/ark-key/backup-witch/context:python">
    <img alt="Language grade: Python" src="https://img.shields.io/lgtm/grade/python/g/ark-key/backup-witch.svg?logo=lgtm&logoWidth=18"/>
  </a>
  <a href="https://codecov.io/gh/ark-key/backup-witch">
    <img src="https://codecov.io/gh/ark-key/backup-witch/branch/master/graph/badge.svg?token=2A648Z07NO"/>
  </a>
  <img src="https://github.com/ark-key/backup-witch/actions/workflows/flake8.yml/badge.svg"/>
  <img src="https://github.com/ark-key/backup-witch/actions/workflows/pytest.yml/badge.svg"/>
  <img src="https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue"/>
  <a href="https://github.com/psf/black">
    <img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg">
  </a>
  <a href="https://pycqa.github.io/isort/">
    <img alt="Imports: isort" src="https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336">
  </a>
</p>

**backup-witch** is an ultimate tool for performing continuous automated backup and synchronization of data with **rclone**.

Made with **python** and **bash**.

## Features

- uses [rclone](https://rclone.org/)
- compatible with any [cloud storage provider](https://rclone.org/overview/#features) supported by rclone
- [top-up sync strategy](https://forum.rclone.org/t/strageties-for-speeding-up-rclone-sync-times/20588/10)
- pre-backup and post-backup hooks
- interval run scheduling or run scheduling with tool of your choice (e.g. cron, fcron)
- full control over rclone configuration ([flags](https://rclone.org/flags/), [filters](https://rclone.org/filtering/))
- rclone _[--backup-dir](https://rclone.org/docs/#backup-dir-dir)_ as backup mechanism

## How it works

**backup-witch** operates with backup source, i.e. source of backup, and backup destination.

On backup destination **backup-witch** creates two folders: latest and previous. _latest_ - is the backup source synced to the backup destination (the latest snapshot of data). _previous_ - is the folder, where previous version of files, as well as deleted files, reside.

Additionally, you can provide **backup-witch** a list of pre-backup and post-backup _hooks_. A _hook_ should be a callable python object or function, which performs a certain action. **backup-witch** ships with one such hook, which saves a list of installed apps (useful for system recovery, more about it in [Plugins](#plugins) section).

## Dependencies

+ python3
+ bash
+ rclone

## System requirements

Any system, that supports the dependencies.

## Prerequisites

You will need to have a properly configured rclone remote to serve as backup destination.

More info -> https://rclone.org/docs/

## How to run

### Configure

To run **backup-witch**, first cd into *src* folder and create **config.py** configuration file from _config.example.py_

```shell
cd src
cp config.example.py config.py
```

Now edit config.py with your preferred text editor and configure **backup-witch** according to your needs. All available configuration options are listed in [Settings](#settings) section of readme. 

Alternatively, you can use python package with name _config_, if you have complex configuration which you want to divide into several files.

### Running as systemd service

To run **backup-witch** as **systemd** service use provided utility script _systemd-init.sh_

It will create a backup-witch.service in _~/.config/systemd/user/_, creating any required dirs automatically.

After that enable backup-witch.service

```shell
systemctl --user enable backup-witch.service
```

And start it

```shell
systemctl --user start backup-witch.service
```

### Running manually

_systemd-init.sh_ sets PYTHONPATH for backup-witch.service to **backup-witch** app folder.

It is also automatically set, if running from **PyCharm IDE**.

You will have to set PYTHONPATH to **backup-witch** app folder yourself, if you want to run **backup-witch**, for example, from terminal.

Use _main.py_ to run **backup-witch**.

## Settings

All settings are processed and have their defaults defined in _src/settings.\_\_init\_\_.py_. Refer to this file in case of uncertainty.

- BACKUP_SOURCE - source argument for rclone
- BACKUP_DESTINATION - backup destination, where _latest_ and _previous_ folders to be created
- BACKUP_INTERVAL - backup interval, specified in seconds, value should be >= 1; alternatively set this to None, to run **backup-witch** in _oneshot mode*_
    > **oneshot** mode makes backup-witch run once and exit, use this if you don't want to use built-in interval runner, and instead want to use an external run scheduler like **cron**, **anacron** or **fcron**
- NO_TRAVERSE_MAX_AGE - specified in seconds
  > **backup-witch** uses **--no-traverse** rclone flag to speedup data transfer; on each run **backup-witch** computes how much time have passed since the last backup, this setting specifies the maximum allowed amount of time passed with which to use **--no-traverse** flag, i.e. if since the last **backup-witch** run have passed more time than NO_TRAVERSE_MAX_AGE, than **--no-traverse** flag will not be used with **rclone copy**
- RCLONE_FILTER_FLAGS_LIST - list of rclone filter flags, e.g. "--include", "--exclude", "--filter", "--links" and so on
  > You can supply here **--filter-from** flag. An example rclone filter file for linux home directory is in _docs_ folder
- RCLONE_ADDITIONAL_FLAGS_LIST - list of additional rclone flags like "--fast-list", "--drive-chunk-size", "--transfers" and such.
- BACKUP_WITCH_DATA_FOLDER - path to **backup-witch** data folder, by default this is set to _~/.backup-witch_
- IGNORE_PERMISSION_DENIED_ERRORS_ON_SOURCE - determines whether to ignore permission denied errors on backup source when copying files from backup source to backup destination.
- IGNORE_PARTIALLY_WRITTEN_FILES_UPLOAD_ERRORS - determines whether to ignore errors caused by uploading files, which are being written to
- EXCEPTION_NOTIFY_COMMAND_COMPOSER - an exception notify command composer (function or callable object)
  > if you provide composer, **backup-witch** will call it to create a shell command, which will be run before termination, if error occurs. It should be command which will notify about error in **backup-witch**. Take a look at **notify_send_exception_notify_command_composer** in [Plugins](#plugins) section, for an example composer, which uses **notify-send** to send a notification.
- RCLONE_COPY_FILES_ERROR_HANDLER - custom handler for "rclone copy files" operation*; provide this if you need to handle rclone errors not handled by **backup-witch**
- RCLONE_MATCH_DESTINATION_TO_SOURCE_ERROR_HANDLER - same as previous, but for "rclone match destination to source" operation*
  > "rclone copy files" and "rclone match destination to source" operations are defined in _src/core_
- PRE_BACKUP_HOOKS - a list of pre-backup hooks; hooks are callables which perform operation; pre-backup hooks are run before backup
- POST_BACKUP_HOOKS - same as previous, but run after backup

## Plugins

All plugins are defined in _src/plugins_. Take a look at them in case of uncertainty.

**backup-witch** ships with two plugins:
  1. **notify_send_exception_notify_command_composer** - can be supplied to **backup-witch** as exception notify command composer, if you are running **backup-witch** on desktop system and have **notify-send** installed (Ubuntu Desktop have it by default, for example).
  2. **SaveListOfInstalledAppsHook** - can be supplied to **backup-witch** as pre-backup hook to create a list of installed apps (apt, snap, flatpak) before backup. This file can later be used during restore process to install all apps, that were present on system (be sure to have it included in backup).

Example usage can be viewed in _config.example.py_
