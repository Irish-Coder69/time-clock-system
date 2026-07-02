@echo off
setlocal

cd /d "%~dp0"

set "APP_VERSION="
for /f "tokens=2 delims==" %%i in ('findstr /b "APP_VERSION" time_clock_version.py') do set "APP_VERSION=%%i"
set "APP_VERSION=%APP_VERSION:"=%"
set "APP_VERSION=%APP_VERSION: =%"

if not defined APP_VERSION (
    set "APP_VERSION=1.0.0"
)

set "TAG=v%APP_VERSION%"
set "INSTALLER=installer_output\TimeClockSetup-%APP_VERSION%.exe"

if not exist "%INSTALLER%" (
    echo Installer not found at %INSTALLER%
    echo Run build_installer.bat first.
    exit /b 1
)

echo Publishing GitHub Release %TAG%

gh release view %TAG% >nul 2>&1
if not errorlevel 1 (
    echo Release already exists. Updating installer asset.
    gh release upload %TAG% "%INSTALLER%" --clobber
    if errorlevel 1 exit /b 1
    echo Release asset updated successfully.
    exit /b 0
)

gh release create %TAG% "%INSTALLER%" --title "Time Clock v%APP_VERSION%" --notes "Time Clock v%APP_VERSION%" --latest
if errorlevel 1 (
    echo.
    echo Failed to create GitHub Release.
    exit /b 1
)

echo.
echo GitHub Release created successfully.
endlocal