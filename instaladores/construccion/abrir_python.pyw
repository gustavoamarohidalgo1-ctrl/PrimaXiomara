"""Abre Servitotal con Python oficial y la carpeta de datos de la instalación."""
from pathlib import Path
import ctypes
from datetime import datetime
import os
import sys
import traceback


class Aviso(Exception):
    """Motivo conocido por el que este acceso no debe abrir Servitotal: se muestra tal cual."""


def mostrar(mensaje):
    if sys.stderr is not None:
        sys.stderr.write(mensaje + "\n")
    try:
        ctypes.windll.user32.MessageBoxW(None, mensaje, "Servitotal — No se pudo abrir", 0x50010)   # al frente
    except Exception:
        pass


def main():
    datos = None
    try:
        if sys.platform != "win32":
            raise Aviso("Este acceso corresponde a Servitotal para Windows.")
        if "\\windowsapps\\" in (sys.base_prefix + "\\").lower():
            # El Python de Microsoft Store guarda en una carpeta privada lo que se escribe en LOCALAPPDATA:
            # los datos no aparecerían en la versión instalada y se perderían al desinstalar ese Python.
            raise Aviso("Este archivo se abrió con el Python de Microsoft Store, que guarda los datos en una "
                        "carpeta privada. Instale Python desde python.org (vea LEEME-INSTALAR.txt), o use "
                        "el instalador Servitotal-Windows-x64.exe o el ZIP portable, que ya traen Python.")
        local = os.environ.get("LOCALAPPDATA")
        if not local or not Path(local).is_absolute():
            raise Aviso("Windows no indicó una carpeta LOCALAPPDATA válida para este usuario.")
        datos = Path(local) / "Servitotal"
        # La fuente calcula sus rutas al importarse: fijar los datos primero.
        sys.argv = [str(Path(__file__).resolve()), "--datos", str(datos)]
        sys.path.insert(0, str(Path(__file__).resolve().parent / "app"))
        for nombre in ("TCL_LIBRARY", "TK_LIBRARY"):
            os.environ.pop(nombre, None)
        import agencia
        agencia.main()
        return 0
    except SystemExit as salida:   # agencia ya mostró su propio aviso antes de salir
        return salida.code if isinstance(salida.code, int) else 0 if salida.code is None else 1
    except Aviso as aviso:
        mostrar(f"No se pudo abrir Servitotal.\n\n{aviso}")
        return 1
    except BaseException:
        detalle = traceback.format_exc()
        mensaje = "No se pudo abrir Servitotal.\n\n"
        if datos is not None:
            registro = datos / "errores_inicio.log"
            try:
                datos.mkdir(parents=True, exist_ok=True)
                with registro.open("a", encoding="utf-8") as archivo:
                    archivo.write(f"\n{datetime.now().isoformat()}\n{detalle}")
                mensaje += f"El detalle se guardó en:\n{registro}\n\n"
            except OSError:
                mensaje += "No se pudo guardar el detalle del error.\n\n"
        mensaje += "Compruebe que extrajo todo el ZIP y que Python incluye tcl/tk.\n"
        mensaje += "Si sigue fallando, abra Diagnosticar Servitotal.py con Python para ver el error.\n\n"
        mensaje += detalle.strip().splitlines()[-1][:300]
        if sys.stderr is not None:
            sys.stderr.write(detalle)
        mostrar(mensaje)
        return 1


if __name__ == "__main__":
    sys.exit(main())
