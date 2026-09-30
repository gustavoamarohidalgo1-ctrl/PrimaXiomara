"""Arranque de Servitotal cuando Python se abre sin argumentos (se copia como Lib/sitecustomize.py del Python incluido).

- ZIP portable: Servitotal.exe y Diagnosticar Servitotal.exe son pythonw.exe y python.exe de Python Software
  Foundation con otro nombre: los bytes y la firma Authenticode no cambian, así que Windows (SmartScreen y el Control
  inteligente de aplicaciones) los reconoce como Python y no hace falta ningún .bat ni ejecutable propio sin firma.
- Instalador: un ícono anclado a la barra de tareas por una versión anterior guarda runtime\\pythonw.exe sin
  argumentos; al pulsarlo, ese pythonw.exe abre Servitotal en vez de no hacer nada.

Python importa este módulo al iniciar. Sólo actúa si se abrió sin argumentos; con cualquier argumento Python se
comporta como siempre."""
import os
import sys

_PYTHON = ("python.exe", "pythonw.exe")   # en el ZIP, con su nombre original se comportan como Python normal


def _elegir():
    """(lanzador, muestra consola) según dónde está este Python, o None si no corresponde abrir nada."""
    carpeta = os.path.dirname(os.path.abspath(sys.executable))
    nombre = os.path.basename(sys.executable).lower()
    portable = os.path.join(carpeta, "app", "abrir_portable.pyw")
    instalado = os.path.join(os.path.dirname(carpeta), "app", "iniciar.pyw")
    if os.path.isfile(portable) and nombre not in _PYTHON:
        # Cualquier otro nombre (también «Servitotal (2).exe», que Windows crea al copiar) abre el programa.
        return portable, nombre.startswith("diagnosticar")
    if os.path.isfile(instalado) and nombre == "pythonw.exe":
        return instalado, False
    return None


def _abrir(lanzador, consola):
    import runpy
    import threading
    local = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    sys.argv = [lanzador, "--datos", os.path.join(local, "Servitotal")]
    codigo = 1
    try:
        runpy.run_path(lanzador, run_name="__main__")
        codigo = 0
    except SystemExit as salida:
        codigo = salida.code if isinstance(salida.code, int) else 0 if salida.code is None else 1
    except BaseException:
        import traceback
        traceback.print_exc()
    # Esperar las copias de seguridad que sigan en marcha y salir aquí: sin argumentos, Python abriría después
    # su consola interactiva.
    for hilo in threading.enumerate():
        if hilo is not threading.current_thread() and not hilo.daemon:
            hilo.join()
    if consola:
        print(f"\nServitotal terminó (código {codigo}).")
        try:
            input("Presione Enter para cerrar esta ventana...")
        except (EOFError, OSError, RuntimeError):
            pass
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.flush()
        except Exception:
            pass
    os._exit(codigo)


if sys.platform == "win32" and sys.argv == [""]:
    _eleccion = _elegir()
    if _eleccion:
        _abrir(*_eleccion)
