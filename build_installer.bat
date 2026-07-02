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

echo Building Time Clock version %APP_VERSION%

if not exist dist mkdir dist
if not exist build mkdir build

python -m PyInstaller --clean --noconfirm time_clock.spec

if errorlevel 1 (
    echo.
    echo PyInstaller build failed.
    exit /b 1
)

echo.
echo PyInstaller build complete. The packaged app is in the dist folder.

set "ISCC_EXE="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if not defined ISCC_EXE (
    echo.
    echo Inno Setup compiler not found. Skipping installer build.
    echo Install Inno Setup 6 to compile the installer automatically.
    exit /b 0
)

"%ISCC_EXE%" "/DMyAppVersion=%APP_VERSION%" "Time Clock Installer.iss"

if errorlevel 1 (
    echo.
    echo Inno Setup compilation failed.
    exit /b 1
)

echo.
echo Installer build complete. Check installer_output for TimeClockSetup-%APP_VERSION%.exe
endlocal