"""Comprueba el EXE exacto de Servitotal 1.7.1 en un Windows de pruebas.

Usa sólo la biblioteca estándar. No comprueba SmartScreen ni la marca de
descarga de Internet (MOTW) del equipo de una usuaria. Los datos de la prueba
son temporales; instalar modifica los accesos y el registro del usuario del
runner, que debe ser efímero.
"""

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback


SHA256_171 = "18b467dca5f9a2c4e64e61fbc75fb938eb21992f4b2d736758e7ccc5f2ab0811"
MARCA = "SERVITOTAL_SMOKE "
SMOKE = r'''
import json, os, sqlite3, sys, traceback
from pathlib import Path
resultado = {"callbacks": []}
root = None
try:
    datos = Path(os.environ["AGENCIA_DATOS"])
    datos.mkdir(parents=True, exist_ok=True)
    import agencia, contratos_servitotal, tkinter
    assert Path(agencia.CARPETA).resolve() == datos.resolve(), agencia.CARPETA
    resultado["python"] = sys.version
    resultado["sqlite"] = sqlite3.sqlite_version
    with sqlite3.connect(":memory:") as conexion:
        assert conexion.execute("select 1").fetchone() == (1,)
    prueba = tkinter.Tk()
    prueba.update()
    resultado["tk"] = str(prueba.tk.call("info", "patchlevel"))
    prueba.destroy()
    resultado["importaciones"] = ["agencia", "contratos_servitotal", "tkinter", "sqlite3"]
    aviso, oferta = agencia.preparar_base()
    assert aviso is None and oferta is None, (aviso, oferta)
    root = tkinter.Tk()
    root.report_callback_exception = lambda tipo, valor, traza: resultado["callbacks"].append(
        "".join(traceback.format_exception(tipo, valor, traza)))
    app = agencia.App(root)
    root.update()
    resultado["titulo"] = root.title()
    assert "Servitotal" in resultado["titulo"], resultado["titulo"]
    resultado["base_inicializada"] = Path(agencia.DB_PATH).is_file()
    resultado["clientes_ficticios"] = app.db.con.execute("select count(*) from clientes").fetchone()[0]
    assert resultado["base_inicializada"] and resultado["clientes_ficticios"] == 0
    root.after(2200, root.destroy)
    root.mainloop()
    root = None
    assert not resultado["callbacks"], resultado["callbacks"]
    assert not Path(agencia.ERRORES_PATH).is_file(), "El programa produjo errores.log"
    resultado["ok"] = True
except BaseException:
    resultado["ok"] = False
    resultado["error"] = traceback.format_exc()
finally:
    if root is not None:
        try:
            root.destroy()
        except Exception:
            pass
    print("SERVITOTAL_SMOKE " + json.dumps(resultado, ensure_ascii=False), flush=True)
sys.exit(0 if resultado["ok"] else 1)
'''


