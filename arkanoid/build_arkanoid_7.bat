@echo off
setlocal
cd /d %~dp0

python -m pip install --upgrade pip
python -m pip install pyinstaller

pyinstaller --noconfirm --onefile --windowed --name Arkanoid7 arkanoid_7.py

echo.
echo Build complete. The EXE is in dist\Arkanoid7.exe
pause
