@echo off
setlocal enabledelayedexpansion
title YouTube Shorts Otomasyon

echo.
echo ====================================================
echo    YouTube Shorts Otomasyon - Odysseus
echo ====================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%..\"
set "PYTHON_EXE=%ROOT_DIR%venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [!] venv python bulunamadi, sistem python araniyor...
    set "PYTHON_EXE=python"
)

echo [*] Python: %PYTHON_EXE%

set "MODE=%~1"
if "%MODE%"=="" set "MODE=--once"

echo [*] Mod: %MODE%
echo [*] Cikti: %SCRIPT_DIR%output\
echo.

"%PYTHON_EXE%" "%SCRIPT_DIR%run.py" %MODE%

if %ERRORLEVEL% equ 0 (
    echo.
    echo [OK] Islem basariyla tamamlandi!
    echo [*] Videolar: %SCRIPT_DIR%output\
) else (
    echo.
    echo [X] Bir hata olustu. Loglari kontrol edin:
    echo [*] Loglar: %SCRIPT_DIR%logs\
)

echo.
pause
