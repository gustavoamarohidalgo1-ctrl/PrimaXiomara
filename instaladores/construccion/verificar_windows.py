"""Comprueba el instalador de Servitotal en un Windows de pruebas, como lo usaría la agencia.

Instala sobre la versión 1.7.1 publicada, comprueba que no se reemplaza un programa abierto, abre el programa con el
mismo acceso directo del Escritorio, trae los datos de la versión anterior respondiendo a su aviso, lo abre con
variables de entorno de otro Python y lo desinstala conservando los datos. Cada apertura se cierra con el botón de
la ventana, como haría la usuaria.

Usa sólo la biblioteca estándar. No comprueba SmartScreen, el Control inteligente de aplicaciones ni el antivirus
del equipo de una usuaria. Instalar modifica los accesos, el registro y el Escritorio del usuario del runner, que
debe ser efímero.
"""

import argparse
from contextlib import closing
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
from urllib.request import urlopen


VERSION = re.search(r'^VERSION = "([0-9.]+)"', (Path(__file__).resolve().parents[2] / "agencia.py")
                    .read_text(encoding="utf-8"), re.M).group(1)          # la de agencia.py
TITULO = "Agencia de Empleos"
TITULO_ANTERIOR = "Agencia de Empleos “Servitotal”"     # la ventana de la 1.7.1 publicada
# Versión publicada antes del arreglo: la agencia puede tenerla instalada.
URL_ANTERIOR = ("https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/raw/"
                "3a9e0a944c071790656e3b511c3f67bd7249363c/instaladores/Servitotal-Windows-x64.exe")
SHA256_ANTERIOR = "18b467dca5f9a2c4e64e61fbc75fb938eb21992f4b2d736758e7ccc5f2ab0811"
CLAVE_DESINSTALAR = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Servitotal"
WM_CLOSE, WM_COMMAND, IDYES, BM_GETCHECK = 0x0010, 0x0111, 6, 0x00F0
MARCA = "SERVITOTAL_SMOKE "
SMOKE = r'''
import json, os, sqlite3, sys, traceback
from pathlib import Path
resultado = {"callbacks": []}
root = None
try:
    datos = Path(os.environ["AGENCIA_DATOS"])
    datos.mkdir(parents=True, exist_ok=True)
    import agencia, tkinter
    assert Path(agencia.CARPETA).resolve() == datos.resolve(), agencia.CARPETA
    import importlib.util
    resultado["pyc_de_la_fuente"] = []
    cache = importlib.util.cache_from_source(agencia.__file__)   # un .pyc «unchecked-hash» viejo se usaría sin avisar
    if os.path.exists(cache):
        pyc = Path(cache).read_bytes()
        if int.from_bytes(pyc[4:8], "little") & 1:
            assert pyc[8:16] == importlib.util.source_hash(Path(agencia.__file__).read_bytes()), cache
            resultado["pyc_de_la_fuente"].append(Path(cache).name)
    resultado["python"] = sys.version
    resultado["sqlite"] = sqlite3.sqlite_version
    with sqlite3.connect(":memory:") as conexion:
        assert conexion.execute("select 1").fetchone() == (1,)
    prueba = tkinter.Tk()
    prueba.update()
    resultado["tk"] = str(prueba.tk.call("info", "patchlevel"))
    prueba.destroy()
    resultado["importaciones"] = ["agencia", "tkinter", "sqlite3"]
    aviso, oferta = agencia.preparar_base()
    assert aviso is None and oferta is None, (aviso, oferta)
    root = tkinter.Tk()
    root.report_callback_exception = lambda tipo, valor, traza: resultado["callbacks"].append(
        "".join(traceback.format_exception(tipo, valor, traza)))
    app = agencia.App(root)
    root.update()
    resultado["titulo"] = root.title()
    assert resultado["titulo"] == "Agencia de Empleos", resultado["titulo"]
    assert agencia.AGENCIA_ESLOGAN == "Servitotal", agencia.AGENCIA_ESLOGAN   # el programa de esta agencia
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
    print("SERVITOTAL_SMOKE " + json.dumps(resultado), flush=True)   # ASCII: -E ignora PYTHONIOENCODING
sys.exit(0 if resultado["ok"] else 1)
'''

