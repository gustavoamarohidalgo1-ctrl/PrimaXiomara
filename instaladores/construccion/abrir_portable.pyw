"""Abre Servitotal y muestra los fallos de inicio anteriores a la interfaz."""
from pathlib import Path
import ctypes
from datetime import datetime
import os
import sys
import traceback


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    # Usar las bibliotecas Tcl/Tk incluidas, aunque exista otro Python instalado.
    for nombre in ("TCL_LIBRARY", "TK_LIBRARY"):
        os.environ.pop(nombre, None)
    try:
        import agencia
        agencia.main()
        return 0
    except SystemExit as salida:   # agencia ya mostró su propio aviso antes de salir
        return salida.code if isinstance(salida.code, int) else 0 if salida.code is None else 1
    except BaseException:
        detalle = traceback.format_exc()
        if "--datos" in sys.argv[:-1]:
            datos = Path(sys.argv[sys.argv.index("--datos") + 1])
        else:
            datos = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Servitotal"
        registro = datos / "errores_inicio.log"
        mensaje = "No se pudo abrir Servitotal.\n\n"
        try:
            datos.mkdir(parents=True, exist_ok=True)
            with registro.open("a", encoding="utf-8") as archivo:
                archivo.write(f"\n{datetime.now().isoformat()}\n{detalle}")
            mensaje += f"El detalle se guardó en:\n{registro}\n\n"
        except OSError:
            mensaje += "No se pudo guardar el detalle del error.\n\n"
        mensaje += "Abra Diagnosticar Servitotal.bat para ver el error en pantalla."
        if sys.stderr is not None:
            sys.stderr.write(detalle)
        try:
            ctypes.windll.user32.MessageBoxW(None, mensaje, "Servitotal — No se pudo abrir", 0x10)
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
