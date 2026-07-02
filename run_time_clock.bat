@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
	start /B "" ".venv\Scripts\pythonw.exe" time_clock_gui.py
) else (
	start /B "" pythonw time_clock_gui.py
)
