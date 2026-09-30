@echo off
setlocal
cd /d "%~dp0" || goto carpeta_error
for %%F in (agencia.py contratos_servitotal.py) do if not exist "%%F" (
  set "FALTA=%%F"
  goto archivo_error
)

set "PY=py"
set "PY_OPCIONES=-3"
set "PYW=pyw"
where py >nul 2>nul
if not errorlevel 1 goto verificar_python
set "PY=python"
set "PY_OPCIONES="
set "PYW=pythonw"
where python >nul 2>nul
if errorlevel 1 goto python_error

:verificar_python
"%PY%" %PY_OPCIONES% -c "import tkinter, sqlite3" >nul 2>nul
if errorlevel 1 goto python_error
"%PY%" %PY_OPCIONES% -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>nul
if errorlevel 1 goto version_error
where "%PYW%" >nul 2>nul
if errorlevel 1 goto abrir_consola
start "" "%PYW%" %PY_OPCIONES% "%~dp0agencia.py"
if errorlevel 1 goto inicio_error
exit /b 0

:abrir_consola
"%PY%" %PY_OPCIONES% "%~dp0agencia.py"
if errorlevel 1 goto inicio_error
exit /b 0

:python_error
echo No se encontro Python 3 con tkinter y sqlite3.
echo Instalelo desde https://www.python.org/downloads/
echo Marque "Add Python to PATH" y deje activado "tcl/tk and IDLE".
echo Tambien puede usar el instalador Servitotal-Windows-x64.exe, que trae su propio Python.
goto fallar
:version_error
echo El Python de este equipo es demasiado antiguo: Servitotal necesita Python 3.8 o posterior.
echo Instale Python 3.12 o posterior desde https://www.python.org/downloads/
echo o use el instalador Servitotal-Windows-x64.exe, que trae su propio Python.
goto fallar
:archivo_error
echo Falta %FALTA% junto a Iniciar.bat.
echo Copie TODOS los archivos de la actualizacion en esta carpeta, no solo agencia.py.
goto fallar
:carpeta_error
echo No se pudo abrir la carpeta del programa.
goto fallar
:inicio_error
echo No se pudo iniciar Servitotal. Revise errores.log en la carpeta de datos.
:fallar
pause
exit /b 1
