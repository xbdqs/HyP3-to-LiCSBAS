@echo off
setlocal
python check_env.py
if errorlevel 1 exit /b 1
set /p INPUT=HyP3 ZIP root: 
set /p OUTPUT=Preflight output directory: 
if "%INPUT%"=="" exit /b 1
if "%OUTPUT%"=="" exit /b 1
python hyp3lics.py preflight -i "%INPUT%" -o "%OUTPUT%"
pause
