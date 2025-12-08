@echo off
REM Start Django server using project virtualenv Python
"%~dp0env\Scripts\python.exe" "%~dp0manage.py" runserver
