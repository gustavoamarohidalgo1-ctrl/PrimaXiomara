"""Comprueba el ZIP portable de Servitotal en un runner Windows efímero de GitHub, como lo usaría la agencia.

Extrae el ZIP en una carpeta con espacios y «ñ», verifica que Servitotal.exe sea el Python firmado por Python
Software Foundation, lo abre con doble clic simulado (sin argumentos), trae los datos de la versión anterior
respondiendo a su aviso, lo abre con variables de otro Python y prueba Diagnosticar Servitotal.exe. Cada apertura
se cierra con el botón de la ventana. No reproduce SmartScreen, el Control inteligente de aplicaciones ni el
antivirus del equipo receptor.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import traceback
import zipfile

from verificar_windows import (IDYES, VERSION, Windows, comprobar_sin_errores, contar, crear_base_anterior,
                               entorno_de_otro_python, ejecutar, huella_publicada, usar_programa)


NOMBRE = f"Servitotal-{VERSION}"
PRUEBA = r'''
import json, os, sqlite3, sys, tkinter
import agencia
r = tkinter.Tk(); r.update()
print("PORTABLE " + json.dumps({
    "aislado": sys.flags.isolated, "ruta": sys.path, "prefijo": sys.prefix, "agencia": agencia.__file__,
    "tcl": os.environ.get("TCL_LIBRARY"), "tk": r.tk.call("info", "patchlevel"), "sqlite": sqlite3.sqlite_version,
    "sitecustomize": sys.modules["sitecustomize"].__file__}))
r.destroy()
'''


def firmas(archivos, evidencia):
    literales = ",".join("'" + str(a).replace("'", "''") + "'" for a in archivos)
    resultado = subprocess.run([
        "pwsh.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-OutputFormat", "Text", "-Command",
        "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue'; "
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
        f"@({literales}) | ForEach-Object {{ $s = Get-AuthenticodeSignature -LiteralPath $_; "
        "[pscustomobject]@{ Archivo=(Split-Path $_ -Leaf); Estado=$s.Status.ToString(); "
        "Editor=$s.SignerCertificate.Subject } } | ConvertTo-Json -Compress"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if resultado.returncode:
        raise RuntimeError("No se pudieron comprobar las firmas: " + resultado.stderr)
    evidencia["firmas"] = json.loads(resultado.stdout.lstrip("﻿"))
    for firma in evidencia["firmas"]:
        if firma["Estado"] != "Valid" or "Python Software Foundation" not in (firma["Editor"] or ""):
            raise RuntimeError("Firma inesperada: " + str(firma))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--evidencia", type=Path, default=Path("evidencia-portable-windows.json"))
    opciones = parser.parse_args()
    pasos = ("archivo", "extraccion", "firmas", "python_aislado", "abrir", "datos_anteriores",
             "entorno_de_otro_python", "diagnostico")
    informe = {"version": VERSION, "plataforma": sys.platform, "fecha_utc": datetime.now(timezone.utc).isoformat(),
               "limite": "No reproduce SmartScreen, el Control inteligente de aplicaciones ni el antivirus real.",
               "pasos": {nombre: {"estado": "no_ejecutado"} for nombre in pasos}}

    def probar(nombre, accion):
        evidencia = informe["pasos"][nombre]
        try:
            accion(evidencia)
            evidencia["estado"] = "correcto"
            return True
        except BaseException:
            evidencia["estado"] = "fallo"
            evidencia["error"] = traceback.format_exc()
            return False

    try:
        if sys.platform != "win32" or os.environ.get("GITHUB_ACTIONS") != "true":
            raise RuntimeError("Ejecute esta prueba sólo en el runner Windows efímero de GitHub")
        paquete_zip = opciones.zip.resolve(strict=True)
        windows = Windows()
        escritorio = windows.carpeta(0x10)

        def comprobar_archivo(evidencia):
            evidencia["sha256"] = hashlib.sha256(paquete_zip.read_bytes()).hexdigest()
            evidencia["sha256_publicado"] = huella_publicada(paquete_zip)
            if evidencia["sha256"] != evidencia["sha256_publicado"]:
                raise RuntimeError("El ZIP no coincide con SHA256SUMS.txt")

        if not probar("archivo", comprobar_archivo):
            return 1
        with tempfile.TemporaryDirectory(prefix="servitotal zip con espacios ñ ", ignore_cleanup_errors=True) as tmp:
            temporal = Path(tmp)
            carpeta = temporal / "Documentos ñ" / NOMBRE
            perfil = temporal / "Usuario prueba Ñ"
            datos = perfil / "Servitotal"
            entorno = {k: v for k, v in os.environ.items() if k not in ("AGENCIA_DATOS", "PYTHONHOME", "PYTHONPATH",
                                                                         "TCL_LIBRARY", "TK_LIBRARY")}
            entorno["LOCALAPPDATA"] = str(perfil)
            exe = carpeta / "Servitotal.exe"
            diagnostico = carpeta / "Diagnosticar Servitotal.exe"

            def extraer(evidencia):
                with zipfile.ZipFile(paquete_zip) as paquete:
                    if paquete.testzip() is not None:
                        raise RuntimeError("El ZIP está dañado")
                    for nombre in paquete.namelist():
                        ruta = PurePosixPath(nombre)
                        if ruta.is_absolute() or ".." in ruta.parts or ruta.parts[0] != NOMBRE or "\\" in nombre:
                            raise RuntimeError("Ruta inesperada en el ZIP: " + nombre)
                        if ruta.suffix.lower() in (".bat", ".cmd", ".ps1", ".vbs", ".js", ".lnk"):
                            raise RuntimeError("El ZIP no debe depender de guiones que Windows bloquea: " + nombre)
                    paquete.extractall(carpeta.parent)
                evidencia["primer_nivel"] = sorted(p.name for p in carpeta.iterdir())
                for necesario in ("Servitotal.exe", "Diagnosticar Servitotal.exe", "python312._pth", "LEEME-ABRIR.txt"):
                    if not (carpeta / necesario).is_file():
                        raise RuntimeError("Falta " + necesario)

            def comprobar_firmas(evidencia):
                firmas([exe, diagnostico, carpeta / "python312.dll", carpeta / "DLLs" / "_tkinter.pyd"], evidencia)

            def python_aislado(evidencia):
                salida = ejecutar([str(diagnostico), "-c", PRUEBA], evidencia, timeout=60, cwd=temporal,
                                  env=entorno_de_otro_python(entorno, temporal))
                linea = next(l for l in salida.stdout.splitlines() if l.startswith("PORTABLE "))
                evidencia["resultado"] = resultado = json.loads(linea[len("PORTABLE "):])
                def dentro(ruta, base):
                    real = lambda r: os.path.normcase(os.path.realpath(r))
                    return real(ruta) == real(base) or real(ruta).startswith(real(base) + os.sep)
                if resultado["aislado"] != 1 or not dentro(resultado["agencia"], carpeta / "app"):
                    raise RuntimeError("El Python portable no está aislado o no usa su propio programa")
                if any(not dentro(r, carpeta) for r in resultado["ruta"]):
                    raise RuntimeError("El Python portable busca módulos fuera de su carpeta: " + str(resultado["ruta"]))
                if not dentro(resultado["tcl"], carpeta / "tcl"):
                    raise RuntimeError("Tcl/Tk no es el incluido: " + str(resultado["tcl"]))

            def abrir(evidencia):
                usar_programa([exe], windows, evidencia, entorno=entorno, cwd=temporal)
                comprobar_sin_errores(datos, evidencia)
                evidencia["datos"] = contar(datos / "agencia.db")
                if any(evidencia["datos"].values()):
                    raise RuntimeError("Un perfil nuevo debe abrir sin registros")
                guardadas = [p for p in carpeta.rglob("*") if p.suffix.lower() in (".db", ".log", ".json")]
                if guardadas:
                    raise RuntimeError("El programa guardó datos junto al código: " + str(guardadas))

            def datos_anteriores(evidencia):
                anterior = escritorio / "Agencia anterior portable" / "agencia.db"
                evidencia["huella_antes"] = crear_base_anterior(anterior)
                usar_programa([exe], windows, evidencia, entorno=entorno, cwd=temporal,
                              respuestas={"Traer los datos de la versión anterior": IDYES,
                                          "Datos recuperados": "unico"})
                comprobar_sin_errores(datos, evidencia)
                evidencia["datos"] = contar(datos / "agencia.db")
                if evidencia["datos"] != {"clientes": 1, "trabajadoras": 1, "colocaciones": 1}:
                    raise RuntimeError("No se trajeron los datos de la versión anterior")
                if hashlib.sha256(anterior.read_bytes()).hexdigest() != evidencia["huella_antes"]:
                    raise RuntimeError("Se modificó la base de la versión anterior")

            def otro_python(evidencia):
                usar_programa([exe], windows, evidencia, entorno=entorno_de_otro_python(entorno, temporal), cwd=temporal)
                comprobar_sin_errores(datos, evidencia)

            def diagnosticar(evidencia):
                usar_programa([diagnostico], windows, evidencia, entorno=entorno, cwd=temporal, entrada="\r\n")
                if not re.search(r"Servitotal termin.{1,3} \(c.{1,3}digo 0\)", evidencia["salida"]):
                    raise RuntimeError("La consola de diagnóstico no informó el cierre")

            if probar("extraccion", extraer):
                probar("firmas", comprobar_firmas)
                probar("python_aislado", python_aislado)
                if probar("abrir", abrir):
                    if probar("datos_anteriores", datos_anteriores):
                        probar("entorno_de_otro_python", otro_python)
                    probar("diagnostico", diagnosticar)
    except BaseException:
        informe["error_general"] = traceback.format_exc()
    finally:
        informe["ok"] = (not informe.get("error_general")
                         and all(paso["estado"] == "correcto" for paso in informe["pasos"].values()))
        opciones.evidencia.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(informe, ensure_ascii=True, indent=2))   # la consola de Windows puede no ser UTF-8
    return 0 if informe["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
