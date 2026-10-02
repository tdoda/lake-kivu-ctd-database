@echo off
setlocal EnableDelayedExpansion

REM ============================================================
REM Lake Kivu CTD Database Launcher
REM ============================================================

REM Move to project root
cd /d "%~dp0"

set "PYTHON_PATH_FILE=%~dp0python_path.txt"
set "PYTHON_PATH="
set "CANDIDATE_FILE=%TEMP%\lake_kivu_python_candidates.txt"


REM ============================================================
REM 1. CHECK SAVED PYTHON PATH
REM ============================================================

if exist "%PYTHON_PATH_FILE%" (

    set /p SAVED_PYTHON=<"%PYTHON_PATH_FILE%"

    REM --------------------------------------------------------
    REM Check that the saved path exists and is a file
    REM --------------------------------------------------------

    if exist "!SAVED_PYTHON!" (

        if not exist "!SAVED_PYTHON!\*" (

            set "PYTHON_PATH=!SAVED_PYTHON!"

            echo Using saved Python environment:
            echo !PYTHON_PATH!
            echo.

        ) else (

            echo The saved Python path is a directory, not a Python executable.
            echo.

        )

    ) else (

        echo The saved Python executable was not found.
        echo.

    )
)


REM ============================================================
REM 2. START DIRECTLY IF SAVED PATH IS VALID
REM ============================================================

if defined PYTHON_PATH goto START_DATABASE


REM ============================================================
REM 3. FIND PYTHON ENVIRONMENTS
REM ============================================================

echo Searching for Python environments...
echo.


REM ------------------------------------------------------------
REM Create clean temporary candidate file
REM ------------------------------------------------------------

if exist "%CANDIDATE_FILE%" del "%CANDIDATE_FILE%"


REM ============================================================
REM 3A. PYTHON AVAILABLE THROUGH PATH
REM ============================================================

for /f "delims=" %%P in ('where python 2^>nul') do (

    if exist "%%P" (

        if not exist "%%P\*" (
            echo %%P>>"%CANDIDATE_FILE%"
        )

    )
)


REM ============================================================
REM 3B. CONDA ENVIRONMENTS
REM ============================================================

where conda >nul 2>&1

if not errorlevel 1 (

    REM --------------------------------------------------------
    REM Conda base environment
    REM --------------------------------------------------------

    for /f "delims=" %%P in ('conda info --base 2^>nul') do (

        if exist "%%P\python.exe" (
            echo %%P\python.exe>>"%CANDIDATE_FILE%"
        )

    )


    REM --------------------------------------------------------
    REM Other Conda environments
    REM --------------------------------------------------------

    for /f "tokens=1,*" %%A in (
        'conda env list 2^>nul ^| findstr /r /v "^#"'
    ) do (

        if not "%%B"=="" (

            if exist "%%B\python.exe" (
                echo %%B\python.exe>>"%CANDIDATE_FILE%"
            )

        )
    )
)


REM ============================================================
REM 4. REMOVE DUPLICATES
REM ============================================================

if exist "%CANDIDATE_FILE%" (

    sort "%CANDIDATE_FILE%" /unique > "%CANDIDATE_FILE%.tmp"

    move /y "%CANDIDATE_FILE%.tmp" "%CANDIDATE_FILE%" >nul
)


REM ============================================================
REM 5. COUNT PYTHON CANDIDATES
REM ============================================================

set COUNT=0

if exist "%CANDIDATE_FILE%" (

    for /f "delims=" %%P in (%CANDIDATE_FILE%) do (
        set /a COUNT+=1
    )

)


REM ============================================================
REM 6. NO PYTHON FOUND
REM ============================================================

if "%COUNT%"=="0" (

    echo No Python executable was found automatically.
    echo.
    echo Please enter the full path to your Python executable.
    echo.

    goto MANUAL_PYTHON_NONE
)


REM ============================================================
REM 7. EXACTLY ONE PYTHON FOUND
REM ============================================================