# Estructura de la base de la versión anterior a la actualización (datos junto al programa, sin áreas).
ESQUEMA_ANTERIOR = """
CREATE TABLE clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT DEFAULT '', dni TEXT DEFAULT '',
  telefono TEXT DEFAULT '', direccion TEXT DEFAULT '', zona TEXT DEFAULT '', fecha_registro TEXT DEFAULT '',
  tipo_servicio TEXT DEFAULT '', sueldo_ofrecido TEXT DEFAULT '', horario TEXT DEFAULT '', dias_libres TEXT DEFAULT '',
  personas_hogar TEXT DEFAULT '', ninos TEXT DEFAULT '', mascotas TEXT DEFAULT '', tareas TEXT DEFAULT '',
  requisitos TEXT DEFAULT '', fecha_necesita TEXT DEFAULT '', estado TEXT DEFAULT '', notas TEXT DEFAULT '',
  garantia TEXT DEFAULT '', ocupacion TEXT DEFAULT '');
CREATE TABLE trabajadoras (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT DEFAULT '', dni TEXT DEFAULT '',
  edad TEXT DEFAULT '', telefono TEXT DEFAULT '', direccion TEXT DEFAULT '', zona TEXT DEFAULT '',
  tipo_servicio TEXT DEFAULT '', cama_adentro TEXT DEFAULT '', experiencia TEXT DEFAULT '',
  sueldo_esperado TEXT DEFAULT '', referencias TEXT DEFAULT '', doc_dni TEXT DEFAULT '',
  doc_antecedentes TEXT DEFAULT '', doc_salud TEXT DEFAULT '', doc_domicilio TEXT DEFAULT '',
  doc_referencias TEXT DEFAULT '', entrevista_fecha TEXT DEFAULT '', entrevista_resultado TEXT DEFAULT '',
  entrevista_notas TEXT DEFAULT '', estado TEXT DEFAULT '', notas TEXT DEFAULT '');
CREATE TABLE colocaciones (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id TEXT DEFAULT '',
  trabajadora_id TEXT DEFAULT '', entrevista_cliente_fecha TEXT DEFAULT '', entrevista_cliente_resultado TEXT DEFAULT '',
  entrevista_cliente_notas TEXT DEFAULT '', sueldo_acordado TEXT DEFAULT '', porcentaje TEXT DEFAULT '',
  comision TEXT DEFAULT '', comision_pagada TEXT DEFAULT '', contrato_firmado TEXT DEFAULT '',
  docs_entregados TEXT DEFAULT '', fecha_inicio TEXT DEFAULT '', fin_garantia TEXT DEFAULT '', estado TEXT DEFAULT '',
  reemplazo_de TEXT DEFAULT '', notas TEXT DEFAULT '', fecha_enlace TEXT DEFAULT '', fecha_pago TEXT DEFAULT '',
  fecha_firma TEXT DEFAULT '', firma_cliente TEXT DEFAULT '', firma_trabajadora TEXT DEFAULT '',
  firma_agencia TEXT DEFAULT '', garantia TEXT DEFAULT '');
"""


class Windows:
    """Sólo enumera, responde y termina procesos descendientes de los lanzados por esta prueba."""

    def __init__(self):
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.shell = ctypes.WinDLL("shell32", use_last_error=True)
        self.callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.user.EnumWindows.argtypes = [self.callback, wintypes.LPARAM]
        self.user.EnumChildWindows.argtypes = [wintypes.HWND, self.callback, wintypes.LPARAM]
        self.user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.user.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        self.user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self.user.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self.user.IsWindowVisible.argtypes = [wintypes.HWND]
        self.user.GetDlgCtrlID.argtypes = [wintypes.HWND]
        self.user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        self.user.PostMessageW.restype = wintypes.BOOL
        self.user.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        self.user.SendMessageW.restype = ctypes.c_ssize_t
        self.user.IsWindowEnabled.argtypes = [wintypes.HWND]
        self.user.IsIconic.argtypes = [wintypes.HWND]
        self.user.GetForegroundWindow.restype = wintypes.HWND
        self.kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self.shell.SHGetFolderPathW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.HANDLE, wintypes.DWORD,
                                                wintypes.LPWSTR]
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

    def clase(self, ventana):
        clase = ctypes.create_unicode_buffer(128)
        self.user.GetClassNameW(ventana, clase, len(clase))
        return clase.value

    def ventanas(self, propios):
        resultado = []

        @self.callback
        def enumerar(ventana, _):
            pid = wintypes.DWORD()
            self.user.GetWindowThreadProcessId(ventana, ctypes.byref(pid))
            if pid.value in propios and self.user.IsWindowVisible(ventana):
                botones, controles, textos = [], [], []

                @self.callback
                def hijo(control, _):
                    clase = self.clase(control).casefold()
                    if clase == "button":
                        botones.append(self.texto(control))
                        controles.append({"texto": self.texto(control), "id": self.user.GetDlgCtrlID(control),
                                          "hwnd": control, "habilitado": bool(self.user.IsWindowEnabled(control)),
                                          "visible": bool(self.user.IsWindowVisible(control)),
                                          "marcado": self.user.SendMessageW(control, BM_GETCHECK, 0, 0)})
                    elif clase == "static" and self.texto(control):
                        textos.append(self.texto(control))
                    return True

                self.user.EnumChildWindows(ventana, hijo, 0)
                resultado.append({"pid": pid.value, "hwnd": ventana, "titulo": self.texto(ventana),
                                  "clase": self.clase(ventana), "botones": botones, "controles": controles,
                                  "textos": textos})
            return True

        if not self.user.EnumWindows(enumerar, 0):
            raise ctypes.WinError(ctypes.get_last_error())
        return resultado

    def enviar(self, ventana, mensaje, wparam=0, lparam=0):
        if not self.user.PostMessageW(ventana, mensaje, wparam, lparam):
            raise ctypes.WinError(ctypes.get_last_error())

    def esperar_fin(self, pid, segundos):
        """Espera a que termine un proceso que no lanzó esta prueba (p. ej. el que abre el instalador)."""
        handle = self.kernel.OpenProcess(0x00100000 | 0x1000, False, pid)   # SYNCHRONIZE | QUERY_LIMITED
        if not handle:
            return None
        try:
            if self.kernel.WaitForSingleObject(handle, int(segundos * 1000)) != 0:
                return None
            codigo = wintypes.DWORD()
            self.kernel.GetExitCodeProcess(handle, ctypes.byref(codigo))
            return codigo.value
        finally:
            self.kernel.CloseHandle(handle)

    def carpeta(self, codigo):
        ruta = ctypes.create_unicode_buffer(260)
        if self.shell.SHGetFolderPathW(None, codigo, None, 0, ruta) != 0:
            raise RuntimeError("Windows no indicó la carpeta especial %#x" % codigo)
        return Path(ruta.value)

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


