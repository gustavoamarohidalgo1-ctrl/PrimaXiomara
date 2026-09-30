"""La versión anterior guardaba agencia.db junto al programa: la nueva debe encontrarlo y traerlo sin tocarlo."""
from contextlib import closing
from pathlib import Path
from unittest import mock
import hashlib
import os
import sqlite3
import tempfile
import unittest

import agencia
from agencia import restablecer_areas

# Estructura exacta de la versión anterior a la actualización (tres tablas, sin áreas).
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


def base_anterior(ruta, clientes=("Clienta ficticia Ñuñoa",), con_datos=True):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(ruta)) as con, con:
        con.executescript(ESQUEMA_ANTERIOR)
        if con_datos:
            for nombre in clientes:
                con.execute("INSERT INTO clientes (nombre, telefono, tipo_servicio, garantia, estado) "
                            "VALUES (?, '900000000', 'Cama adentro', 'Sí', 'Colocado')", (nombre,))
            con.execute("INSERT INTO trabajadoras (nombre, tipo_servicio, estado) "
                        "VALUES ('Trabajadora ficticia', 'Cama adentro', 'Trabajando')")
            con.execute("INSERT INTO colocaciones (cliente_id, trabajadora_id, sueldo_acordado, porcentaje, comision, "
                        "estado, fecha_inicio, garantia) VALUES ('1', '1', '1500', '50', '750', 'Activa', "
                        "'01/09/2026', 'Sí')")
    return str(ruta)


