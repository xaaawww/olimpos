@echo off
setlocal EnableExtensions
title OlimpOS - Instalador
cd /d "%~dp0"

echo =====================================================================
echo  OLIMPOS - INSTALADOR
echo =====================================================================
echo.
echo  Instala: Visual C++ Redistributable, Python 3.12, Node.js, Git,
echo  Java 17, Android Studio, las librerias de Python (install.txt,
echo  versiones fijas) y las dependencias de los 3 workers (package-lock.json).
echo.
echo  Puede tardar bastante (Android Studio pesa mas de 1 GB).
echo  Si Windows pregunta si permitis cambios, acepta.
echo.
pause

where winget >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] No se encontro "winget". Instala "Instalador de aplicacion"
    echo         desde la Microsoft Store y volve a ejecutar este archivo.
    goto :fin
)

set "WG=winget install -e --silent --accept-source-agreements --accept-package-agreements --id"

echo.
echo [1/4] Instalando programas...
echo ---------------------------------------------------------------------
call :programa Microsoft.VCRedist.2015+.x64 "Visual C++ Redistributable - lo necesita wrangler dev"
call :programa Python.Python.3.12   "Python 3.12"
call :programa OpenJS.NodeJS.LTS    "Node.js"
call :programa Git.Git              "Git"
rem Java 17: el Gradle de la app (8.9) NO anda con el Java 25 que trae
rem Android Studio. En Android Studio hay que elegirlo una vez en Settings -
rem Build Tools - Gradle - Gradle JDK (ver AppMovil\LEEME.md).
call :programa EclipseAdoptium.Temurin.17.JDK "Java 17 (Temurin) - para compilar la app"
call :programa Google.AndroidStudio "Android Studio"

rem Los programas recien instalados todavia no estan en el PATH de esta
rem ventana: se vuelve a leer el PATH del sistema y del usuario.
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')"`) do set "PATH=%%P"

rem Se busca el python.exe real por su ruta: "python" y "py" pueden ser
rem accesos directos de la Microsoft Store que no son Python de verdad.
set "PY="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY="%LOCALAPPDATA%\Programs\Python\Python312\python.exe""
if not defined PY if exist "%ProgramFiles%\Python312\python.exe" set "PY="%ProgramFiles%\Python312\python.exe""
if not defined PY py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12"

echo.
echo [2/4] Instalando librerias de Python (install.txt)...
echo ---------------------------------------------------------------------
if not defined PY (
    echo [ERROR] No se encontro Python. Cerra esta ventana, abri el
    echo         instalador de nuevo y, si sigue fallando, reinicia la PC.
    set "FALLO=1"
) else (
    %PY% -m pip install --upgrade pip --no-warn-script-location
    %PY% -m pip install -r "%~dp0install.txt" --no-warn-script-location
    if errorlevel 1 (set "FALLO=1") else (echo [OK] Librerias de Python instaladas.)
)

echo.
echo [3/4] Instalando dependencias de los workers...
echo ---------------------------------------------------------------------
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se encontro npm ^(Node.js^). Reinicia la PC y volve a
    echo         ejecutar este archivo.
    set "FALLO=1"
) else (
    call :worker ApiWorker
    call :worker ArgosWorker
    call :worker PagosWorker
)

echo.
echo [4/4] Revisando credenciales...
echo ---------------------------------------------------------------------
call :credencial "Aplicaciones\olimpos_gym\neon_credentials.json"
call :credencial "Aplicaciones\olimpos_gym\firebase_credentials.json"
call :credencial "Aplicaciones\olimpos_gym\anthropic_credentials.json"
call :credencial "Aplicaciones\olimpos_gym\openai_credentials.json"
call :credencial "AppMovil\app\google-services.json"

echo.
echo =====================================================================
if defined FALLO (
    echo  TERMINO CON ERRORES. Revisa los mensajes [ERROR] de arriba.
) else (
    echo  LISTO. Todo lo que se puede instalar automaticamente ya esta.
)
echo =====================================================================
echo.
echo  Falta hacer a mano:
echo   - Abrir Android Studio una vez y seguir el asistente "Standard"
echo     (descarga el Android SDK). Despues: File - Open - AppMovil, y en
echo     Settings - Build Tools - Gradle - Gradle JDK elegir Java 17.
echo   - Poner los archivos de credenciales que falten (ver INSTALAR.txt,
echo     PASO 6).
echo.
echo  Para abrir el sistema de empleados: doble clic en abrir_sistema.bat
echo.

:fin
pause
exit /b

rem ---------------------------------------------------------------------
:programa
echo.
echo  - %~2
%WG% %1
rem winget devuelve error tambien cuando el programa ya estaba instalado,
rem asi que se comprueba con "winget list" en vez de mirar el codigo.
rem (Se compara con 0 porque winget devuelve codigos negativos, y
rem "if errorlevel 1" los toma como exito.)
winget list -e --id %1 --accept-source-agreements >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo instalar %~2.
    set "FALLO=1"
) else (
    echo [OK] %~2
)
exit /b

:worker
echo.
echo  - %1
pushd "%~dp0%1"
rem "npm ci" instala exactamente las versiones de package-lock.json.
call npm ci
if errorlevel 1 (
    echo [ERROR] Fallo "npm ci" en %1.
    set "FALLO=1"
) else (
    echo [OK] %1
)
popd
exit /b

:credencial
if exist "%~dp0%~1" (
    echo [OK]     %~1
) else (
    echo [FALTA]  %~1
)
exit /b