class Windows:
    """Sólo enumera y termina procesos descendientes del EXE de esta prueba."""

    def __init__(self):
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.user.EnumWindows.argtypes = [self.callback, wintypes.LPARAM]
        self.user.EnumChildWindows.argtypes = [wintypes.HWND, self.callback, wintypes.LPARAM]
        self.user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.user.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        self.user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self.user.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self.user.IsWindowVisible.argtypes = [wintypes.HWND]
        self.kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self.kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.WaitForSingleObject.restype = wintypes.DWORD

        class Entrada(ctypes.Structure):
            _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                        ("pid", wintypes.DWORD), ("heap", ctypes.c_size_t),
                        ("module", wintypes.DWORD), ("threads", wintypes.DWORD),
                        ("parent", wintypes.DWORD), ("priority", wintypes.LONG),
                        ("flags", wintypes.DWORD), ("exe", wintypes.WCHAR * 260)]

        self.Entrada = Entrada
        for nombre in ("Process32FirstW", "Process32NextW"):
            getattr(self.kernel, nombre).argtypes = [wintypes.HANDLE, ctypes.POINTER(Entrada)]
            getattr(self.kernel, nombre).restype = wintypes.BOOL

    def descendientes(self, raiz):
        snapshot = self.kernel.CreateToolhelp32Snapshot(2, 0)
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        parentesco = {}
        try:
            entrada = self.Entrada()
            entrada.dwSize = ctypes.sizeof(entrada)
            hay = self.kernel.Process32FirstW(snapshot, ctypes.byref(entrada))
            if not hay:
                raise ctypes.WinError(ctypes.get_last_error())
            while hay:
                parentesco[entrada.pid] = entrada.parent
                hay = self.kernel.Process32NextW(snapshot, ctypes.byref(entrada))
        finally:
            self.kernel.CloseHandle(snapshot)
        propios = {raiz}
        while True:
            nuevos = {pid for pid, padre in parentesco.items() if padre in propios}
            if nuevos <= propios:
                return propios
            propios.update(nuevos)

    def texto(self, ventana):
        texto = ctypes.create_unicode_buffer(self.user.GetWindowTextLengthW(ventana) + 1)
        self.user.GetWindowTextW(ventana, texto, len(texto))
        return texto.value

    def ventanas(self, propios):
        resultado = []

        @self.callback
        def enumerar(ventana, _):
            pid = wintypes.DWORD()
            self.user.GetWindowThreadProcessId(ventana, ctypes.byref(pid))
            if pid.value in propios and self.user.IsWindowVisible(ventana):
                botones = []

                @self.callback
                def hijo(control, _):
                    clase = ctypes.create_unicode_buffer(128)
                    self.user.GetClassNameW(control, clase, len(clase))
                    if clase.value.casefold() == "button":
                        botones.append(self.texto(control))
                    return True

                self.user.EnumChildWindows(ventana, hijo, 0)
                resultado.append({"pid": pid.value, "titulo": self.texto(ventana), "botones": botones})
            return True

        if not self.user.EnumWindows(enumerar, 0):
            raise ctypes.WinError(ctypes.get_last_error())
        return resultado

    def cerrar_prueba(self, proceso):
        propios = self.descendientes(proceso.pid)
        for pid in propios - {proceso.pid}:
            handle = self.kernel.OpenProcess(0x00100001, False, pid)
            if handle:
                try:
                    if not self.kernel.TerminateProcess(handle, 0) and self.kernel.WaitForSingleObject(handle, 0) != 0:
                        raise ctypes.WinError(ctypes.get_last_error())
                    if self.kernel.WaitForSingleObject(handle, 5000) != 0:
                        raise TimeoutError("El proceso de prueba no terminó de liberar sus archivos")
                finally:
                    self.kernel.CloseHandle(handle)
        if proceso.poll() is None:
            proceso.terminate()
        proceso.wait(timeout=5)


def asistente(exe, evidencia):
    windows = Windows()
    proceso = subprocess.Popen([str(exe)])
    evidencia["pid_lanzado"] = proceso.pid
    evidencia["ventanas"] = []
    try:
        limite = time.monotonic() + 15
        while time.monotonic() < limite:
            propios = windows.descendientes(proceso.pid)
            vistas = windows.ventanas(propios)
            if vistas:
                evidencia["ventanas"] = vistas
            for ventana in vistas:
                if "servitotal" in ventana["titulo"].casefold() and any(
                        "siguiente" in boton.replace("&", "").casefold() for boton in ventana["botones"]):
                    evidencia["asistente"] = ventana
                    return
            if proceso.poll() is not None and len(propios) == 1 and not vistas:
                evidencia["exit_code"] = proceso.returncode
                raise RuntimeError("El EXE terminó sin mostrar el asistente")
            time.sleep(0.2)
        raise TimeoutError("No apareció una ventana de Servitotal con el botón Siguiente en 15 s")
    finally:
        windows.cerrar_prueba(proceso)
        evidencia["proceso_prueba_cerrado"] = True


