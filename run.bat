@echo off
rem DC Hound: starts the server and opens the app at http://127.0.0.1:8000
rem Extra arguments pass through, e.g.  run.bat --no-ingest   or   run.bat --port 9000
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo No .venv found. Create it first:
  echo   python -m venv .venv
  echo   .venv\Scripts\python -m pip install -r src\requirements.txt
  pause
  exit /b 1
)
set PYTHONPATH=%~dp0
set PYTHONIOENCODING=utf-8
set ARGS=%*
set PORT=8000
:args
if "%~1"=="--port" set PORT=%~2
if not "%~1"=="" (shift & goto args)
start "" /b cmd /c "timeout /t 4 /nobreak >nul & start "" http://127.0.0.1:%PORT%"
".venv\Scripts\python.exe" -m src.server %ARGS%
