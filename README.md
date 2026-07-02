# Time Clock Program

A comprehensive time clock application that tracks employee hours and calculates wages based on hourly rates.

## Features

- **Employee Management**: Add employees with unique IDs, names, and hourly rates
- **Clock In/Out**: Track when employees start and finish work
- **Wage Calculation**: Automatically calculate wages based on hours worked and hourly rate
- **Time Entries**: View all time entries with detailed information
- **Wage Reports**: Generate wage summaries for individual employees or all employees
- **Data Persistence**: All data is saved to a JSON file and persists between sessions

## Installation

No installation required! Just make sure you have Python 3.6 or later installed.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Versioning and Updates

The application version is managed in `time_clock_version.py`:

- `APP_VERSION` controls the app version shown in the UI.
- `GITHUB_REPO` enables update checks from GitHub Releases (format: `owner/repo`).

### How update checks work

1. Set `GITHUB_REPO` in `time_clock_version.py`.
2. Create GitHub releases using tags like `v1.1.0`, `v1.2.0`, etc.
3. In the app, use `Help -> Check for Updates`.

If a newer release exists, the app will offer to open the release page.

## Release process

1. Run `bump_version.bat` to increment `APP_VERSION` in `time_clock_version.py`.
2. Commit and push the version bump with your code changes.
3. Build the app and installer with `build_installer.bat`.
4. Run `publish_release.bat` to create the GitHub Release tagged `v<APP_VERSION>`.
5. If the tag already exists, bump the version again before publishing.

## Usage

Run the program:

```bash
python time_clock.py
```

### Menu Options

1. **Add Employee**: Register a new employee with ID, name, and hourly rate
2. **Update Hourly Rate**: Change an employee's hourly rate
3. **Clock In**: Record when an employee starts their shift
4. **Clock Out**: Record when an employee ends their shift (automatically calculates wages)
5. **View Employee Status**: Check if an employee is currently clocked in or out
6. **List All Employees**: Display all registered employees and their status
7. **View Time Entries**: See all time entries (can filter by employee)
8. **Calculate Total Wages**: View total hours and wages (for all or specific employee)
9. **Exit**: Close the program

## Example Workflow

1. **Add an employee**:
   - Choose option 1
   - Enter employee ID: `E001`
   - Enter name: `John Smith`
   - Enter hourly rate: `$25.00`

2. **Clock in**:
   - Choose option 3
   - Enter employee ID: `E001`
   - System records the clock-in time

3. **Clock out**:
   - Choose option 4
   - Enter employee ID: `E001`
   - System calculates hours worked and wages earned

4. **View wage summary**:
   - Choose option 8
   - Press Enter to see all employees or enter specific ID
   - See total hours and wages

## Data Storage

All data is stored in `time_clock_data.json` in the same directory as the program. This file includes:

- Employee records (ID, name, hourly rate, current status)
- Time entries (clock in/out times, hours worked, wages)

## Features Explained

### Wage Calculation

Wages are automatically calculated when an employee clocks out:

```text
Wages = Hours Worked × Hourly Rate
```

### Time Tracking

- Clock-in time is recorded when an employee clocks in
- Clock-out time is recorded when an employee clocks out
- Hours are calculated in decimal format (e.g., 1.5 hours = 1 hour 30 minutes)

### Employee Status

The system prevents:

- Clocking in when already clocked in
- Clocking out when not clocked in
- Duplicate employee IDs

## Tips

- Use consistent employee ID formats (e.g., E001, E002, E003)
- Update hourly rates as needed before clocking out to ensure accurate wage calculation
- Regularly check time entries to verify accuracy
- Back up the `time_clock_data.json` file periodically

## Requirements

- Python 3.6+
- External dependency: `tkcalendar`

## License

Free to use and modify as needed.