def usar_programa(comando, windows, evidencia, *, entorno=None, cwd=None, respuestas=None, entrada=None, limite=60):
    """Abre el programa como la usuaria, responde a los avisos esperados y lo cierra con el botón X.

    `respuestas` asocia el título de cada aviso esperado con el botón a pulsar (IDYES o "unico"). Cualquier otro
    aviso, una ventana que no aparece o un cierre con error hacen fallar la prueba."""
    pendientes = dict(respuestas or {})
    evidencia.update(comando=[str(c) for c in comando], avisos=[])
    with tempfile.TemporaryFile() as salida:
        proceso = subprocess.Popen([str(c) for c in comando], cwd=cwd, env=entorno, stdout=salida,
                                   stderr=subprocess.STDOUT,
                                   stdin=subprocess.PIPE if entrada is not None else subprocess.DEVNULL)
        evidencia["pid"] = proceso.pid
        principal = visible_desde = None
        cierre = False
        try:
            fin = time.monotonic() + limite
            while time.monotonic() < fin and proceso.poll() is None:
                vistas = windows.ventanas(windows.descendientes(proceso.pid))
                for ventana in vistas:
                    if ventana["titulo"] == TITULO:
                        if principal is None:
                            principal, visible_desde = ventana, time.monotonic()
                            evidencia["ventana"] = {k: ventana[k] for k in ("titulo", "clase")}
                        continue
                    if ventana["clase"] != "#32770":
                        continue
                    boton = pendientes.pop(ventana["titulo"], None)
                    evidencia["avisos"].append({k: ventana[k] for k in ("titulo", "textos", "controles")})
                    if boton is None:
                        raise RuntimeError("Aviso inesperado: %s %s" % (ventana["titulo"], ventana["textos"]))
                    if boton == "unico":
                        boton = ventana["controles"][0]["id"]
                    windows.enviar(ventana["hwnd"], WM_COMMAND, boton)
                    time.sleep(0.5)
                abiertos = [v for v in vistas if v["clase"] == "#32770"]
                if (principal is not None and not pendientes and not abiertos and not cierre
                        and time.monotonic() - visible_desde > 4):
                    windows.enviar(principal["hwnd"], WM_CLOSE)      # el botón X de la ventana
                    cierre = True
                    evidencia["cierre_solicitado"] = True
                if (cierre and entrada is not None and proceso.stdin and not proceso.stdin.closed
                        and not any(v["titulo"] == TITULO for v in vistas)):
                    proceso.stdin.write(entrada.encode())             # la tecla Enter que pide la consola
                    proceso.stdin.close()
                time.sleep(0.25)
            proceso.wait(timeout=max(1, fin - time.monotonic()))
        except subprocess.TimeoutExpired:
            raise TimeoutError("El programa no terminó después de pedir el cierre")
        finally:
            if proceso.poll() is None:
                windows.cerrar_prueba(proceso)
                evidencia["terminado_por_la_prueba"] = True
            salida.seek(0)
            evidencia["salida"] = salida.read().decode("utf-8", "replace")[-4000:]
            evidencia["codigo"] = proceso.returncode
    if principal is None:
        raise RuntimeError("No apareció la ventana de Servitotal")
    if pendientes:
        raise RuntimeError("No aparecieron los avisos esperados: " + ", ".join(pendientes))
    if not cierre or proceso.returncode != 0:
        raise RuntimeError(f"El programa no se cerró normalmente (código {proceso.returncode})")


def comprobar_sin_errores(datos, evidencia):
    for nombre in ("errores.log", "errores_inicio.log"):
        if (datos / nombre).is_file():
            evidencia[nombre] = (datos / nombre).read_text(encoding="utf-8", errors="replace")[-4000:]
            raise RuntimeError(f"El programa registró errores en {nombre}")


def contar(base):
    with closing(sqlite3.connect(base.resolve().as_uri() + "?mode=ro", uri=True)) as conexion:
        return {tabla: conexion.execute(f"select count(*) from {tabla}").fetchone()[0]
                for tabla in ("clientes", "trabajadoras", "colocaciones")}


