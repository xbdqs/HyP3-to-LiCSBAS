@echo off
setlocal
python check_env.py
if errorlevel 1 exit /b 1
set /p INPUT=HyP3 ZIP root: 
set /p OUTPUT=Plan output directory: 
if "%INPUT%"=="" exit /b 1
if "%OUTPUT%"=="" exit /b 1
python hyp3lics.py plan -i "%INPUT%" -o "%OUTPUT%"
pause
