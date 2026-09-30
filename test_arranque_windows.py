"""Un fallo al abrir nunca debe pasar en silencio: pythonw no tiene consola y la usuaria solo vería que no pasa nada."""
from pathlib import Path
from unittest import mock
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import agencia

RAIZ = Path(__file__).resolve().parent
LANZADOR = RAIZ / "instaladores" / "construccion" / "iniciar.pyw"


def entorno_limpio(**extra):
    entorno = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME", "AGENCIA_DATOS")}
    entorno.update(PYTHONIOENCODING="utf-8", **extra)
    return entorno


# Abre un guion como lo haría Windows, pero cambia la ventana de aviso por texto: una ventana modal dejaría la
# prueba esperando a que alguien pulse Aceptar.
SIN_VENTANAS = """
import runpy, sys
if sys.platform == "win32":
    import ctypes
    ctypes.windll.user32.MessageBoxW = lambda _v, texto, titulo, _t: print("AVISO:", titulo, texto, file=sys.stderr)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


def ejecutar(guion, *argumentos, cwd, opciones=(), **extra):
    return subprocess.run([sys.executable, *opciones, "-c", SIN_VENTANAS, str(guion), *argumentos], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                          env=entorno_limpio(**extra))


class ArranqueVisible(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(prefix="arranque ñ ")
        self.carpeta = Path(self.temporal.name)

    def tearDown(self):
        self.temporal.cleanup()

    def test_actualizar_solo_agencia_py_avisa_que_falta_el_contrato(self):
        shutil.copy2(RAIZ / "agencia.py", self.carpeta / "agencia.py")
        proceso = ejecutar(self.carpeta / "agencia.py", cwd=self.carpeta)
        self.assertEqual(proceso.returncode, 1)
        self.assertIn("contratos_servitotal.py", proceso.stderr + proceso.stdout)
        if sys.platform == "win32":
            self.assertIn("AVISO: Servitotal", proceso.stderr)
        self.assertNotIn("Traceback", proceso.stderr)

    def test_un_fallo_antes_de_la_ventana_se_registra_y_se_muestra(self):
        registro = self.carpeta / "errores.log"
        with mock.patch.object(agencia, "main", side_effect=RuntimeError("Tk no pudo arrancar")), \
                mock.patch.object(agencia, "_aviso_de_inicio") as aviso, \
                mock.patch.object(agencia, "ERRORES_PATH", str(registro)):
            with self.assertRaises(SystemExit) as salida:
                agencia.arrancar()
        self.assertEqual(salida.exception.code, 1)
        aviso.assert_called_once()
        self.assertIn("Tk no pudo arrancar", aviso.call_args[0][0])
        self.assertIn("Tk no pudo arrancar", registro.read_text(encoding="utf-8"))

    def preparar_lanzador(self, contenido):
        app = self.carpeta / "app con espacios"
        app.mkdir()
        shutil.copy2(LANZADOR, app / "iniciar.pyw")
        (app / "agencia.py").write_text(contenido, encoding="utf-8")
        return app

    def test_el_lanzador_del_instalador_guarda_el_error_de_inicio(self):
        app = self.preparar_lanzador("def main():\n    raise RuntimeError('fallo ficticio de inicio')\n")
        datos = self.carpeta / "datos ñ"
        proceso = ejecutar(app / "iniciar.pyw", "--datos", str(datos), cwd=self.carpeta, opciones=("-E", "-s"))
        self.assertEqual(proceso.returncode, 1)
        self.assertIn("fallo ficticio de inicio", (datos / "errores_inicio.log").read_text(encoding="utf-8"))
        if sys.platform == "win32":
            self.assertIn("AVISO: Servitotal", proceso.stderr)

    def test_el_lanzador_respeta_la_salida_ya_avisada_por_el_programa(self):
        app = self.preparar_lanzador("raise SystemExit(1)\n")
        datos = self.carpeta / "datos"
        proceso = ejecutar(app / "iniciar.pyw", "--datos", str(datos), cwd=self.carpeta)
        self.assertEqual(proceso.returncode, 1)
        self.assertFalse((datos / "errores_inicio.log").exists())   # el programa ya mostró su propio aviso

    def test_el_lanzador_abre_el_programa_como_modulo(self):
        app = self.preparar_lanzador("import sys\ndef main():\n    print('ABIERTO', sys.argv[1:])\n")
        proceso = ejecutar(app / "iniciar.pyw", "--datos", "X", cwd=self.carpeta)
        self.assertEqual(proceso.returncode, 0, proceso.stderr)
        self.assertIn("ABIERTO ['--datos', 'X']", proceso.stdout)


@unittest.skipUnless(sys.platform == "win32", "TCL_LIBRARY sólo decide en Windows qué Tcl/Tk se carga")
class TclDeOtroPrograma(unittest.TestCase):
    def test_un_tcl_library_ajeno_no_impide_abrir_la_ventana(self):
        with tempfile.TemporaryDirectory(prefix="tcl ajeno ") as ajeno:
            codigo = ("import os, agencia, tkinter; r = tkinter.Tk(); r.update(); "
                      "print('TK', r.tk.call('info', 'patchlevel'), os.environ['TCL_LIBRARY']); r.destroy()")
            proceso = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True, text=True,
                                     encoding="utf-8", timeout=60,
                                     env=entorno_limpio(TCL_LIBRARY=ajeno, TK_LIBRARY=ajeno,
                                                        AGENCIA_DATOS=os.path.join(ajeno, "datos")))
        self.assertEqual(proceso.returncode, 0, proceso.stderr)
        self.assertIn("TK ", proceso.stdout)
        propia = os.path.join(sys.base_prefix, "tcl", f"tcl{agencia.tk.TclVersion}")
        if os.path.isdir(propia):       # Tcl 9 (Python 3.14) lleva su biblioteca dentro de la DLL
            self.assertIn(propia, proceso.stdout)


if __name__ == "__main__":
    unittest.main()