def crear_base_anterior(ruta):
    """Base ficticia con la estructura de la versión anterior; devuelve su huella para comprobar que no cambia."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(str(ruta))) as conexion, conexion:
        conexion.executescript(ESQUEMA_ANTERIOR)
        conexion.execute("INSERT INTO clientes (nombre, telefono, tipo_servicio, garantia, estado) "
                         "VALUES ('Clienta ficticia Ñuñoa', '900000000', 'Cama adentro', 'Sí', 'Colocado')")
        conexion.execute("INSERT INTO trabajadoras (nombre, tipo_servicio, estado) "
                         "VALUES ('Trabajadora ficticia', 'Cama adentro', 'Trabajando')")
        conexion.execute("INSERT INTO colocaciones (cliente_id, trabajadora_id, sueldo_acordado, porcentaje, comision, "
                         "estado, fecha_inicio, garantia) VALUES ('1', '1', '1500', '50', '750', 'Activa', "
                         "'01/09/2026', 'Sí')")
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def huella_publicada(archivo):
    """Huella del archivo según SHA256SUMS.txt, junto a él."""
    for linea in (archivo.parent / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        huella, _, nombre = linea.partition("  ")
        if nombre.strip() == archivo.name:
            return huella.strip()
    raise RuntimeError(f"SHA256SUMS.txt no tiene la huella de {archivo.name}")


def entorno_de_otro_python(base, carpeta):
    """Variables que dejan otros programas y que no deben alterar el Python incluido."""
    ajena = carpeta / "otro python"
    ajena.mkdir(parents=True, exist_ok=True)
    return dict(base, PYTHONHOME=str(ajena), PYTHONPATH=str(ajena), TCL_LIBRARY=str(ajena), TK_LIBRARY=str(ajena),
                PYTHONSTARTUP=str(ajena / "no-existe.py"))


def asistente_completo(exe, windows, evidencia, entorno, al_aviso=None):
    """Instala como la usuaria: Siguiente, Instalar y Terminar con «Abrir Servitotal ahora» marcado. Después la
    ventana del programa debe aparecer sola, en primer plano, y cerrarse normalmente con su botón X."""
    proceso = subprocess.Popen([str(exe)], env=entorno)
    evidencia.update(pid=proceso.pid, pulsados=[])
    try:
        fin = time.monotonic() + 240
        programa = None
        while time.monotonic() < fin and programa is None:
            vistas = windows.ventanas(windows.descendientes(proceso.pid))
            programa = next((v for v in vistas if v["titulo"] == TITULO), None)
            if programa is not None or proceso.poll() is not None:
                continue
            propias = [v for v in vistas if v["pid"] == proceso.pid]
            asistente = next((v for v in propias if any(c["id"] == 3 for c in v["controles"])), None)  # tiene «Atrás»
            avisos = [v for v in propias if v is not asistente and v["clase"] == "#32770"]
            if avisos:
                evidencia.setdefault("avisos_instalador", []).append({k: avisos[0][k] for k in ("titulo", "textos")})
                if al_aviso is None:
                    raise RuntimeError("El instalador mostró un aviso: %s %s" % (avisos[0]["titulo"], avisos[0]["textos"]))
                windows.enviar(avisos[0]["hwnd"], WM_COMMAND, al_aviso(avisos[0]))   # el botón que elige la usuaria
                time.sleep(2)
                continue
            siguiente = next((c for c in (asistente or {}).get("controles", []) if c["id"] == 1), None)
            if siguiente and siguiente["habilitado"] and siguiente["visible"]:
                texto = siguiente["texto"].replace("&", "")
                if "terminar" in texto.casefold():
                    abrir = [c for c in asistente["controles"] if "abrir" in c["texto"].casefold()]
                    evidencia["abrir_ahora_marcado"] = bool(abrir and abrir[0]["marcado"] == 1)
                    if not evidencia["abrir_ahora_marcado"]:
                        raise RuntimeError("La casilla «Abrir Servitotal ahora» no está marcada por defecto")
                evidencia["pulsados"].append(texto)
                windows.enviar(asistente["hwnd"], WM_COMMAND, 1, siguiente["hwnd"])
                time.sleep(2)                     # dejar que cambie la página antes de mirar de nuevo
                continue
            time.sleep(0.3)
        if programa is None:
            evidencia["codigo_instalador"] = proceso.poll()
            raise RuntimeError("Después de Terminar no apareció la ventana de Servitotal")
        evidencia["codigo_instalador"] = proceso.wait(timeout=30)
        if evidencia["codigo_instalador"] != 0:
            raise RuntimeError("El instalador terminó con código %s" % evidencia["codigo_instalador"])
        pasos = [p.casefold() for p in evidencia["pulsados"]]
        if not pasos or "terminar" not in pasos[-1] or not any("instalar" in p for p in pasos):
            raise RuntimeError("El asistente no pasó por Instalar y Terminar: " + str(evidencia["pulsados"]))
        time.sleep(4)
        # Al frente debe estar Servitotal: su ventana o un aviso suyo.
        frente = windows.user.GetForegroundWindow()
        pid_frente = wintypes.DWORD()
        windows.user.GetWindowThreadProcessId(frente, ctypes.byref(pid_frente))
        evidencia["en_primer_plano"] = pid_frente.value == programa["pid"]
        evidencia["al_frente"] = windows.texto(frente) if frente else None
        evidencia["minimizada"] = bool(windows.user.IsIconic(programa["hwnd"]))
        if not evidencia["en_primer_plano"] or evidencia["minimizada"]:
            raise RuntimeError("La ventana del programa quedó detrás de otras o minimizada: la usuaria no la vería")
        # Sin datos anteriores en este equipo, el programa termina de buscarlos y abre sin ningún aviso.
        limite = time.monotonic() + 10
        evidencia["avisos_programa"] = []
        while time.monotonic() < limite:
            avisos = [v for v in windows.ventanas({programa["pid"]}) if v["clase"] == "#32770"]
            if avisos:
                aviso = avisos[0]
                evidencia["avisos_programa"].append({k: aviso[k] for k in ("titulo", "textos")})
                raise RuntimeError("El programa abrió con un aviso: %s %s" % (aviso["titulo"], aviso["textos"]))
            time.sleep(0.25)
        windows.enviar(programa["hwnd"], WM_CLOSE)
        evidencia["codigo_programa"] = windows.esperar_fin(programa["pid"], 60)
        if evidencia["codigo_programa"] != 0:
            raise RuntimeError("El programa abierto por el instalador no se cerró normalmente: %s"
                               % evidencia["codigo_programa"])
    finally:
        if proceso.poll() is None:
            windows.cerrar_prueba(proceso)


def analizar_con_defender(ruta, evidencia):
    """Analiza con Microsoft Defender actualizado. Código 0 de MpCmdRun: sin amenazas; 2: amenaza detectada."""
    literal = str(ruta).replace("'", "''")
    guion = (
        "$ErrorActionPreference = 'Continue'; [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
        "$antes = (Get-MpComputerStatus).AntivirusSignatureVersion; "
        "try { Update-MpSignature -ErrorAction Stop; $act = 'ok' } catch { $act = $_.Exception.Message }; "
        "$e = Get-MpComputerStatus; "
        "$mp = Join-Path $env:ProgramFiles 'Windows Defender\\MpCmdRun.exe'; "
        f"$salida = & $mp -Scan -ScanType 3 -File '{literal}' -DisableRemediation 2>&1 | Out-String; "
        "$codigo = $LASTEXITCODE; "
        "[pscustomobject]@{ servicio=$e.AMServiceEnabled; antivirus=$e.AntivirusEnabled; modo=\"$($e.AMRunningMode)\"; "
        "tiempo_real=$e.RealTimeProtectionEnabled; "
        "firmas_antes=$antes; firmas=$e.AntivirusSignatureVersion; actualizacion=$act; codigo=$codigo; "
        "salida=$salida.Trim() } | ConvertTo-Json -Compress")
    resultado = subprocess.run(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", guion],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    try:
        datos = json.loads(resultado.stdout.strip().lstrip("\ufeff"))
    except ValueError:
        evidencia.update(stdout=resultado.stdout[-2000:], stderr=resultado.stderr[-2000:])
        raise RuntimeError("No se pudo ejecutar Microsoft Defender")
    evidencia["defender"] = datos
    if datos.get("codigo") == 2:
        raise RuntimeError("Microsoft Defender detectó una amenaza en " + str(ruta))
    if datos.get("codigo") != 0:
        raise RuntimeError("Microsoft Defender no pudo analizar el archivo (código %s)" % datos.get("codigo"))


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
                evidencia["ventanas"] = [{k: v[k] for k in ("titulo", "botones")} for v in vistas]
            for ventana in vistas:
                if "servitotal" in ventana["titulo"].casefold() and any(
                        "siguiente" in boton.replace("&", "").casefold() for boton in ventana["botones"]):
                    evidencia["asistente"] = {k: ventana[k] for k in ("titulo", "botones")}
                    return
            if proceso.poll() is not None and len(propios) == 1 and not vistas:
                evidencia["exit_code"] = proceso.returncode
                raise RuntimeError("El EXE terminó sin mostrar el asistente")
            time.sleep(0.2)
        raise TimeoutError("No apareció una ventana de Servitotal con el botón Siguiente en 15 s")
    finally:
        windows.cerrar_prueba(proceso)
        evidencia["proceso_prueba_cerrado"] = True


def ejecutar(comando, evidencia, *, timeout, codigo_esperado=0, **opciones):
    try:
        salida = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=timeout, **opciones)
    except subprocess.TimeoutExpired as error:
        evidencia["timeout_segundos"] = timeout
        for nombre in ("stdout", "stderr"):
            contenido = getattr(error, nombre) or ""
            evidencia[nombre] = contenido.decode("utf-8", "replace") if isinstance(contenido, bytes) else contenido
        raise
    evidencia.update(exit_code=salida.returncode, stdout=salida.stdout[-4000:], stderr=salida.stderr[-4000:])
    if salida.returncode != codigo_esperado:
        raise RuntimeError(f"El proceso terminó con código {salida.returncode} (se esperaba {codigo_esperado})")
    return salida


def acceso_directo(ruta):
    """Destino, argumentos y carpeta de inicio de un .lnk, leídos por el propio Windows."""
    literal = str(ruta).replace("'", "''")
    resultado = subprocess.run([
        "powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command",
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
        f"$l = (New-Object -ComObject WScript.Shell).CreateShortcut('{literal}'); "
        "[pscustomobject]@{ destino=$l.TargetPath; argumentos=$l.Arguments; inicio=$l.WorkingDirectory } "
        "| ConvertTo-Json -Compress"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    if resultado.returncode:
        raise RuntimeError("No se pudo leer el acceso directo: " + resultado.stderr)
    return json.loads(resultado.stdout.lstrip("﻿"))


def comando_de_acceso(atajo):
    """Descompone los argumentos del acceso como lo haría Windows (CommandLineToArgvW)."""
    shell = ctypes.WinDLL("shell32")
    shell.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    shell.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    cantidad = ctypes.c_int()
    lista = shell.CommandLineToArgvW(f'"{atajo["destino"]}" {atajo["argumentos"]}', ctypes.byref(cantidad))
    try:
        return [lista[i] for i in range(cantidad.value)]
    finally:
        ctypes.windll.kernel32.LocalFree(lista)


def version_registrada():
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE_DESINSTALAR) as clave:
        return winreg.QueryValueEx(clave, "DisplayVersion")[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--evidencia", "--salida", type=Path, default=Path("verificacion-windows.json"))
    parser.add_argument("--sin-anterior", action="store_true", help="no instalar antes la versión 1.7.1")
    opciones = parser.parse_args()
    pasos = ("archivo", "defender_instalador", "asistente", "instalacion_anterior", "en_uso", "instalacion",
             "defender_instalado", "runtime_app", "acceso_directo", "icono_anclado_antiguo", "datos_anteriores",
             "entorno_de_otro_python", "desinstalacion", "datos_dentro_del_programa")
    informe = {"version": VERSION, "fecha_utc": datetime.now(timezone.utc).isoformat(), "plataforma": sys.platform,
               "limite": "No valida SmartScreen, el Control inteligente de aplicaciones ni MOTW del equipo real.",
               "datos": "Sólo bases ficticias en un runner efímero.",
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
            raise RuntimeError("Ejecute esta prueba sólo en un runner Windows efímero de GitHub")
        exe = opciones.exe.resolve(strict=True)

        def comprobar_archivo(evidencia):
            evidencia["sha256"] = hashlib.sha256(exe.read_bytes()).hexdigest()
            evidencia["sha256_publicado"] = huella_publicada(exe)
            if evidencia["sha256"] != evidencia["sha256_publicado"]:
                raise RuntimeError("El EXE no coincide con SHA256SUMS.txt")

        if not probar("archivo", comprobar_archivo):
            return 1
        windows = Windows()
        local = windows.carpeta(0x1C)                      # LOCALAPPDATA real: el instalador usa esa carpeta
        datos = local / "Servitotal"
        escritorio = windows.carpeta(0x10)
        if datos.exists():
            raise RuntimeError("El runner ya tiene datos de Servitotal; se requiere un perfil vacío")
        with tempfile.TemporaryDirectory(prefix="servitotal prueba windows ñ ", ignore_cleanup_errors=True) as temporal:
            temporal = Path(temporal)
            instalacion = temporal / "programa con espacios"
            entorno = {k: v for k, v in os.environ.items() if k not in ("AGENCIA_DATOS", "PYTHONHOME", "PYTHONPATH",
                                                                         "TCL_LIBRARY", "TK_LIBRARY")}
            probar("defender_instalador", lambda evidencia: analizar_con_defender(exe, evidencia))
            probar("asistente", lambda evidencia: asistente(exe, evidencia))

            def instalar(instalador, evidencia, codigo=0):
                # NSIS consume el resto de la línea como /D: último y sin comillas.
                ejecutar(f'"{instalador}" /S /D={instalacion}', evidencia, timeout=180, codigo_esperado=codigo)

            def instalar_anterior(evidencia):
                anterior = temporal / "Servitotal-1.7.1.exe"
                with urlopen(URL_ANTERIOR, timeout=120) as respuesta:
                    anterior.write_bytes(respuesta.read())
                evidencia["sha256"] = hashlib.sha256(anterior.read_bytes()).hexdigest()
                if evidencia["sha256"] != SHA256_ANTERIOR:
                    raise RuntimeError("La descarga de la versión 1.7.1 no coincide con la publicada")
                instalar(anterior, evidencia)
                evidencia["version_registrada"] = version_registrada()
                if evidencia["version_registrada"] != "1.7.1":
                    raise RuntimeError("No quedó instalada la versión 1.7.1")

            def en_uso(evidencia):
                # Con la versión anterior abierta, el instalador nuevo no debe tocar nada.
                antes = (instalacion / "app/agencia.py").read_bytes()
                abierto = subprocess.Popen([str(instalacion / "runtime/pythonw.exe"),
                                            str(instalacion / "app/iniciar.pyw"), "--datos", str(temporal / "d")],
                                           cwd=instalacion / "app", env=entorno)
                try:
                    limite = time.monotonic() + 30
                    while not any(v["titulo"] == TITULO_ANTERIOR for v in windows.ventanas(windows.descendientes(abierto.pid))):
                        if time.monotonic() > limite or abierto.poll() is not None:
                            raise RuntimeError("La versión anterior no llegó a abrirse")
                        time.sleep(0.25)
                    instalar(exe, evidencia, codigo=2)
                    if (instalacion / "app/agencia.py").read_bytes() != antes:
                        raise RuntimeError("El instalador modificó un programa abierto")
                    evidencia["programa_abierto_intacto"] = True
                finally:
                    windows.cerrar_prueba(abierto)

            def instalar_nueva(evidencia):
                if opciones.sin_anterior:
                    instalar(exe, evidencia)
                else:
                    # Sobre la versión anterior, con clics, como la usuaria, y con la 1.7.1 todavía abierta: al pulsar
                    # Instalar debe ofrecer Reintentar; ella cierra la 1.7.1 y pulsa Reintentar.
                    abierta = subprocess.Popen([str(instalacion / "runtime/pythonw.exe"), str(instalacion / "app/iniciar.pyw"),
                                                "--datos", str(temporal / "d2")], cwd=instalacion / "app", env=entorno)
                    limite = time.monotonic() + 30
                    while not any(v["titulo"] == TITULO_ANTERIOR for v in windows.ventanas(windows.descendientes(abierta.pid))):
                        if time.monotonic() > limite or abierta.poll() is not None:
                            raise RuntimeError("La versión anterior no llegó a abrirse")
                        time.sleep(0.25)

                    def al_aviso(aviso):
                        texto = " ".join(aviso["textos"]).casefold()
                        ids = [c["id"] for c in aviso["controles"]]
                        if "abierto" not in texto or 4 not in ids:                   # 4 = IDRETRY
                            raise RuntimeError("Aviso inesperado del instalador: %s" % aviso["textos"])
                        windows.cerrar_prueba(abierta)                                # ella cierra la 1.7.1
                        evidencia["reintento"] = True
                        return 4

                    try:
                        asistente_completo(exe, windows, evidencia, entorno, al_aviso=al_aviso)
                    finally:
                        if abierta.poll() is None:
                            windows.cerrar_prueba(abierta)
                    if not evidencia.get("reintento"):
                        raise RuntimeError("Con la 1.7.1 abierta, el instalador no ofreció Reintentar")
                evidencia["version_registrada"] = version_registrada()
                if evidencia["version_registrada"] != VERSION:
                    raise RuntimeError("El registro no muestra la versión " + VERSION)
                piezas = ("runtime/python.exe", "runtime/pythonw.exe", "runtime/python312.dll",
                          "runtime/vcruntime140_1.dll", "app/agencia.py", "app/iniciar.pyw", "Desinstalar.exe")
                evidencia["archivos"] = {ruta: (instalacion / ruta).is_file() for ruta in piezas}
                if not all(evidencia["archivos"].values()):
                    raise RuntimeError("La instalación no contiene todas las piezas necesarias")
                sobrantes = [p.name for p in instalacion.iterdir() if p.name not in ("runtime", "app", "Desinstalar.exe")]
                if sobrantes:
                    raise RuntimeError("Quedaron restos de la actualización: " + ", ".join(sobrantes))
                raiz, aqui = Path(__file__).resolve().parents[2], Path(__file__).resolve().parent
                for instalado, fuente in (("agencia.py", raiz / "agencia.py"), ("iniciar.pyw", aqui / "iniciar.pyw")):
                    if (instalacion / "app" / instalado).read_bytes() != fuente.read_bytes():
                        raise RuntimeError(f"El {instalado} instalado no es el de esta versión")

            def runtime_app(evidencia):
                propio = dict(entorno, AGENCIA_DATOS=str(temporal / "datos smoke"))
                try:
                    ejecutar([str(instalacion / "runtime/python.exe"), "-E", "-s", "-c", SMOKE], evidencia, timeout=60,
                             cwd=instalacion / "app", env=propio)
                finally:
                    respuestas = [linea[len(MARCA):] for linea in evidencia.get("stdout", "").splitlines()
                                  if linea.startswith(MARCA)]
                    if respuestas:
                        evidencia["resultado"] = json.loads(respuestas[-1])
                if not evidencia.get("resultado", {}).get("ok"):
                    raise RuntimeError("El runtime no devolvió evidencia satisfactoria de Tk, SQLite y App")
                if len(evidencia["resultado"]["pyc_de_la_fuente"]) != 1:
                    raise RuntimeError("Faltan los .pyc precompilados del programa")

            def comando_escritorio(evidencia):
                atajo = acceso_directo(escritorio / "Servitotal.lnk")
                evidencia["acceso"] = atajo
                comando = comando_de_acceso(atajo)
                if (not os.path.samefile(comando[0], instalacion / "runtime" / "pythonw.exe")
                        or comando[1:3] != ["-E", "-s"]):
                    raise RuntimeError("El acceso directo no abre el Python incluido aislado: " + str(comando))
                if comando[-2] != "--datos" or os.path.normcase(comando[-1]) != os.path.normcase(str(datos)):
                    raise RuntimeError("El acceso directo no usa la carpeta de datos del usuario")
                return comando, atajo["inicio"] or None

            def abrir_acceso(evidencia):
                comando, inicio = comando_escritorio(evidencia)
                usar_programa(comando, windows, evidencia, entorno=entorno, cwd=inicio)
                comprobar_sin_errores(datos, evidencia)
                evidencia["datos"] = contar(datos / "agencia.db")
                if any(evidencia["datos"].values()):
                    raise RuntimeError("Una instalación nueva debe abrir sin registros")

            def icono_anclado_antiguo(evidencia):
                # Un ícono anclado por 1.7.1 abre runtime\pythonw.exe sin argumentos: debe abrir Servitotal.
                usar_programa([instalacion / "runtime" / "pythonw.exe"], windows, evidencia, entorno=entorno,
                              cwd=instalacion / "runtime")
                comprobar_sin_errores(datos, evidencia)

            def datos_dentro_del_programa(evidencia):
                # Datos que quedaron dentro de app\ de 1.7.1 (p. ej. si alguien abrió app\agencia.py con otro
                # Python): la actualización los aparta a la carpeta de datos, intactos, y sigue.
                otra = temporal / "otra instalacion"
                anterior = temporal / "Servitotal-1.7.1.exe"
                ejecutar(f'"{anterior}" /S /D={otra}', evidencia, timeout=180)
                evidencia["huella"] = crear_base_anterior(otra / "app" / "agencia.db")
                (otra / "app" / "contratos").mkdir()
                (otra / "app" / "contratos" / "contrato_1.html").write_text("<p>Servitotal</p>", encoding="utf-8")
                ejecutar(f'"{exe}" /S /D={otra}', evidencia, timeout=300)
                if (otra / "app" / "agencia.db").exists() or not (otra / "runtime" / "pythonw.exe").exists():
                    raise RuntimeError("La actualización no apartó los datos o no quedó instalada")
                apartadas = list(datos.glob("Recuperado de la instalacion anterior*/app/agencia.db"))
                evidencia["apartadas"] = [str(r) for r in apartadas]
                if len(apartadas) != 1 or hashlib.sha256(apartadas[0].read_bytes()).hexdigest() != evidencia["huella"]:
                    raise RuntimeError("Los datos apartados no están intactos en la carpeta de datos")
                if not (apartadas[0].parent / "contratos" / "contrato_1.html").is_file():
                    raise RuntimeError("No se apartaron los contratos")
                ejecutar(f'"{otra / "Desinstalar.exe"}" /S _?={otra}', {}, timeout=120)

            def datos_anteriores(evidencia):
                anterior = escritorio / "Agencia anterior ñ" / "agencia.db"
                evidencia["huella_antes"] = crear_base_anterior(anterior)
                comando, inicio = comando_escritorio({})
                usar_programa(comando, windows, evidencia, entorno=entorno, cwd=inicio,
                              respuestas={"Traer sus datos": IDYES, "Datos recuperados": "unico"})
                comprobar_sin_errores(datos, evidencia)
                evidencia["datos"] = contar(datos / "agencia.db")
                if evidencia["datos"] != {"clientes": 1, "trabajadoras": 1, "colocaciones": 1}:
                    raise RuntimeError("No se trajeron los datos de la versión anterior")
                if hashlib.sha256(anterior.read_bytes()).hexdigest() != evidencia["huella_antes"]:
                    raise RuntimeError("Se modificó la base de la versión anterior")

            def otro_python(evidencia):
                comando, inicio = comando_escritorio({})
                usar_programa(comando, windows, evidencia, entorno=entorno_de_otro_python(entorno, temporal), cwd=inicio)
                comprobar_sin_errores(datos, evidencia)
                if contar(datos / "agencia.db")["clientes"] != 1:
                    raise RuntimeError("Los datos traídos no se conservaron entre aperturas")

            def desinstalar(evidencia):
                # _?= último y sin comillas (como /D=): así NSIS desinstala aquí mismo y espera a terminar.
                ejecutar(f'"{instalacion / "Desinstalar.exe"}" /S _?={instalacion}', evidencia, timeout=120)
                if (instalacion / "runtime").exists() or (instalacion / "app").exists():
                    raise RuntimeError("La desinstalación dejó el programa")
                if contar(datos / "agencia.db")["clientes"] != 1:
                    raise RuntimeError("La desinstalación no conservó los datos de la agencia")
                evidencia["datos_conservados"] = True

            anterior_ok = False
            if opciones.sin_anterior:
                for nombre in ("instalacion_anterior", "en_uso", "datos_dentro_del_programa"):
                    informe["pasos"][nombre]["estado"] = "omitido_por_opcion"
            elif probar("instalacion_anterior", instalar_anterior):
                anterior_ok = probar("en_uso", en_uso)
            if probar("instalacion", instalar_nueva):
                probar("defender_instalado", lambda evidencia: analizar_con_defender(instalacion, evidencia))
                probar("runtime_app", runtime_app)
                if probar("acceso_directo", abrir_acceso):
                    probar("icono_anclado_antiguo", icono_anclado_antiguo)
                    if probar("datos_anteriores", datos_anteriores):
                        probar("entorno_de_otro_python", otro_python)
                    if probar("desinstalacion", desinstalar) and not opciones.sin_anterior:
                        probar("datos_dentro_del_programa", datos_dentro_del_programa)
            informe["actualizacion_desde_171"] = anterior_ok
    except BaseException:
        informe["error_general"] = traceback.format_exc()
    finally:
        informe["ok"] = (not informe.get("error_general")
                         and all(paso["estado"] in ("correcto", "omitido_por_opcion")
                                 for paso in informe["pasos"].values()))
        opciones.evidencia.parent.mkdir(parents=True, exist_ok=True)
        opciones.evidencia.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(informe, ensure_ascii=True, indent=2))   # la consola de Windows puede no ser UTF-8
    return 0 if informe["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
