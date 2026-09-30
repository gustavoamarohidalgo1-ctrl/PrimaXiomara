"""Arranque del ZIP portable de Servitotal (se copia como Lib/sitecustomize.py).

Servitotal.exe y Diagnosticar Servitotal.exe son pythonw.exe y python.exe de Python Software Foundation con otro
nombre: los bytes y la firma Authenticode no cambian, así que Windows (SmartScreen y el Control inteligente de
aplicaciones) los reconoce como Python y no hace falta ningún .bat ni ejecutable propio sin firma.

Python importa este módulo al iniciar. Si se abrió uno de esos archivos sin argumentos (doble clic), arranca el
programa; con cualquier argumento Python se comporta como siempre."""
import os
import sys

_PYTHON = ("python.exe", "pythonw.exe")   # con su nombre original se comportan como Python normal


def _abrir():
    import runpy
    import threading
    consola = os.path.basename(sys.executable).lower().startswith("diagnosticar")
    carpeta = os.path.dirname(os.path.abspath(sys.executable))
    lanzador = os.path.join(carpeta, "app", "abrir_portable.pyw")
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


# Cualquier otro nombre (también «Servitotal (2).exe», que Windows crea al copiar) abre el programa.
if (sys.platform == "win32" and sys.argv == [""] and os.path.basename(sys.executable).lower() not in _PYTHON
        and os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "app", "abrir_portable.pyw"))):
    _abrir()
