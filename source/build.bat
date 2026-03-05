@echo off
echo ========================================
echo Building OpenMicroManipulator to .exe
echo ========================================
echo.

REM Install PyInstaller if not already installed
echo Installing/Updating PyInstaller...
pip install pyinstaller

echo.
echo Starting build process...
echo.

REM Run PyInstaller with the spec file
pyinstaller --clean build.spec

echo.
echo ========================================
echo Build completed!
echo The .exe file is located in: dist\OpenMicroManipulator.exe
echo ========================================
echo.
pause