def ejecutar(comando, evidencia, *, timeout, **opciones):
    try:
        salida = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=timeout, **opciones)
    except subprocess.TimeoutExpired as error:
        evidencia["timeout_segundos"] = timeout
        for nombre in ("stdout", "stderr"):
            contenido = getattr(error, nombre) or ""
            evidencia[nombre] = contenido.decode("utf-8", "replace") if isinstance(contenido, bytes) else contenido
        raise
    evidencia.update(exit_code=salida.returncode, stdout=salida.stdout, stderr=salida.stderr)
    if salida.returncode:
        raise RuntimeError(f"El proceso terminó con código {salida.returncode}")
    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--evidencia", "--salida", type=Path, default=Path("verificacion-windows.json"))
    opciones = parser.parse_args()
    informe = {"version": "1.7.1", "fecha_utc": datetime.now(timezone.utc).isoformat(),
               "plataforma": sys.platform, "sha256_esperado": SHA256_171,
               "limite": "No valida SmartScreen ni MOTW del equipo de la usuaria.",
               "datos": "Sólo base vacía temporal en runner efímero.",
               "pasos": {nombre: {"estado": "no_ejecutado"} for nombre in
                         ("archivo", "asistente", "instalacion", "runtime_app")}}
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
        def comprobar_archivo(evidencia):
            if sys.platform != "win32":
                raise RuntimeError("Esta comprobación exige Windows nativo; no se omite la prueba")
            exe = opciones.exe.resolve(strict=True)
            evidencia["sha256"] = hashlib.sha256(exe.read_bytes()).hexdigest()
            if evidencia["sha256"] != SHA256_171:
                raise RuntimeError("El EXE no coincide con Servitotal 1.7.1 entregado")

        if not probar("archivo", comprobar_archivo):
            for nombre in ("asistente", "instalacion", "runtime_app"):
                informe["pasos"][nombre]["motivo"] = "No se puede ejecutar un archivo sin validar"
            return 1
        exe = opciones.exe.resolve(strict=True)
        with tempfile.TemporaryDirectory(prefix="servitotal prueba windows ") as temporal:
            instalacion = Path(temporal) / "programa con espacios"
            datos = Path(temporal) / "datos ficticios"
            probar("asistente", lambda evidencia: asistente(exe, evidencia))

            def instalar(evidencia):
                # NSIS consume el resto de la línea como /D: último y sin comillas.
                ejecutar(f'"{exe}" /S /D={instalacion}', evidencia, timeout=60)
                piezas = ("runtime/python.exe", "runtime/pythonw.exe", "runtime/python312.dll",
                          "app/agencia.py", "app/contratos_servitotal.py", "app/iniciar.pyw")
                evidencia["archivos"] = {ruta: (instalacion / ruta).is_file() for ruta in piezas}
                if not all(evidencia["archivos"].values()):
                    raise RuntimeError("La instalación no contiene todas las piezas necesarias")

            def runtime_app(evidencia):
                entorno = dict(os.environ, AGENCIA_DATOS=str(datos), PYTHONIOENCODING="utf-8")
                for nombre in ("PYTHONHOME", "PYTHONPATH", "TCL_LIBRARY", "TK_LIBRARY"):
                    entorno.pop(nombre, None)
                try:
                    ejecutar([str(instalacion / "runtime/python.exe"), "-c", SMOKE, "--datos", str(datos)],
                             evidencia, timeout=20, cwd=instalacion / "app", env=entorno)
                finally:
                    respuestas = [linea[len(MARCA):] for linea in evidencia.get("stdout", "").splitlines()
                                  if linea.startswith(MARCA)]
                    if respuestas:
                        evidencia["resultado"] = json.loads(respuestas[-1])
                if not evidencia.get("resultado", {}).get("ok"):
                    raise RuntimeError("El runtime no devolvió evidencia satisfactoria de Tk, SQLite y App")

            if probar("instalacion", instalar):
                probar("runtime_app", runtime_app)
            else:
                informe["pasos"]["runtime_app"]["motivo"] = "Depende de la instalación fallida"
    except BaseException:
        informe["error_general"] = traceback.format_exc()
    finally:
        informe["ok"] = (not informe.get("error_general")
                         and all(paso["estado"] == "correcto" for paso in informe["pasos"].values()))
        opciones.evidencia.parent.mkdir(parents=True, exist_ok=True)
        opciones.evidencia.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(informe, ensure_ascii=False, indent=2))
    return 0 if informe["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
