"""Prepara sólo el código y recursos públicos de Servitotal para Python oficial."""
from pathlib import Path
import hashlib
import os
import tempfile
import zipfile


RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "instaladores/Servitotal-1.7.2-Windows-Python.zip"
NOMBRE = "Servitotal-1.7.2-Python"
ARCHIVOS = ("agencia.py", "contratos_servitotal.py", "logo.png", "icono.png", "icono.ico")
LEEME = """SERVITOTAL 1.7.2 — ABRIR CON PYTHON OFICIAL EN WINDOWS DE 64 BITS

1. Descargue el instalador completo Python 3.14.7 de 64 bits desde:
   https://www.python.org/downloads/release/python-3147/
   Elija Windows installer (64-bit), no Windows embeddable package.
2. Abra el instalador de Python. Marque Add python.exe to PATH.
   En Customize installation mantenga tcl/tk and IDLE y el lanzador Python.
   En las opciones avanzadas mantenga Associate files with Python.
   Instale para su usuario; no necesita instalar paquetes con pip.
3. Clic derecho sobre Servitotal-1.7.2-Windows-Python.zip > Extraer todo.
   Conserve toda la carpeta extraída; puede guardarla en Documentos.
4. Doble clic en Abrir Servitotal.pyw desde esa carpeta.
   Si Windows pregunta con qué abrirlo, elija Python (no el de Microsoft Store).

Este paquete contiene el mismo programa 1.7.2 y sus gráficos originales.
No incluye Python, EXE propio ni registros reales del negocio.
El archivo .pyw es el acceso al programa: no abra app/agencia.py directamente.

Los datos se guardan en %LOCALAPPDATA%\\Servitotal, igual que con el instalador.
Guarde y cierre cualquier Servitotal abierto antes de usar esta versión.
Si su versión anterior guardaba agencia.db junto al programa, conserve esa carpeta:
la primera vez el programa la busca en Escritorio, Documentos y Descargas y ofrece
traer esos datos. También puede traerlos con Ctrl+Shift+B > Traer datos de otra carpeta.

Si no abre, abra Diagnosticar Servitotal.py con Python para ver el error.
También puede escribir en la terminal de esta carpeta:
python "Diagnosticar Servitotal.py"
Los errores que llegan al lanzador se guardan en
%LOCALAPPDATA%\\Servitotal\\errores_inicio.log.

Python oficial tiene su propia firma; esa firma no firma el código de Servitotal.
Windows o el antivirus todavía pueden mostrar advertencias o bloquearlo.
Mantenga las protecciones activas. Si hay un bloqueo, conserve el texto exacto.
Origen: https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara
"""
DIAGNOSTICAR = '''"""Muestra los errores de inicio de Servitotal en la consola de Python."""
from pathlib import Path
import runpy
import traceback

codigo = 1
try:
    lanzador = runpy.run_path(str(Path(__file__).with_name("Abrir Servitotal.pyw")))
    codigo = lanzador["main"]()
except BaseException:
    traceback.print_exc()
try:
    input("\\nPresione Enter para cerrar esta comprobación...")
except EOFError:
    pass
raise SystemExit(codigo)
'''


def agregar(paquete, nombre, contenido):
    # Metadatos fijos: el mismo código produce el mismo ZIP.
    info = zipfile.ZipInfo(f"{NOMBRE}/{nombre}", date_time=(2026, 9, 29, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    paquete.writestr(info, contenido, compresslevel=9)


def main():
    with tempfile.TemporaryDirectory(prefix="servitotal-python-") as temporal:
        nuevo = Path(temporal) / SALIDA.name
        with zipfile.ZipFile(nuevo, "w") as paquete:
            for nombre in ARCHIVOS:
                origen = RAIZ / nombre
                if origen.is_symlink() or not origen.is_file():
                    raise RuntimeError("Recurso del programa no válido: " + nombre)
                agregar(paquete, "app/" + nombre, origen.read_bytes())
            agregar(paquete, "Abrir Servitotal.pyw", Path(__file__).with_name("abrir_python.pyw").read_bytes())
            agregar(paquete, "Diagnosticar Servitotal.py", DIAGNOSTICAR.encode("utf-8"))
            agregar(paquete, "LEEME-INSTALAR.txt", LEEME.replace("\n", "\r\n").encode("utf-8"))
        with zipfile.ZipFile(nuevo) as paquete:
            if paquete.testzip() is not None or len(paquete.namelist()) != 8:
                raise RuntimeError("El ZIP no pasó la comprobación de integridad")
        os.replace(nuevo, SALIDA)
    print(f"ZIP creado: {SALIDA.name} ({SALIDA.stat().st_size} bytes)")
    print("SHA256: " + hashlib.sha256(SALIDA.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
