@echo off
setlocal
echo ============================================================
echo HyP3-to-LiCSBAS v1.0.1 - Cross-platform core / Windows runner
echo Plot backend: AUTO (Matplotlib/Agg if healthy, stdlib fallback otherwise)
echo ============================================================
python check_env.py
if errorlevel 1 goto :fail

set /p INPUT=HyP3 ZIP root: 
set /p PLAN=Existing PLAN directory: 
set /p OUTPUT=Output directory: 
if "%INPUT%"=="" goto :fail
if "%PLAN%"=="" goto :fail
if "%OUTPUT%"=="" goto :fail

python hyp3lics.py prepare ^
  -i "%INPUT%" ^
  -o "%OUTPUT%" ^
  --plan-dir "%PLAN%" ^
  --extent-mode intersection ^
  --plot-backend auto
if errorlevel 1 goto :fail

echo SUCCESS.
pause
exit /b 0
:fail
echo ERROR. See messages above.
pause
exit /b 1
