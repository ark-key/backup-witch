<h1 align="center" style="border-bottom: none;">backup-witch</h1>
<h3 align="center">rclone backup automation tool</h3>

<p align="center">
  <a href="https://lgtm.com/projects/g/ark-key/backup-witch/context:python">
    <img alt="Language grade: Python" src="https://img.shields.io/lgtm/grade/python/g/ark-key/backup-witch.svg?logo=lgtm&logoWidth=18"/>
  </a>
  <a href="https://codecov.io/gh/ark-key/backup-witch">
    <img src="https://codecov.io/gh/ark-key/backup-witch/branch/master/graph/badge.svg?token=2A648Z07NO"/>
  </a>
</p>

**backup-witch** is an easily configurable and extendable tool for performing continuous
automated backup of data with **rclone**.

Made with **python** and **bash**.

## How it works

**backup-witch** operates with backup source, i.e. source of backup, and backup destination.

On backup destination **backup-witch** creates two folders: latest and previous. _latest_ - is the backup source synced
to the backup destination (the latest snapshot of data). _previous_ - is the folder, where previous version of files, as
well as deleted files, reside.

By default, backup source is the user _home_ folder. Because of that, before performing backup **backup-witch**
creates a txt file, containing a list of installed apps (apt, snap,
flatpak). This file can later be used during restore process to install all apps, that were present on system.

## Dependencies

+ bash
+ python3
+ rclone
+ notify-send (for notifying about errors)

## System requirements

Any system, that supports the dependencies.

## Prerequisites

You will need to have a properly configured rclone remote to serve as backup destination.

More info -> https://rclone.org/docs/

## How to run

### Configure

To run **backup-witch**, first copy *sample_configs* folder to *src* folder and rename it to **configs**

```bash
cp -r sample_config src/config
```

Then set appropriate rclone remote as backup destination.

Corresponding config option will be in *src/config/paths.py*.

Set this option to complete path of folder on remote, without trailing slash. For example:

```python
BACKUP_WITCH_DESTINATION = "dropbox:backup-witch" 
```

Now you can modify any other config options you wish to change.

### Plain run

Use _main.py_ to run **backup-witch**.

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
