"""Prueba Servitotal con Python oficial en un runner Windows efímero.

Descarga el instalador oficial, comprueba su huella y firma antes de usarlo,
y abre dos veces el código entregado con datos ficticios fuera del ZIP.
No reproduce SmartScreen, MOTW ni el antivirus del equipo receptor.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import traceback
from urllib.request import urlopen
import uuid
import zipfile

from verificar_windows import Windows, huella_publicada


URL_PYTHON = "https://www.python.org/ftp/python/3.14.7/python-3.14.7-amd64.exe"
SHA_PYTHON = "9d9eb2709ef81bf5cd30db3c2096bdbc4ea10087c22e62f27d356b36f6ae9649"
RAIZ_ZIP = "Servitotal-1.7.2-Python"
ARCHIVOS_ZIP = {
    "Abrir Servitotal.pyw", "Diagnosticar Servitotal.py", "LEEME-INSTALAR.txt",
    "app/agencia.py", "app/contratos_servitotal.py", "app/logo.png",
    "app/icono.png", "app/icono.ico",
}
TITULO = "Agencia de Empleos “Servitotal”"


def extraer_paquete(archivo, destino, evidencia):
    evidencia["sha256"] = hashlib.sha256(archivo.read_bytes()).hexdigest()
    evidencia["sha256_esperado"] = huella_publicada(archivo)
    if evidencia["sha256"] != evidencia["sha256_esperado"]:
        raise RuntimeError("El ZIP no coincide con la entrega de Servitotal preparada")
    esperados = {f"{RAIZ_ZIP}/{ruta}" for ruta in ARCHIVOS_ZIP}
    with zipfile.ZipFile(archivo) as paquete:
        vistos = set()
        archivos = set()
        for pieza in paquete.infolist():
            ruta = PurePosixPath(pieza.filename)
            windows = PureWindowsPath(pieza.filename)
            if (ruta.is_absolute() or windows.drive or windows.is_absolute()
                    or "\\" in pieza.filename or ":" in pieza.filename
                    or any(parte in ("", ".", "..") for parte in pieza.filename.rstrip("/").split("/"))
                    or ruta.parts[0] != RAIZ_ZIP):
                raise RuntimeError("Ruta inesperada en el ZIP: " + pieza.filename)
            identidad = pieza.filename.rstrip("/").casefold()
            if identidad in vistos:
                raise RuntimeError("Entrada duplicada en el ZIP: " + pieza.filename)
            vistos.add(identidad)
            modo = pieza.external_attr >> 16
            if stat.S_ISLNK(modo) or pieza.flag_bits & 1:
                raise RuntimeError("Enlace o archivo cifrado inesperado en el ZIP")
            if pieza.is_dir():
                if pieza.filename.rstrip("/") not in (RAIZ_ZIP, RAIZ_ZIP + "/app"):
                    raise RuntimeError("Carpeta inesperada en el ZIP")
            else:
                if pieza.filename not in esperados:
                    raise RuntimeError("Archivo inesperado en el ZIP: " + pieza.filename)
                archivos.add(pieza.filename)
        if archivos != esperados:
            raise RuntimeError("Al ZIP le faltan archivos del programa")
        if paquete.testzip() is not None:
            raise RuntimeError("El ZIP no supera la comprobación CRC")
        evidencia["archivos"] = sorted(archivos)
        paquete.extractall(destino)
    return destino / RAIZ_ZIP


def descargar_python(destino, evidencia):
    evidencia.update(url=URL_PYTHON, sha256_esperado=SHA_PYTHON)
    huella = hashlib.sha256()
    total = 0
    with urlopen(URL_PYTHON, timeout=60) as respuesta, destino.open("wb") as archivo:
        while True:
            bloque = respuesta.read(1024 * 1024)
            if not bloque:
                break
            total += len(bloque)
            if total > 100 * 1024 * 1024:
                raise RuntimeError("El instalador oficial excede el tamaño esperado")
            archivo.write(bloque)
            huella.update(bloque)
    evidencia.update(bytes=total, sha256=huella.hexdigest())
    if evidencia["sha256"] != SHA_PYTHON:
        raise RuntimeError("El instalador descargado no coincide con la huella oficial fijada")


def firma_oficial(archivo, evidencia):
    literal = str(archivo).replace("'", "''")
    resultado = subprocess.run([
        "pwsh.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-OutputFormat", "Text", "-Command",
        "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue'; "
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
        f"$s = Get-AuthenticodeSignature -LiteralPath '{literal}'; "
        "[pscustomobject]@{ Archivo=(Split-Path $s.Path -Leaf); Estado=$s.Status.ToString(); "
        "Editor=$s.SignerCertificate.Subject } | ConvertTo-Json -Compress"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    evidencia.update(codigo=resultado.returncode, stdout=resultado.stdout, stderr=resultado.stderr)
    if resultado.returncode:
        raise RuntimeError("No se pudo comprobar la firma oficial: " + resultado.stderr)
    firma = json.loads(resultado.stdout.lstrip("\ufeff"))
    evidencia["firma"] = firma
    if firma.get("Estado") != "Valid" or "Python Software Foundation" not in (firma.get("Editor") or ""):
        raise RuntimeError("El instalador de Python no tiene la firma oficial válida esperada")


def instalar_python(instalador, destino, windows, evidencia):
    comando = [str(instalador), "/quiet", "/norestart", "InstallAllUsers=0",
               f"TargetDir={destino}", "Include_launcher=0", "Include_pip=0",
               "Include_test=0", "Include_tcltk=1", "AssociateFiles=0",
               "PrependPath=0", "AppendPath=0", "Shortcuts=0"]
    proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    evidencia["pid_instalador"] = proceso.pid
    try:
        stdout, stderr = proceso.communicate(timeout=240)
        evidencia.update(codigo=proceso.returncode, stdout=stdout.decode("utf-8", "replace"),
                         stderr=stderr.decode("utf-8", "replace"))
        if proceso.returncode:
            raise RuntimeError(f"El instalador oficial terminó con código {proceso.returncode}")
    finally:
        windows.cerrar_prueba(proceso)
        evidencia["proceso_instalador_cerrado"] = True
    piezas = ("python.exe", "pythonw.exe", "python314.dll", "DLLs/_tkinter.pyd")
    evidencia["archivos"] = {ruta: (destino / ruta).is_file() for ruta in piezas}
    if not all(evidencia["archivos"].values()):
        raise RuntimeError("El Python instalado no contiene el runtime completo con Tcl/Tk")
    # Los instaladores actuales pueden incluir Tcl/Tk 9; comprobar la biblioteca real.
    comprobacion = subprocess.run([str(destino / "python.exe"), "-I", "-c",
        "import json, sys, tkinter, sqlite3; r=tkinter.Tk(); "
        "print(json.dumps({'python':sys.version,'tcl':r.tk.call('info','patchlevel'),"
        "'tk':r.tk.call('package','require','Tk'),'sqlite':sqlite3.sqlite_version})); r.destroy()"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    evidencia["comprobacion_runtime"] = {"codigo": comprobacion.returncode,
                                       "stdout": comprobacion.stdout, "stderr": comprobacion.stderr}
    if comprobacion.returncode:
        raise RuntimeError("El Python oficial no pudo abrir Tk: " + comprobacion.stderr)
    evidencia["runtime"] = json.loads(comprobacion.stdout)
    if tuple(int(parte) for parte in evidencia["runtime"]["tk"].split(".")[:2]) < (8, 6):
        raise RuntimeError("El programa necesita Tk 8.6 o posterior")


def abrir_programa(pythonw, carpeta, entorno, windows, evidencia):
    # Sin --datos: esta prueba exige que el lanzador fije la carpeta por sí mismo.
    proceso = subprocess.Popen([str(pythonw), "-I", str(carpeta / "Abrir Servitotal.pyw")],
                               cwd=carpeta, env=entorno)
    evidencia["pid_lanzador"] = proceso.pid
    vistas = []
    try:
        limite = time.monotonic() + 25
        while time.monotonic() < limite:
            vistas = windows.ventanas(windows.descendientes(proceso.pid))
            esperadas = [ventana for ventana in vistas if ventana["titulo"] == TITULO]
            if esperadas:
                evidencia["ventana"] = esperadas[0]
                break
            if proceso.poll() is not None:
                raise RuntimeError(f"El lanzador terminó sin ventana (código {proceso.returncode})")
            time.sleep(0.2)
        else:
            evidencia["ventanas"] = vistas
            raise RuntimeError("El lanzador Python no mostró la ventana de Servitotal")
        time.sleep(2)
        if not any(ventana["titulo"] == TITULO for ventana in windows.ventanas(
                windows.descendientes(proceso.pid))):
            raise RuntimeError("La ventana se cerró durante el arranque")
        evidencia["visible_dos_segundos"] = True
    finally:
        windows.cerrar_prueba(proceso)
        evidencia["proceso_prueba_cerrado"] = True


def comprobar_datos(datos, carpeta, evidencia):
    for nombre in ("errores.log", "errores_inicio.log"):
        archivo = datos / nombre
        if archivo.is_file():
            evidencia[nombre] = archivo.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError("El programa registró un fallo de inicio")
    base = datos / "agencia.db"
    if not base.is_file():
        raise RuntimeError("El lanzador no creó la base en LOCALAPPDATA de prueba")
    inesperadas = list(carpeta.rglob("*.db")) + list(carpeta.rglob("*.sqlite*"))
    evidencia["datos_fuera_del_zip"] = not inesperadas
    if inesperadas:
        raise RuntimeError("El programa guardó una base junto al código")
    # mode=ro impide que esta comprobación cree una base ausente por accidente.
    with closing(sqlite3.connect(base.resolve().as_uri() + "?mode=ro", uri=True)) as conexion:
        evidencia["clientes"] = conexion.execute("select count(*) from clientes").fetchone()[0]
        evidencia["trabajadoras"] = conexion.execute("select count(*) from trabajadoras").fetchone()[0]
    if evidencia["clientes"] or evidencia["trabajadoras"]:
        raise RuntimeError("Se esperaban datos de negocio ficticios vacíos")
    return base


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--evidencia", type=Path, default=Path("evidencia-python-windows.json"))
    opciones = parser.parse_args()
    informe = {"ok": False, "version": "1.7.2", "plataforma": sys.platform,
               "fecha_utc": datetime.now(timezone.utc).isoformat(),
               "limite": "No reproduce SmartScreen ni antivirus del equipo receptor.",
               "datos": "Sólo dos arranques sobre una base ficticia en un perfil temporal.",
               "zip": {}, "python": {}, "firma": {},
               "instalacion": {}, "arranques": []}
    try:
        if sys.platform != "win32" or os.environ.get("GITHUB_ACTIONS") != "true":
            raise RuntimeError("Ejecute esta prueba sólo en un runner Windows efímero de GitHub")
        windows = Windows()
        with tempfile.TemporaryDirectory(prefix="servitotal python prueba ") as temporal:
            raiz = Path(temporal)
            carpeta = extraer_paquete(opciones.zip.resolve(strict=True), raiz / "paquete con espacios", informe["zip"])
            instalador = raiz / "python-3.14.7-amd64.exe"
            descargar_python(instalador, informe["python"])
            firma_oficial(instalador, informe["firma"])
            runtime = raiz / "Python oficial con espacios"
            instalar_python(instalador, runtime, windows, informe["instalacion"])
            entorno = dict(os.environ, LOCALAPPDATA=str(raiz / "Usuario prueba Ñ con espacios"))
            # Evitar que una variable heredada apunte a los datos de otro programa.
            entorno.pop("AGENCIA_DATOS", None)
            datos = Path(entorno["LOCALAPPDATA"]) / "Servitotal"
            if datos.exists():
                raise RuntimeError("La carpeta ficticia debe estar vacía antes del primer arranque")
            primera = {}
            informe["arranques"].append(primera)
            abrir_programa(runtime / "pythonw.exe", carpeta, entorno, windows, primera)
            base = comprobar_datos(datos, carpeta, primera)
            marca = uuid.uuid4().hex
            with closing(sqlite3.connect(str(base))) as conexion, conexion:
                conexion.execute("create table _prueba_python_preservacion (id integer primary key, marca text not null)")
                conexion.execute("insert into _prueba_python_preservacion values (1, ?)", (marca,))
            segunda = {}
            informe["arranques"].append(segunda)
            abrir_programa(runtime / "pythonw.exe", carpeta, entorno, windows, segunda)
            comprobar_datos(datos, carpeta, segunda)
            with closing(sqlite3.connect(base.resolve().as_uri() + "?mode=ro", uri=True)) as conexion:
                conservada = conexion.execute("select marca from _prueba_python_preservacion where id=1").fetchone()
            informe["base_anterior_conservada"] = conservada == (marca,)
            if not informe["base_anterior_conservada"]:
                raise RuntimeError("El segundo arranque no conservó la marca ficticia de la base anterior")
        # Sólo éxito después de cerrar nuestros procesos y retirar todos los archivos temporales.
        informe["limpieza_temporal_completada"] = True
        informe["ok"] = True
    except BaseException:
        informe["ok"] = False
        informe["error"] = traceback.format_exc()
    finally:
        opciones.evidencia.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(informe, ensure_ascii=True, indent=2))   # la consola de Windows puede no ser UTF-8
    return 0 if informe["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
