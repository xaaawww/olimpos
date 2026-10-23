@echo off
setlocal
title OlimpOS - Sistema de empleados
cd /d "%~dp0Aplicaciones\olimpos_gym"

rem Siempre con Python 3.12: es el que tiene las librerias de install.txt.
rem ("py" o "python" solos pueden abrir otra version, como la 3.15.)
set "PY="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY="%LOCALAPPDATA%\Programs\Python\Python312\python.exe""
if not defined PY if exist "%ProgramFiles%\Python312\python.exe" set "PY="%ProgramFiles%\Python312\python.exe""
if not defined PY py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12"

if not defined PY (
    echo No se encontro Python 3.12. Ejecuta primero instalar.bat
    pause
    exit /b 1
)

%PY% main.py
if errorlevel 1 pause
