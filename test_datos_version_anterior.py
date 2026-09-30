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


def programa(carpeta, eslogan):
    """El agencia.py que acompaña a la base en la carpeta de la versión anterior (sólo su identidad)."""
    Path(carpeta).mkdir(parents=True, exist_ok=True)
    (Path(carpeta) / "agencia.py").write_text(f'AGENCIA_NOMBRE = "Agencia de Empleos"\nAGENCIA_ESLOGAN = "{eslogan}"\n',
                                             encoding="utf-8")


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
        with self.preparar(externa=None):
            aviso, oferta = agencia.preparar_base()
        self.assertIsNone(aviso)
        self.assertEqual(os.path.normcase(oferta["ruta"]), os.path.normcase(anterior))
        self.assertIsNone(oferta["alternativa"])
        self.assertFalse(os.path.exists(self.actual))           # buscar nunca crea la base nueva
        with self.preparar(externa=None, buscar=False):         # en Mac no se recorren las carpetas personales
            self.assertEqual(agencia.preparar_base(), (None, None))

    def preparar(self, externa, buscar=True):
        from contextlib import ExitStack
        pila = ExitStack()
        for nombre, valor in (("DB_PATH", self.actual), ("CARPETA_RESPALDOS", str(self.casa / "datos nuevos" / "respaldos")),
                              ("carpetas_externas", lambda config=None: [externa] if externa else []),
                              ("carpetas_personales", lambda: [str(self.escritorio)]),
                              ("BUSCAR_VERSION_ANTERIOR", buscar)):
            pila.enter_context(mock.patch.object(agencia, nombre, valor))
        return pila

    def test_una_copia_diaria_mas_vieja_no_tapa_la_base_anterior_mas_reciente(self):
        externa = self.casa / "Documentos" / "Respaldos Servitotal"
        externa.mkdir(parents=True)
        copia = base_anterior(externa / "agencia-20260929.db", clientes=("Ana",))
        os.utime(copia, (1_700_000_000, 1_700_000_000))           # la copia de la mañana
        anterior = base_anterior(self.escritorio / "Agencia" / "agencia.db", clientes=("Ana", "Beto"))
        with self.preparar(externa=str(externa)):
            _, oferta = agencia.preparar_base()
        self.assertEqual(os.path.normcase(oferta["ruta"]), os.path.normcase(anterior))
        self.assertEqual(os.path.normcase(oferta["alternativa"]["ruta"]), os.path.normcase(copia))
        os.utime(anterior, (1_600_000_000, 1_600_000_000))        # ahora la copia es la más reciente
        with self.preparar(externa=str(externa)):
            _, oferta = agencia.preparar_base()
        self.assertEqual(os.path.normcase(oferta["ruta"]), os.path.normcase(copia))
        self.assertEqual(os.path.normcase(oferta["alternativa"]["ruta"]), os.path.normcase(anterior))

    def test_carpetas_personales_existen_y_no_se_repiten(self):
        carpetas = agencia.carpetas_personales()
        self.assertTrue(carpetas)
        self.assertTrue(all(os.path.isdir(c) for c in carpetas))
        claves = [os.path.normcase(os.path.abspath(c)) for c in carpetas]
        self.assertEqual(len(claves), len(set(claves)))


    def test_la_base_de_otra_agencia_no_se_ofrece_aunque_sea_la_mas_reciente(self):
        # Nombres reales: la carpeta del repositorio descargado y el programa de la otra agencia no dicen «Servitotal».
        propia = base_anterior(self.escritorio / "PrimaXiomara-main" / "agencia.db")
        programa(self.escritorio / "PrimaXiomara-main", "Servitotal")
        ajena = base_anterior(self.escritorio / "Tia_Programa-main" / "agencia.db", clientes=("Otra agencia",))
        programa(self.escritorio / "Tia_Programa-main", "Servicio Exclusivo")
        os.utime(propia, (1_700_000_000, 1_700_000_000))            # la de la otra agencia es más reciente
        self.assertEqual(agencia.identidad_de_base(propia), "propia")
        self.assertEqual(agencia.identidad_de_base(ajena), "ajena")
        oferta = agencia.buscar_base_anterior(self.actual, [str(self.escritorio)])
        self.assertEqual(os.path.normcase(oferta["ruta"]), os.path.normcase(propia))
        self.assertEqual(oferta["otras"], [])                       # la ajena ni siquiera se menciona
        self.assertEqual(oferta["ejemplos"], ["Clienta ficticia Ñuñoa"])
        os.remove(propia)
        self.assertIsNone(agencia.buscar_base_anterior(self.actual, [str(self.escritorio)]))

    def test_una_base_propia_vieja_gana_a_una_desconocida_y_los_contratos_identifican_la_agencia(self):
        propia = base_anterior(self.escritorio / "Respaldo" / "agencia.db")
        os.utime(propia, (1_600_000_000, 1_600_000_000))
        (self.escritorio / "Respaldo" / "contratos").mkdir()
        (self.escritorio / "Respaldo" / "contratos" / "contrato_1.html").write_text(
            "<p>AGENCIA DE EMPLEOS S.T SERVITOTAL</p>", encoding="utf-8")
        desconocida = base_anterior(self.escritorio / "Agencia.exe carpeta" / "agencia.db")
        ajena = base_anterior(self.escritorio / "Otro" / "agencia.db")
        (self.escritorio / "Otro" / "contratos").mkdir()
        (self.escritorio / "Otro" / "contratos" / "contrato_1.html").write_text("<p>Servicio Exclusivo</p>",
                                                                               encoding="utf-8")
        self.assertEqual([agencia.identidad_de_base(r) for r in (propia, desconocida, ajena)],
                         ["propia", "desconocida", "ajena"])
        oferta = agencia.buscar_base_anterior(self.actual, [str(self.escritorio)])
        self.assertEqual(os.path.normcase(oferta["ruta"]), os.path.normcase(propia))
        self.assertEqual([os.path.normcase(r) for r in oferta["otras"]], [os.path.normcase(desconocida)])

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
        self.assertIn("Clienta ficticia Ñuñoa", self.mensajes[0][1])        # para reconocer sus propios datos
        self.assertIn("Compruebe que son los datos", self.mensajes[0][1])  # sin agencia.py no se sabe de quién es

    def test_la_oferta_menciona_otras_bases_encontradas(self):
        base_anterior(self.base / "Escritorio" / "Agencia Servitotal" / "agencia.db")
        programa(self.base / "Escritorio" / "Agencia Servitotal", "Servitotal")
        otra = base_anterior(self.base / "Escritorio" / "Otra carpeta" / "agencia.db", clientes=("Otra",))
        self.mensajes.clear()
        with mock.patch.object(agencia.messagebox, "askyesno", side_effect=lambda titulo, texto, **k:
                               (self.mensajes.append((titulo, texto)), False)[1]):
            self.app.ofrecer_recuperacion(agencia.buscar_base_anterior(carpetas=[str(self.base / "Escritorio")]))
        self.assertIn(otra, self.mensajes[0][1])
        self.assertIn("Traer datos de otra carpeta", self.mensajes[0][1])
        self.assertNotIn("Compruebe que son los datos", self.mensajes[0][1])   # su agencia.py dice Servitotal
        self.assertEqual(self.app.db.todos("clientes"), [])            # «No»: no se trae nada

    def test_si_dice_no_a_la_copia_se_le_ofrece_la_version_anterior(self):
        anterior = base_anterior(self.base / "Escritorio" / "Agencia" / "agencia.db")
        copia = base_anterior(self.base / "copia" / "agencia-20260929.db", clientes=("Copia vieja",))
        oferta = dict(agencia.listar_copias([(str(self.base / "copia"), "Documentos")])[0],
                      alternativa=agencia.buscar_base_anterior(carpetas=[str(self.base / "Escritorio")]))
        respuestas = iter([False, True])
        with mock.patch.object(agencia.messagebox, "askyesno", side_effect=lambda titulo, texto, **k:
                               (self.mensajes.append((titulo, texto)), next(respuestas))[1]):
            self.app.ofrecer_recuperacion(oferta)
        self.assertEqual([m[0] for m in self.mensajes[:2]], ["Recuperar sus datos", "Traer los datos de la versión anterior"])
        self.assertIn(anterior, self.mensajes[0][1])
        self.assertEqual([c["nombre"] for c in self.app.db.todos("clientes")], ["Clienta ficticia Ñuñoa"])
        self.assertTrue(os.path.exists(copia))

    def test_elegir_a_mano_una_base_de_otra_agencia_pide_confirmar(self):
        ajena = base_anterior(self.base / "Tia" / "agencia.db", clientes=("Otra agencia",))
        programa(self.base / "Tia", "Servicio Exclusivo")
        dialogo = agencia.DialogoCopias(self.root, self.app)
        try:
            preguntas = []
            with mock.patch("tkinter.filedialog.askopenfilename", return_value=ajena), \
                    mock.patch.object(agencia.messagebox, "askyesno", side_effect=lambda titulo, texto, **k:
                                      (preguntas.append((titulo, k.get("default"))), False)[1]):
                dialogo.traer_de_archivo()
            self.assertEqual(preguntas, [("Datos de otro programa", "no")])
            self.assertEqual(self.app.db.todos("clientes"), [])
        finally:
            dialogo.destroy()

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
