"""Shared filesystem paths for Time Clock."""

from pathlib import Path
import os
import shutil
import sys


APP_NAME = "Time Clock"
DATA_FILENAME = "time_clock_data.json"
BACKUP_FOLDER_NAME = "Backup Data"


def get_app_storage_dir() -> Path:
    """Return the writable per-user storage directory."""
    base_dir = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base_dir:
        return Path(base_dir) / APP_NAME
    return Path.home() / APP_NAME


def get_backup_dir() -> Path:
    """Return the directory used for backup files."""
    backup_dir = get_app_storage_dir() / BACKUP_FOLDER_NAME
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def get_legacy_data_file_path() -> Path:
    """Return the old local data file path beside the app entry point."""
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parent
    return base_dir / DATA_FILENAME


def get_data_file_path() -> str:
    """Return the active data file path, migrating legacy data if present."""
    storage_dir = get_app_storage_dir()
    storage_dir.mkdir(parents=True, exist_ok=True)

    data_file = storage_dir / DATA_FILENAME
    if not data_file.exists():
        legacy_data_file = get_legacy_data_file_path()
        if legacy_data_file.exists():
            try:
                shutil.copy2(legacy_data_file, data_file)
            except OSError:
                pass

    return str(data_file)