@echo off
setlocal
echo ============================================================
echo HyP3-to-LiCSBAS v1.0.1 - Windows setup
echo Core installation does NOT require Matplotlib.
echo ============================================================
where conda >nul 2>&1
if errorlevel 1 (
  echo Conda was not found in PATH.
  echo Use a Python 3.10+ environment and run:
  echo   python -m pip install -r requirements-core.txt
  exit /b 1
)

call conda create -n hyp3lics python=3.11 pip -y
if errorlevel 1 exit /b 1
call conda activate hyp3lics
python -m pip install --upgrade pip
python -m pip install -r requirements-windows-known-good.txt
if errorlevel 1 exit /b 1

echo.
echo Optional prettier network plot:
echo   python -m pip install -r requirements-plot.txt
echo This is NOT required; a stdlib PNG fallback is built in.
echo.
python check_env.py
pause