if "%COUNT%"=="1" (

    for /f "delims=" %%P in (%CANDIDATE_FILE%) do (
        set "PYTHON_PATH=%%P"
    )

    echo One Python executable was found:
    echo.
    echo !PYTHON_PATH!
    echo.

    goto SAVE_PYTHON
)


REM ============================================================
REM 8. MULTIPLE PYTHON EXECUTABLES FOUND
REM ============================================================

echo Several Python executables were found.
echo.
echo Please select the Python environment to use:
echo.

set INDEX=0

for /f "delims=" %%P in (%CANDIDATE_FILE%) do (

    set /a INDEX+=1

    set "PYTHON_!INDEX!=%%P"

    echo [!INDEX!] %%P
)


REM ------------------------------------------------------------
REM Manual selection option
REM ------------------------------------------------------------

set /a MANUAL_OPTION=COUNT+1

echo [!MANUAL_OPTION!] Enter a Python path manually
echo.


REM ============================================================
REM 9. SELECT PYTHON
REM ============================================================

:SELECT_PYTHON

set "SELECTION="

set /p SELECTION=Selection:


REM ------------------------------------------------------------
REM Manual option
REM ------------------------------------------------------------

if "!SELECTION!"=="!MANUAL_OPTION!" goto MANUAL_PYTHON


REM ------------------------------------------------------------
REM Check selected candidate
REM ------------------------------------------------------------

set "SELECTED_PYTHON=!PYTHON_%SELECTION%!"

if not defined SELECTED_PYTHON (

    echo.
    echo Invalid selection.
    echo Please enter one of the numbers shown above.
    echo.

    goto SELECT_PYTHON
)


set "PYTHON_PATH=!SELECTED_PYTHON!"

goto SAVE_PYTHON


REM ============================================================
REM 10. MANUAL PYTHON PATH — NO CANDIDATES
REM ============================================================

:MANUAL_PYTHON_NONE

set "PYTHON_PATH="

set /p PYTHON_PATH=Python path:


REM ------------------------------------------------------------
REM Check that path exists
REM ------------------------------------------------------------

if not exist "!PYTHON_PATH!" (

    echo.
    echo The specified path does not exist.
    echo.

    goto MANUAL_PYTHON_NONE
)


REM ------------------------------------------------------------
REM Check that path is a file, not a directory
REM ------------------------------------------------------------

if exist "!PYTHON_PATH!\*" (

    echo.
    echo The specified path is a directory, not a Python executable.
    echo.

    goto MANUAL_PYTHON_NONE
)


goto SAVE_PYTHON


REM ============================================================
REM 11. MANUAL PYTHON PATH — MULTIPLE CANDIDATES
REM ============================================================

:MANUAL_PYTHON

echo.

set "PYTHON_PATH="

set /p PYTHON_PATH=Enter full path to Python executable:


REM ------------------------------------------------------------
REM Check that path exists
REM ------------------------------------------------------------

if not exist "!PYTHON_PATH!" (

    echo.
    echo The specified path does not exist.
    echo.

    goto MANUAL_PYTHON
)


REM ------------------------------------------------------------
REM Check that path is a file, not a directory
REM ------------------------------------------------------------

if exist "!PYTHON_PATH!\*" (

    echo.
    echo The specified path is a directory, not a Python executable.
    echo.

    goto MANUAL_PYTHON
)


goto SAVE_PYTHON


REM ============================================================
REM 12. SAVE PYTHON PATH
REM ============================================================

:SAVE_PYTHON

echo !PYTHON_PATH!>"%PYTHON_PATH_FILE%"

echo.
echo Python environment saved to:
echo %PYTHON_PATH_FILE%
echo.


REM ============================================================
REM 13. START DATABASE INTERFACE
REM ============================================================

:START_DATABASE

echo Starting Lake Kivu CTD database interface...
echo Python: !PYTHON_PATH!
echo.

"!PYTHON_PATH!" -m scripts.database_interface


REM ============================================================
REM 14. CLOSE
REM ============================================================

echo.
echo Database interface closed.

if exist "%CANDIDATE_FILE%" del "%CANDIDATE_FILE%"

pause