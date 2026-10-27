@echo off
chcp 65001 > nul
title Chat Project - Demarrage
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON=python"
    ) else (
        echo Python n'a pas ete trouve.
        echo Installez Python depuis https://www.python.org/downloads/
        echo Pendant l'installation, cochez "Add Python to PATH".
        pause
        exit /b 1
    )
)

if not exist "backend\.venv\Scripts\python.exe" (
    echo [1/3] Creation de l'environnement Python...
    %PYTHON% -m venv "backend\.venv"
    if errorlevel 1 goto erreur
)

echo [2/3] Installation/verifications des dependances...
"backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
"backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 goto erreur

echo [3/3] Demarrage du chat...
echo Ouvrez http://127.0.0.1:8000 dans votre navigateur.
echo Pour arreter le serveur : Ctrl+C
cd /d "%~dp0backend"
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
exit /b 0

:erreur
echo.
echo Une erreur est survenue. Verifiez que Python est installe et que votre connexion Internet fonctionne.
pause
exit /b 1
