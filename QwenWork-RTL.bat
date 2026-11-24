@echo off
chcp 65001 >nul
title QwenWork RTL + Vazir
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 goto :python
where py >nul 2>nul
if %errorlevel%==0 goto :py

echo.
echo Python 3 was not found.
echo Install it from https://www.python.org/downloads/windows/
echo and tick "Add python.exe to PATH", then run this file again.
echo.
pause
goto :eof

:python
python "%~dp0qwenwork_rtl.py" %*
goto :eof

:py
py -3 "%~dp0qwenwork_rtl.py" %*
goto :eof
