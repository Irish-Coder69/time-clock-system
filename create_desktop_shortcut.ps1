# PowerShell script to create a desktop shortcut for Time Clock Program

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Time Clock.lnk"
$AppRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetPath = Join-Path $AppRoot "run_time_clock.bat"
$IconLocation = "C:\Windows\System32\shell32.dll,165"

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $AppRoot
$Shortcut.IconLocation = $IconLocation
$Shortcut.Description = "Time Clock Program with Hourly Wage Tracking"
$Shortcut.Save()

Write-Host "Desktop shortcut created successfully at: $ShortcutPath" -ForegroundColor Green
Write-Host "You can now double-click 'Time Clock' on your desktop to run the program." -ForegroundColor Cyan
