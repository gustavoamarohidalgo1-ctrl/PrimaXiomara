"""Construye un ZIP de Servitotal con el runtime del EXE 1.7.1 verificado."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import tempfile
import zipfile


RAIZ = Path(__file__).resolve().parents[2]
EXE = RAIZ / "instaladores/Servitotal-Windows-x64.exe"
SALIDA = RAIZ / "instaladores/Servitotal-1.7.1-Windows-portable.zip"
SHA_EXE = "18b467dca5f9a2c4e64e61fbc75fb938eb21992f4b2d736758e7ccc5f2ab0811"
NOMBRE = "Servitotal-1.7.1"

ABRIR = r'''@echo off
setlocal
cd /d "%~dp0" || goto fallar
if not defined LOCALAPPDATA goto fallar
if not exist "%~dp0runtime\pythonw.exe" goto fallar
if not exist "%~dp0app\abrir_portable.pyw" goto fallar
start "" "%~dp0runtime\pythonw.exe" -I "%~dp0app\abrir_portable.pyw" --datos "%LOCALAPPDATA%\Servitotal"
if errorlevel 1 goto fallar
exit /b 0
:fallar
echo No se pudo iniciar Servitotal.
echo Extraiga TODO el ZIP y abra este archivo desde la carpeta extraida.
echo Si sigue fallando, abra Diagnosticar Servitotal.bat.
pause
exit /b 1
'''

DIAGNOSTICAR = r'''@echo off
setlocal
cd /d "%~dp0" || goto fallar
if not defined LOCALAPPDATA goto fallar
if not exist "%~dp0runtime\python.exe" goto fallar
echo Servitotal: comprobacion del inicio.
echo Esta ventana mostrara los errores si el programa no puede abrirse.
echo Si se abre Servitotal, cierre el programa para terminar esta comprobacion.
"%~dp0runtime\python.exe" -I "%~dp0app\abrir_portable.pyw" --datos "%LOCALAPPDATA%\Servitotal"
set "RESULTADO=%ERRORLEVEL%"
echo.
echo Codigo de salida: %RESULTADO%
pause
exit /b %RESULTADO%
:fallar
echo Falta el Python incluido o la carpeta de datos del usuario.
echo Extraiga TODO el ZIP antes de abrir Servitotal.
pause
exit /b 1
'''

LEEME = """SERVITOTAL 1.7.1 — WINDOWS DE 64 BITS

1. Guarde el ZIP. Clic derecho sobre el ZIP > Extraer todo.
2. Abra la carpeta extraida Servitotal-1.7.1.
3. Doble clic en Abrir Servitotal.bat.

Python y las bibliotecas necesarias estan incluidos. Conserve completa esta
carpeta; puede guardarla, por ejemplo, en Documentos. Abra el programa desde
la carpeta extraida: no abra el BAT dentro de la vista del ZIP.

Los datos se guardan en %LOCALAPPDATA%\\Servitotal, igual que con el instalador.
Si ya usa la version instalada, guarde su trabajo y cierrela antes de abrir
esta version. Los datos de esa carpeta se conservan. Si su version antigua
guardaba agencia.db junto al programa, cree un respaldo en ella y restaurelo
desde el panel de respaldos de esta version. Conserve su carpeta anterior.

Si no abre, use Diagnosticar Servitotal.bat y conserve el texto del error.
Los fallos que alcanzan el lanzador tambien se registran en
%LOCALAPPDATA%\\Servitotal\\errores_inicio.log.

Este ZIP no incluye registros reales, bases, contratos generados ni respaldos.
Es una alternativa de distribucion; Windows o un antivirus todavia pueden
mostrar avisos o bloquearla. No requiere desactivar las protecciones.
Origen: https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara
"""


def main():
    if hashlib.sha256(EXE.read_bytes()).hexdigest() != SHA_EXE:
        raise RuntimeError("El EXE no coincide con el paquete Servitotal 1.7.1 verificado")
    herramienta = shutil.which("7zz") or shutil.which("7z")
    if not herramienta:
        raise RuntimeError("Necesita 7-Zip para extraer el runtime del instalador")
    with tempfile.TemporaryDirectory(prefix="servitotal-portable-") as temporal:
        temporal = Path(temporal)
        extraido = temporal / "extraido"
        subprocess.run([herramienta, "x", "-y", "-o" + str(extraido), str(EXE)],
                       check=True, capture_output=True)
        payload = extraido / "$_13_"
        carpeta = temporal / NOMBRE
        carpeta.mkdir()
        for nombre in ("runtime", "app"):
            shutil.copytree(payload / nombre, carpeta / nombre)
        for nombre in ("agencia.py", "contratos_servitotal.py", "logo.png", "icono.png", "icono.ico"):
            if (carpeta / "app" / nombre).read_bytes() != (RAIZ / nombre).read_bytes():
                raise RuntimeError("El instalador no corresponde a la fuente actual: " + nombre)
        for archivo in carpeta.rglob("*"):
            if archivo.is_symlink():
                raise RuntimeError("No se admiten enlaces en el paquete")
            if archivo.is_file() and archivo.suffix.lower() in (".db", ".sqlite", ".sqlite3", ".log", ".csv", ".xlsx", ".pdf"):
                raise RuntimeError("El paquete contiene un archivo de datos: " + archivo.name)
        shutil.copy2(Path(__file__).with_name("abrir_portable.pyw"), carpeta / "app/abrir_portable.pyw")
        for nombre, contenido in (("Abrir Servitotal.bat", ABRIR), ("Diagnosticar Servitotal.bat", DIAGNOSTICAR)):
            (carpeta / nombre).write_bytes(contenido.replace("\n", "\r\n").encode("ascii"))
        (carpeta / "LEEME-ABRIR.txt").write_bytes(LEEME.replace("\n", "\r\n").encode("utf-8"))
        nuevo = temporal / SALIDA.name
        with zipfile.ZipFile(nuevo, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as paquete:
            for archivo in sorted(carpeta.rglob("*")):
                if archivo.is_file():
                    paquete.write(archivo, str(archivo.relative_to(temporal)))
        with zipfile.ZipFile(nuevo) as paquete:
            if paquete.testzip() is not None:
                raise RuntimeError("Fallo de integridad del ZIP")
        shutil.copy2(nuevo, SALIDA)
    print(f"ZIP creado: {SALIDA.name} ({SALIDA.stat().st_size} bytes)")
    print("SHA256: " + hashlib.sha256(SALIDA.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
