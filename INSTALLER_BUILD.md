# Windows Installer Build

This project can be packaged into a standard Windows setup installer.

## What it uses

- PyInstaller to freeze the Python GUI into a standalone executable
- Inno Setup to create the final installer

## Prerequisites

Install these on the build machine:

- Python 3
- PyInstaller: `python -m pip install pyinstaller tkcalendar`
- Inno Setup

## Build steps

1. Update `APP_VERSION` in `time_clock_version.py`.
2. Run `build_installer.bat`.
3. The script will:
   - Build the frozen app in `dist`
   - Compile Inno Setup (if installed)
   - Produce `installer_output\TimeClockSetup-<version>.exe`
4. Run `publish_release.bat` to publish the matching GitHub Release tagged `v<APP_VERSION>`.

If Inno Setup is not installed, the script still builds the app and reports that installer compilation was skipped.

## Release notes

The update checker reads GitHub Releases, so each new version should be published as a release with a matching tag like `v1.1.2`.

## Notes

- The app now stores its live data in the user profile under AppData, so it can be installed under Program Files without losing write access.
- Existing `time_clock_data.json` files in the old location will be migrated automatically on first launch if they are present beside the app.
