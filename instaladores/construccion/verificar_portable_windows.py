"""Comprueba el ZIP de Servitotal en un runner Windows efímero de GitHub."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
import zipfile

from verificar_windows import Windows


SHA_ZIP = "5405d8c3a2caf7d29fba346f8ffde82c4a810e146ffa09cd3cf1ac5b4bb6b605"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--evidencia", type=Path, default=Path("evidencia-portable-windows.json"))
    opciones = parser.parse_args()
    informe = {"ok": False, "version": "1.7.1", "plataforma": sys.platform,
               "limite": "No reproduce SmartScreen ni antivirus del equipo receptor.",
               "sha256_esperado": SHA_ZIP}
    proceso = None
    windows = None
    try:
        if sys.platform != "win32" or os.environ.get("GITHUB_ACTIONS") != "true":
            raise RuntimeError("Ejecute esta prueba sólo en el runner Windows efímero de GitHub")
        huella = hashlib.sha256(opciones.zip.read_bytes()).hexdigest()
        informe["sha256"] = huella
        if huella != SHA_ZIP:
            raise RuntimeError("El ZIP no coincide con el paquete preparado")
        datos = Path(os.environ["LOCALAPPDATA"]) / "Servitotal"
        if (datos / "agencia.db").exists():
            raise RuntimeError("El runner ya tiene datos; se requiere un perfil de prueba vacío")
        with tempfile.TemporaryDirectory(prefix="servitotal zip con espacios ") as temporal:
            destino = Path(temporal)
            with zipfile.ZipFile(opciones.zip) as paquete:
                if paquete.testzip() is not None:
                    raise RuntimeError("El ZIP está dañado")
                for nombre in paquete.namelist():
                    if Path(nombre).is_absolute() or ".." in Path(nombre).parts:
                        raise RuntimeError("Ruta inesperada en el ZIP")
                paquete.extractall(destino)
            carpeta = destino / "Servitotal-1.7.1"
            ruta_python = str(carpeta / "runtime/python.exe").replace("'", "''")
            ruta_pythonw = str(carpeta / "runtime/pythonw.exe").replace("'", "''")
            firmas = subprocess.run([
                "pwsh.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-OutputFormat", "Text", "-Command",
                "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue'; "
                "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
                f"@('{ruta_python}','{ruta_pythonw}') | ForEach-Object {{ "
                "$s = Get-AuthenticodeSignature -LiteralPath $_; "
                "[pscustomobject]@{ Archivo=(Split-Path $_ -Leaf); Estado=$s.Status.ToString(); "
                "Editor=$s.SignerCertificate.Subject } } | ConvertTo-Json -Compress"],
                cwd=carpeta, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            informe["comprobacion_firmas"] = {"codigo": firmas.returncode, "stdout": firmas.stdout, "stderr": firmas.stderr}
            if firmas.returncode:
                raise RuntimeError("No se pudieron comprobar las firmas: " + firmas.stderr)
            informe["firmas_python"] = json.loads(firmas.stdout.lstrip("\ufeff"))
            for firma in informe["firmas_python"]:
                if firma["Estado"] != "Valid" or "Python Software Foundation" not in firma["Editor"]:
                    raise RuntimeError("Firma inesperada del Python incluido: " + str(firma))
            windows = Windows()
            proceso = subprocess.Popen(["cmd.exe", "/d", "/c", str(carpeta / "Abrir Servitotal.bat")], cwd=carpeta)
            informe["pid_lanzador"] = proceso.pid
            limite = time.monotonic() + 20
            while time.monotonic() < limite:
                propias = windows.descendientes(proceso.pid)
                vistas = windows.ventanas(propias)
                esperadas = [v for v in vistas if v["titulo"] == "Agencia de Empleos “Servitotal”"]
                if esperadas:
                    informe["ventana"] = esperadas[0]
                    break
                time.sleep(0.2)
            else:
                informe["ventanas"] = vistas
                raise RuntimeError("El lanzador BAT no mostró la ventana de Servitotal")
            time.sleep(2)
            propias = windows.descendientes(proceso.pid)
            if not any(v["titulo"] == "Agencia de Empleos “Servitotal”" for v in windows.ventanas(propias)):
                raise RuntimeError("La ventana se cerró durante el arranque")
            for nombre in ("errores.log", "errores_inicio.log"):
                if (datos / nombre).is_file():
                    informe[nombre] = (datos / nombre).read_text(encoding="utf-8", errors="replace")
                    raise RuntimeError("Se registró un fallo de inicio")
            with sqlite3.connect(str(datos / "agencia.db")) as conexion:
                informe["clientes"] = conexion.execute("select count(*) from clientes").fetchone()[0]
                informe["trabajadoras"] = conexion.execute("select count(*) from trabajadoras").fetchone()[0]
            if informe["clientes"] or informe["trabajadoras"]:
                raise RuntimeError("Se esperaban datos de prueba vacíos")
            informe["datos_fuera_del_zip"] = not (carpeta / "app/agencia.db").exists()
            if not informe["datos_fuera_del_zip"]:
                raise RuntimeError("El programa guardó datos junto al código")
            windows.cerrar_prueba(proceso)
            proceso = None
            informe["ok"] = True
    except BaseException:
        informe["error"] = traceback.format_exc()
    finally:
        if proceso is not None and windows is not None:
            try:
                windows.cerrar_prueba(proceso)
            except Exception:
                informe["error_cierre"] = traceback.format_exc()
        opciones.evidencia.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(informe, ensure_ascii=False, indent=2))
    return 0 if informe["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
