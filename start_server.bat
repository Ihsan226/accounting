@echo off
setlocal
REM Ensure we run Django with the workspace virtual environment
set VENV_DIR=%~dp0env
set VENV_PY=%VENV_DIR%\Scripts\python.exe

if exist "%VENV_PY%" (
	echo Using virtualenv Python: %VENV_PY%
	"%VENV_PY%" manage.py runserver
) else (
	echo Virtualenv not found at %VENV_DIR%. Running with system Python.
	python manage.py runserver
)
endlocal
