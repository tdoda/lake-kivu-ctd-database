:: UTF-8 characters (accents):
chcp 65001

@echo off
setlocal enabledelayedexpansion

REM Read Python path from file
set /p PYTHON_PATH=<python_path.txt

:: Use script in the same folder as this .bat file (robust for spaces)
:: set "script=%~dp0main_ctd_database.py"

REM Run the Python script
:: "%PYTHON_PATH%" "%script%"
echo Starting data processing
echo Please wait until the Processing Options window opens...
"%PYTHON_PATH%" scripts/main_ctd_database.py

REM Pause the terminal so you can see output
pause
