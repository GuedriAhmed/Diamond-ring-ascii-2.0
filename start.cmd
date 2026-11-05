@echo off
setlocal
cd /d "%~dp0"
title ASCII Diamond Ring - Setup

rem Use an existing supported Python installation when possible.
set "PYTHON_EXE="
set "PYTHON_ARGS="
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -c "import sys" >nul 2>nul && (set "PYTHON_EXE=py" & set "PYTHON_ARGS=-3.12" & goto python_ready)
    py -3.11 -c "import sys" >nul 2>nul && (set "PYTHON_EXE=py" & set "PYTHON_ARGS=-3.11" & goto python_ready)
    py -3.10 -c "import sys" >nul 2>nul && (set "PYTHON_EXE=py" & set "PYTHON_ARGS=-3.10" & goto python_ready)
)
where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul && (set "PYTHON_EXE=python" & goto python_ready)
)

echo Python 3.10 or newer was not found. Trying to install Python 3.12 with winget...
where winget >nul 2>nul
if errorlevel 1 (
    echo winget is unavailable. Install Python 3.10 or newer, then run this file again.
    goto failed
)
winget install --id Python.Python.3.12 --exact --silent --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
    echo Python installation did not complete. Install Python 3.10 or newer, then run this file again.
    goto failed
)

rem The installer may not refresh this command window's PATH, so check common install paths too.
where py >nul 2>nul
if not errorlevel 1 py -3.12 -c "import sys" >nul 2>nul && (set "PYTHON_EXE=py" & set "PYTHON_ARGS=-3.12" & goto python_ready)
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PYTHON_EXE if exist "%ProgramFiles%\Python312\python.exe" set "PYTHON_EXE=%ProgramFiles%\Python312\python.exe"
if not defined PYTHON_EXE (
    echo Python was installed, but this window could not find it. Close this window and run start.cmd again.
    goto failed
)

:python_ready
echo Setting up the animation's required packages...
if not exist ".venv\Scripts\python.exe" (
    "%PYTHON_EXE%" %PYTHON_ARGS% -m venv .venv
    if errorlevel 1 (
        echo Could not create the project's virtual environment.
        goto failed
    )
)
set "APP_PYTHON=%~dp0.venv\Scripts\python.exe"
"%APP_PYTHON%" -m ensurepip --upgrade >nul 2>nul
"%APP_PYTHON%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo Could not install the required packages. Check your internet connection and try again.
    goto failed
)

echo Starting the diamond ring animation...
title ASCII Diamond Ring
"%APP_PYTHON%" diamond_ring.py
if errorlevel 1 goto failed
goto done

:failed
echo.
pause
:done
endlocal
