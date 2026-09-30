"""Construye el ZIP portable de Servitotal para Windows de 64 bits a partir del instalador ya construido.

El ZIP no lleva ningún ejecutable propio ni .bat: «Servitotal.exe» es el pythonw.exe incluido en el instalador
(firmado por Python Software Foundation) con otro nombre, y un archivo python312._pth hace que ese Python use sólo
sus propias carpetas. Así Windows no lo trata como un programa desconocido."""
from pathlib import Path
import hashlib
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile


RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
VERSION = "1.7.2"
EXE = RAIZ / "instaladores/Servitotal-Windows-x64.exe"
SALIDA = RAIZ / f"instaladores/Servitotal-{VERSION}-Windows-portable.zip"
NOMBRE = f"Servitotal-{VERSION}"
FIJA = (2026, 9, 29, 0, 0, 0)     # metadatos fijos: el mismo código produce el mismo ZIP

# Rutas de Python dentro de la carpeta; también activa el modo aislado (sin PYTHONPATH ni paquetes del usuario).
PTH = "Lib\nDLLs\napp\nimport site\n"

LEEME = f"""SERVITOTAL {VERSION} — WINDOWS 10 Y 11 DE 64 BITS (SIN INSTALAR)

1. Antes de extraer: clic derecho sobre el ZIP > Propiedades > marque
   «Desbloquear» (si aparece) > Aceptar.
2. Clic derecho sobre el ZIP > Extraer todo. Puede extraerlo en Documentos.
3. Abra la carpeta {NOMBRE} y haga doble clic en Servitotal.exe.

Servitotal.exe es el Python oficial (firmado por Python Software Foundation)
que abre el programa: no hace falta instalar nada ni desactivar protecciones.
Para tenerlo a mano: clic derecho en Servitotal.exe > Mostrar más opciones >
Enviar a > Escritorio (crear acceso directo).

Conserve la carpeta completa. Los datos se guardan en %LOCALAPPDATA%\\Servitotal,
igual que con el instalador, así que no se pierden al cambiar de versión.
La primera vez, si encuentra los datos de la versión anterior (agencia.db en
el Escritorio, Documentos o Descargas), el programa ofrece traerlos. También
puede traerlos con Ctrl+Shift+B > «Traer datos de otra carpeta…».

Si no abre, haga doble clic en Diagnosticar Servitotal.exe: muestra el error
en una ventana. Los fallos también se guardan en
%LOCALAPPDATA%\\Servitotal\\errores_inicio.log.

Este ZIP no incluye registros reales, bases, contratos ni respaldos.
Origen: https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara
"""

NECESARIOS = ("Servitotal.exe", "Diagnosticar Servitotal.exe", "python312.dll", "python3.dll", "vcruntime140.dll",
              "vcruntime140_1.dll", "python312._pth", "Lib/sitecustomize.py", "Lib/os.py", "DLLs/_tkinter.pyd",
              "DLLs/_sqlite3.pyd", "tcl/tcl8.6/init.tcl", "tcl/tk8.6/tk.tcl", "app/agencia.py",
              "app/contratos_servitotal.py", "app/abrir_portable.pyw", "app/logo.png", "app/icono.ico")


def firmado(ruta):
    """True si el PE lleva una firma Authenticode (entrada 4 del directorio de datos)."""
    datos = ruta.read_bytes()
    pe = struct.unpack_from("<I", datos, 0x3C)[0]
    opcional = pe + 24
    directorios = opcional + (112 if struct.unpack_from("<H", datos, opcional)[0] == 0x20B else 96)
    return struct.unpack_from("<II", datos, directorios + 8 * 4)[1] > 0


def main():
    herramienta = shutil.which("7zz") or shutil.which("7z")
    if not herramienta:
        raise RuntimeError("Necesita 7-Zip (7zz o 7z) para leer el instalador")
    with tempfile.TemporaryDirectory(prefix="servitotal-portable-") as temporal:
        temporal = Path(temporal)
        extraido = temporal / "extraido"
        subprocess.run([herramienta, "x", "-y", "-o" + str(extraido), str(EXE)], check=True, capture_output=True)
        payload = extraido / "$_13_"
        carpeta = temporal / NOMBRE
        shutil.copytree(payload / "runtime", carpeta)
        (carpeta / "pythonw.exe").rename(carpeta / "Servitotal.exe")
        (carpeta / "python.exe").rename(carpeta / "Diagnosticar Servitotal.exe")
        shutil.copytree(payload / "app", carpeta / "app")
        (carpeta / "app/iniciar.pyw").unlink()          # es el arranque del instalador
        for nombre in ("agencia.py", "contratos_servitotal.py", "logo.png", "icono.png", "icono.ico"):
            if (carpeta / "app" / nombre).read_bytes() != (RAIZ / nombre).read_bytes():
                raise RuntimeError("El instalador no corresponde a la fuente actual: " + nombre)
        shutil.copy2(AQUI / "abrir_portable.pyw", carpeta / "app/abrir_portable.pyw")
        shutil.copy2(AQUI / "arranque_portable.py", carpeta / "Lib/sitecustomize.py")
        (carpeta / "python312._pth").write_bytes(PTH.replace("\n", "\r\n").encode("ascii"))
        (carpeta / "LEEME-ABRIR.txt").write_bytes(LEEME.replace("\n", "\r\n").encode("utf-8-sig"))
        for relativa in NECESARIOS:
            if not (carpeta / relativa).is_file():
                raise RuntimeError("Falta en el paquete: " + relativa)
        for archivo in carpeta.rglob("*"):
            if archivo.is_symlink():
                raise RuntimeError("No se admiten enlaces en el paquete")
            sufijo = archivo.suffix.lower()
            if archivo.is_file() and sufijo in (".db", ".sqlite", ".sqlite3", ".log", ".csv", ".xlsx", ".pdf", ".bat",
                                                ".cmd", ".ps1", ".vbs", ".js", ".lnk"):
                raise RuntimeError("El paquete no debe contener: " + archivo.name)
            if archivo.is_file() and sufijo in (".exe", ".dll", ".pyd") and not firmado(archivo):
                raise RuntimeError("Binario sin firma en el paquete: " + str(archivo.relative_to(carpeta)))
        nuevo = temporal / SALIDA.name
        with zipfile.ZipFile(nuevo, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as paquete:
            for archivo in sorted(carpeta.rglob("*")):
                if archivo.is_file():
                    info = zipfile.ZipInfo(str(archivo.relative_to(temporal)).replace("\\", "/"), date_time=FIJA)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    paquete.writestr(info, archivo.read_bytes(), compresslevel=6)
        with zipfile.ZipFile(nuevo) as paquete:
            if paquete.testzip() is not None:
                raise RuntimeError("Fallo de integridad del ZIP")
            if any(not n.isascii() for n in paquete.namelist()):
                raise RuntimeError("Los nombres del ZIP deben ser ASCII para el extractor de Windows")
        shutil.copy2(nuevo, SALIDA)
    print(f"ZIP creado: {SALIDA.name} ({SALIDA.stat().st_size} bytes)")
    print("SHA256: " + hashlib.sha256(SALIDA.read_bytes()).hexdigest())


if __name__ == "__main__":
    sys.exit(main())
