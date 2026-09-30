"""Arranque del ZIP portable de Servitotal (se copia como Lib/sitecustomize.py).

Servitotal.exe y Diagnosticar Servitotal.exe son pythonw.exe y python.exe de Python Software Foundation con otro
nombre: los bytes y la firma Authenticode no cambian, así que Windows (SmartScreen y el Control inteligente de
aplicaciones) los reconoce como Python y no hace falta ningún .bat ni ejecutable propio sin firma.

Python importa este módulo al iniciar. Si se abrió uno de esos dos archivos sin argumentos (doble clic), arranca el
programa; con cualquier argumento Python se comporta como siempre."""
import os
import sys

_PROPIOS = {"servitotal.exe": False, "diagnosticar servitotal.exe": True}   # nombre -> muestra consola


def _abrir():
    import runpy
    import threading
    consola = _PROPIOS[os.path.basename(sys.executable).lower()]
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


if sys.argv == [""] and os.path.basename(sys.executable).lower() in _PROPIOS:
    _abrir()
