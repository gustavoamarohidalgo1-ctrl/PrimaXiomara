"""Comportamientos propios de Windows: arranque sin consola (pythonw), Tcl/Tk ajeno, rutas de red y archivos que
otro programa mantiene abiertos."""
from contextlib import closing
from pathlib import Path
from unittest import mock
import os
import shutil
import sqlite3
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


class BasesEnOtrasRutas(unittest.TestCase):
    def test_uri_de_rutas_locales_con_acentos_espacios_y_almohadilla(self):
        with tempfile.TemporaryDirectory(prefix="ruta #1 ñ ") as carpeta:
            ruta = os.path.join(carpeta, "agencia vieja #2.db")
            with closing(sqlite3.connect(ruta)) as con, con:
                con.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY, nombre TEXT)")
                con.execute("INSERT INTO clientes (nombre) VALUES ('Ana')")
            self.assertEqual(agencia.contar_datos(ruta)["clientes"], 1)
            self.assertEqual(agencia.contar_datos(os.path.relpath(ruta))["clientes"], 1)
            self.assertIsNone(agencia.contar_datos(ruta + ".no-existe"))
            self.assertFalse(os.path.exists(ruta + ".no-existe"))

    @unittest.skipUnless(sys.platform == "win32", "las rutas UNC sólo existen en Windows")
    def test_una_base_en_una_carpeta_de_red_se_puede_leer(self):
        with tempfile.TemporaryDirectory(prefix="red ñ ") as carpeta:
            ruta = os.path.join(carpeta, "agencia.db")
            with closing(sqlite3.connect(ruta)) as con, con:
                con.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY, nombre TEXT)")
                con.execute("INSERT INTO clientes (nombre) VALUES ('Ana')")
            unidad, resto = os.path.splitdrive(os.path.realpath(ruta))
            unc = "\\\\localhost\\" + unidad.rstrip(":") + "$" + resto
            if not os.path.exists(unc):
                self.skipTest("este equipo no comparte sus unidades como \\\\localhost\\C$")
            self.assertEqual(agencia.uri_sqlite(unc)[:12], "file:////loc")
            self.assertEqual(agencia.contar_datos(unc)["clientes"], 1)


class CsvAbiertoEnExcel(unittest.TestCase):
    """En Windows no se puede reemplazar un CSV que Excel tiene abierto: la copia .db vale y el aviso no se repite."""

    def test_la_copia_de_la_base_vale_y_el_aviso_es_siempre_el_mismo(self):
        from datetime import datetime
        with tempfile.TemporaryDirectory(prefix="csv abierto ") as carpeta:
            ruta = os.path.join(carpeta, "agencia.db")
            base = agencia.BaseDatos(ruta)
            try:
                base.con.execute("INSERT INTO clientes (nombre) VALUES ('Ana')")
                base.con.commit()
            finally:
                base.con.close()
            externa = os.path.join(carpeta, "Respaldos")
            agencia.copia_externa(ruta, externa, datetime(2026, 9, 28))        # CSV anteriores ya publicados
            original = os.replace

            def reemplazar(origen, destino):
                if str(destino).endswith(".csv"):
                    raise PermissionError(13, "El proceso no tiene acceso al archivo porque está siendo utilizado")
                return original(origen, destino)

            errores = []
            with mock.patch.object(agencia.os, "replace", reemplazar):
                for dia in (29, 30):
                    resultado = agencia.respaldar("auto", ruta=ruta, carpeta=os.path.join(carpeta, "respaldos"),
                                                  externas=[externa], ahora=datetime(2026, 9, dia))
                    self.assertEqual(resultado["externas"], [externa])
                    errores.append(resultado["errores"])
            self.assertEqual(errores[0], errores[1])                          # se avisa una sola vez por sesión
            self.assertIn("Datos legibles", errores[0][0])
            self.assertNotIn(".exportacion-csv-", errores[0][0])
            self.assertTrue(os.path.isfile(os.path.join(externa, "agencia-20260930.db")))
            self.assertTrue(os.path.isfile(os.path.join(externa, "Datos legibles", "Clientes.csv")))
            restos = [n for n in os.listdir(os.path.join(externa, "Datos legibles")) if n.startswith(".exportacion")]
            self.assertEqual(restos, [])


if __name__ == "__main__":
    unittest.main()
