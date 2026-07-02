@echo off
setlocal

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$path = 'time_clock_version.py';" ^
    "$text = Get-Content -Raw $path;" ^
    "$match = [regex]::Match($text, 'APP_VERSION\s*=\s*\"(?<version>\d+\.\d+\.\d+)\"');" ^
    "if (-not $match.Success) { throw 'APP_VERSION not found.' }" ^
    "$version = $match.Groups['version'].Value;" ^
    "$parts = $version.Split('.') | ForEach-Object { [int]$_ };" ^
    "$parts[2]++;" ^
    "$newVersion = '{0}.{1}.{2}' -f $parts[0], $parts[1], $parts[2];" ^
    "$newText = [regex]::Replace($text, 'APP_VERSION\s*=\s*\"(?<version>\d+\.\d+\.\d+)\"', 'APP_VERSION = \"' + $newVersion + '\"', 1);" ^
    "Set-Content -Path $path -Value $newText -NoNewline;" ^
    "Write-Host ('Bumped version from ' + $version + ' to ' + $newVersion)"

if errorlevel 1 (
    echo Failed to bump version.
    exit /b 1
)

endlocal