def huella(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


class BusquedaDeBasesAnteriores(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(prefix="version anterior ñ ")
        self.casa = Path(self.temporal.name)
        self.escritorio = self.casa / "Escritorio"
        self.actual = str(self.casa / "datos nuevos" / "agencia.db")

    def tearDown(self):
        self.temporal.cleanup()

    def test_encuentra_la_carpeta_anterior_y_descarta_vacias_ocultas_y_profundas(self):
        anterior = base_anterior(self.escritorio / "Agencia Servitotal" / "agencia.db")
        base_anterior(self.escritorio / "vacía" / "agencia.db", con_datos=False)
        base_anterior(self.casa / "AppData" / "Local" / "otra" / "agencia.db")
        base_anterior(self.escritorio / "a" / "b" / "c" / "d" / "agencia.db")          # demasiado profunda
        base_anterior(self.escritorio / ".oculta" / "agencia.db")
        copias = agencia.buscar_bases_anteriores([str(self.escritorio), str(self.casa)], actual=self.actual)
        self.assertEqual([os.path.normcase(c["ruta"]) for c in copias], [os.path.normcase(anterior)])
        self.assertEqual((copias[0]["clientes"], copias[0]["trabajadoras"], copias[0]["colocaciones"]), (1, 1, 1))
        self.assertEqual(copias[0]["tipo"], "Versión anterior")

    def test_no_se_ofrece_la_base_abierta_ni_nada_si_ya_hay_datos(self):
        abierta = base_anterior(self.escritorio / "Agencia" / "agencia.db")
        self.assertEqual(agencia.buscar_bases_anteriores([str(self.escritorio)], actual=abierta), [])
        otra = base_anterior(self.escritorio / "Otra" / "agencia.db")
        self.assertIsNone(agencia.buscar_base_anterior(abierta, [str(self.escritorio)]))
        vacia = str(self.casa / "nueva" / "agencia.db")
        self.assertEqual(os.path.normcase(agencia.buscar_base_anterior(vacia, [str(self.escritorio)])["ruta"]),
                         os.path.normcase(otra))

    def test_la_mas_reciente_va_primero_y_un_error_no_impide_abrir(self):
        vieja = base_anterior(self.escritorio / "vieja" / "agencia.db")
        nueva = base_anterior(self.escritorio / "nueva" / "agencia.db", clientes=("Una", "Dos"))
        os.utime(vieja, (1_700_000_000, 1_700_000_000))
        os.utime(nueva, (1_750_000_000, 1_750_000_000))
        copias = agencia.buscar_bases_anteriores([str(self.escritorio)], actual=self.actual)
        self.assertEqual([c["clientes"] for c in copias], [2, 1])
        with mock.patch.object(agencia, "buscar_bases_anteriores", side_effect=PermissionError("sin acceso")):
            self.assertIsNone(agencia.buscar_base_anterior(self.actual))

    def test_preparar_base_ofrece_la_version_anterior_si_no_hay_copias(self):
        anterior = base_anterior(self.escritorio / "Agencia" / "agencia.db")
        with mock.patch.object(agencia, "DB_PATH", self.actual), \
                mock.patch.object(agencia, "CARPETA_RESPALDOS", str(self.casa / "datos nuevos" / "respaldos")), \
                mock.patch.object(agencia, "carpetas_externas", lambda config=None: []), \
                mock.patch.object(agencia, "carpetas_personales", lambda: [str(self.escritorio)]):
            aviso, oferta = agencia.preparar_base()
        self.assertIsNone(aviso)
        self.assertEqual(os.path.normcase(oferta["ruta"]), os.path.normcase(anterior))
        self.assertFalse(os.path.exists(self.actual))           # buscar nunca crea la base nueva

    def test_carpetas_personales_existen_y_no_se_repiten(self):
        carpetas = agencia.carpetas_personales()
        self.assertTrue(carpetas)
        self.assertTrue(all(os.path.isdir(c) for c in carpetas))
        claves = [os.path.normcase(os.path.abspath(c)) for c in carpetas]
        self.assertEqual(len(claves), len(set(claves)))


    def test_con_varias_bases_prefiere_la_de_servitotal_y_avisa_de_las_otras(self):
        otra = base_anterior(self.escritorio / "Servicio Exclusivo" / "agencia.db", clientes=("Otra agencia",))
        propia = base_anterior(self.escritorio / "Agencia Servitotal" / "agencia.db")
        os.utime(propia, (1_700_000_000, 1_700_000_000))          # la de otra agencia es más reciente
        oferta = agencia.buscar_base_anterior(self.actual, [str(self.escritorio)])
        self.assertEqual(os.path.normcase(oferta["ruta"]), os.path.normcase(propia))
        self.assertEqual([os.path.normcase(r) for r in oferta["otras"]], [os.path.normcase(otra)])


class TraerDatosAnterioresEnElPrograma(unittest.TestCase):
    def setUp(self):
        try:
            self.root = agencia.tk.Tk()
        except agencia.tk.TclError:
            self.skipTest("no hay pantalla disponible")
        self.root.withdraw()
        self.temporal = tempfile.TemporaryDirectory(prefix="traer datos ñ ")
        base = Path(self.temporal.name)
        self.base = base
        self.respaldos = str(base / "nuevo" / "respaldos")
        self.parches = [
            mock.patch.object(agencia, "DB_PATH", str(base / "nuevo" / "agencia.db")),
            mock.patch.object(agencia, "CARPETA_RESPALDOS", self.respaldos),
            mock.patch.object(agencia, "CONFIG_PATH", str(base / "nuevo" / "configuracion.json")),
            mock.patch.object(agencia, "carpetas_externas", lambda config=None: [str(base / "externa")]),
            mock.patch.object(agencia.tk.Toplevel, "grab_set", lambda self: None)]
        for parche in self.parches:
            parche.start()
        os.makedirs(base / "nuevo", exist_ok=True)
        self.mensajes = []
        for nombre in ("askyesno", "askyesnocancel"):
            p = mock.patch.object(agencia.messagebox, nombre, side_effect=lambda titulo, texto, **k:
                                  (self.mensajes.append((titulo, texto)), True)[1])
            p.start(); self.parches.append(p)
        for nombre in ("showinfo", "showwarning", "showerror"):
            p = mock.patch.object(agencia.messagebox, nombre, side_effect=lambda titulo, texto, **k:
                                  self.mensajes.append((titulo, texto)))
            p.start(); self.parches.append(p)
        self.app = agencia.App(self.root)

    def tearDown(self):
        for parche in reversed(self.parches):
            parche.stop()
        restablecer_areas()
        try:
            self.root.update()
            self.root.destroy()
        except agencia.tk.TclError:
            pass
        self.temporal.cleanup()

    def comprobar_traidos(self, original, antes):
        self.assertEqual([c["nombre"] for c in self.app.db.todos("clientes")], ["Clienta ficticia Ñuñoa"])
        self.assertEqual([t["nombre"] for t in self.app.db.todos("trabajadoras")], ["Trabajadora ficticia"])
        colocacion = self.app.db.todos("colocaciones")[0]
        self.assertEqual((colocacion["sueldo_acordado"], colocacion["estado"]), ("1500", "Activa"))
        self.assertEqual(huella(original), antes)                # la versión anterior queda intacta

    def test_la_oferta_al_abrir_trae_los_datos_de_la_version_anterior(self):
        original = base_anterior(self.base / "Escritorio" / "Agencia" / "agencia.db")
        antes = huella(original)
        oferta = agencia.buscar_base_anterior(carpetas=[str(self.base / "Escritorio")])
        self.app.ofrecer_recuperacion(oferta)
        self.assertEqual(self.mensajes[0][0], "Traer los datos de la versión anterior")
        self.assertIn(original, self.mensajes[0][1])
        self.comprobar_traidos(original, antes)
        self.assertEqual(self.mensajes[-1][0], "Datos recuperados")
        self.assertNotIn("También hay otros", self.mensajes[0][1])

    def test_la_oferta_menciona_otras_bases_encontradas(self):
        base_anterior(self.base / "Escritorio" / "Agencia Servitotal" / "agencia.db")
        otra = base_anterior(self.base / "Escritorio" / "Otro programa" / "agencia.db", clientes=("Otra",))
        self.mensajes.clear()
        with mock.patch.object(agencia.messagebox, "askyesno", side_effect=lambda titulo, texto, **k:
                               (self.mensajes.append((titulo, texto)), False)[1]):
            self.app.ofrecer_recuperacion(agencia.buscar_base_anterior(carpetas=[str(self.base / "Escritorio")]))
        self.assertIn(otra, self.mensajes[0][1])
        self.assertIn("Traer datos de otra carpeta", self.mensajes[0][1])
        self.assertEqual(self.app.db.todos("clientes"), [])            # «No»: no se trae nada

    def test_el_panel_de_copias_trae_un_archivo_elegido_y_rechaza_otro(self):
        original = base_anterior(self.base / "USB" / "agencia.db")
        antes = huella(original)
        dialogo = agencia.DialogoCopias(self.root, self.app)
        try:
            invalido = self.base / "no es una base.db"
            invalido.write_bytes(b"texto cualquiera")
            with mock.patch("tkinter.filedialog.askopenfilename", return_value=str(invalido)):
                dialogo.traer_de_archivo()
            self.assertEqual(self.mensajes[-1][0], "Archivo no válido")
            self.assertEqual(self.app.db.todos("clientes"), [])
            with mock.patch("tkinter.filedialog.askopenfilename", return_value=""):
                dialogo.traer_de_archivo()                      # cancelar no hace nada
            with mock.patch("tkinter.filedialog.askopenfilename", return_value=original.replace(os.sep, "/")):
                dialogo.traer_de_archivo()
            self.comprobar_traidos(original, antes)
            self.assertEqual(self.mensajes[-1][0], "Datos traídos")
        finally:
            dialogo.destroy()

    def test_el_atajo_abre_el_panel_que_trae_datos(self):
        atajo = "<Command-Shift-Key-B>" if agencia.sys.platform == "darwin" else "<Control-Shift-Key-B>"
        self.assertTrue(self.root.bind_all(atajo))
        self.app.abrir_copias()
        self.root.update()
        dialogos = [w for w in self.root.winfo_children() if isinstance(w, agencia.DialogoCopias)]
        self.assertEqual(len(dialogos), 1)
        self.assertTrue(callable(dialogos[0].traer_de_archivo))
        dialogos[0].destroy()

if __name__ == "__main__":
    unittest.main()
