@echo off

REM Read Python path from file
cd /d "%~dp0"
set /p PYTHON_PATH=<python_path.txt

echo Starting data processing
echo Please wait until the Database Interface window opens...

"%PYTHON_PATH%" -m scripts.database_interface

echo Database interface closed.
pause
