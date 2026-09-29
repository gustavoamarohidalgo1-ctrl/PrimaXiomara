"""Regresiones de la actualización de Servitotal, con datos totalmente ficticios.

No se abre agencia.db ni se modifica el logo original. El esquema legado reproduce
el de la carpeta recibida; todas las escrituras se realizan en un directorio temporal.
"""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing, contextmanager, ExitStack
from datetime import date, datetime
from types import SimpleNamespace
import unittest
from unittest import mock


CARPETA_PROYECTO = Path(__file__).resolve().parent

# Columnas presentes en la base antigua, incluidas las de versiones anteriores
# que ya no aparecían en los formularios. No contienen información personal.
COLUMNAS_ANTIGUAS = {
    "clientes": (
        "nombre", "dni", "telefono", "direccion", "zona", "fecha_registro",
        "tipo_servicio", "sueldo_ofrecido", "horario", "dias_libres", "personas_hogar",
        "ninos", "mascotas", "tareas", "requisitos", "fecha_necesita", "estado", "notas",
        "garantia", "ocupacion",
    ),
    "trabajadoras": (
        "nombre", "dni", "edad", "telefono", "direccion", "zona", "tipo_servicio",
        "cama_adentro", "experiencia", "sueldo_esperado", "referencias", "doc_dni",
        "doc_antecedentes", "doc_salud", "doc_domicilio", "doc_referencias",
        "entrevista_fecha", "entrevista_resultado", "entrevista_notas", "estado", "notas",
    ),
    "colocaciones": (
        "cliente_id", "trabajadora_id", "entrevista_cliente_fecha",
        "entrevista_cliente_resultado", "entrevista_cliente_notas", "sueldo_acordado",
        "porcentaje", "comision", "comision_pagada", "contrato_firmado", "docs_entregados",
        "fecha_inicio", "fin_garantia", "estado", "reemplazo_de", "notas", "fecha_enlace",
        "fecha_pago", "fecha_firma", "firma_cliente", "firma_trabajadora", "firma_agencia",
        "garantia",
    ),
}

PALETA_ANTIGUA = {
    "fondo": "#FFFFFF", "lateral": "#FCE9F2", "suave": "#F7F4F7", "hover": "#F8D6E7",
    "activo": "#FFFFFF", "borde": "#EDE4EB", "barra": "#DACBD6", "texto": "#2A2230",
    "texto2": "#574B5A", "tenue": "#7C6F80", "acento": "#C2156B", "acento_osc": "#99104F",
    "acento_suave": "#FCE4EF", "rojo": "#E0197D", "rojo_osc": "#B8135F",
    "peligro": "#C62828", "peligro_suave": "#FDEDED", "alerta": "#FFF4D6",
}


def crear_base_legada(ruta):
    """Crea registros con todos los campos antiguos y referencias reconocibles."""
    dibujo = json.dumps({"w": 330, "h": 150, "trazos": [[12, 21, 35, 47, 60, 19]]})
    filas = {
        "clientes": {
            "id": 71, "nombre": "Cliente ficticio & prueba", "dni": "00000001", "telefono": "900000001",
            "direccion": "Dirección de prueba", "zona": "Zona ficticia", "fecha_registro": "27/09/2026",
            "tipo_servicio": "Niñera", "sueldo_ofrecido": "1800", "horario": "08:00–17:00",
            "dias_libres": "Domingo", "personas_hogar": "3", "ninos": "1 de 5 años",
            "mascotas": "No", "tareas": "Cuidado\nDos líneas", "requisitos": "Experiencia de prueba",
            "fecha_necesita": "27/09/2026", "estado": "Colocado", "notas": "  Nota con espacios  ",
            "garantia": "Sí", "ocupacion": "Profesión ficticia",
        },
        "trabajadoras": {
            "id": 92, "nombre": "Trabajadora ficticia <prueba>", "dni": "00000002", "edad": "36",
            "telefono": "900000002", "direccion": "Dirección ficticia", "zona": "Zona de prueba",
            "tipo_servicio": "Niñera", "cama_adentro": "No", "experiencia": "7", "sueldo_esperado": "1800",
            "referencias": "Referencia ficticia\nSegundo renglón", "doc_dni": "1", "doc_antecedentes": "1",
            "doc_salud": "1", "doc_domicilio": "0", "doc_referencias": "1",
            "entrevista_fecha": "26/09/2026", "entrevista_resultado": "Aprobada",
            "entrevista_notas": "Nota de entrevista original", "estado": "Trabajando", "notas": "Nota original",
        },
        "colocaciones": {
            "id": 113, "cliente_id": "71", "trabajadora_id": "92", "entrevista_cliente_fecha": "26/09/2026",
            "entrevista_cliente_resultado": "Aceptada", "entrevista_cliente_notas": "Conservar esta entrevista",
            "sueldo_acordado": "1800.00", "porcentaje": "50", "comision": "900.00", "comision_pagada": "1",
            "contrato_firmado": "1", "docs_entregados": "1", "fecha_inicio": "27/09/2026",
            "fin_garantia": "27/10/2026", "estado": "Activa", "reemplazo_de": "", "notas": "Contrato original",
            "fecha_enlace": "26/09/2026", "fecha_pago": "27/09/2026", "fecha_firma": "27/09/2026 11:45",
            "firma_cliente": dibujo, "firma_trabajadora": dibujo, "firma_agencia": dibujo, "garantia": "Sí",
        },
    }
    with closing(sqlite3.connect(ruta)) as conexion:
        for tabla, columnas in COLUMNAS_ANTIGUAS.items():
            campos = ", ".join(f'"{c}" TEXT DEFAULT \'\'' for c in columnas)
            conexion.execute(f'CREATE TABLE "{tabla}" (id INTEGER PRIMARY KEY AUTOINCREMENT, {campos})')
            fila = filas[tabla]
            nombres = ", ".join(f'"{c}"' for c in fila)
            parametros = ", ".join("?" for _ in fila)
            conexion.execute(f'INSERT INTO "{tabla}" ({nombres}) VALUES ({parametros})', list(fila.values()))
        conexion.commit()
    return filas


class MigracionServitotal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.importacion_temporal = tempfile.TemporaryDirectory()
        especificacion = importlib.util.spec_from_file_location(
            "agencia_servitotal_validacion", CARPETA_PROYECTO / "agencia.py")
        cls.agencia = importlib.util.module_from_spec(especificacion)
        with mock.patch.dict(os.environ, {"AGENCIA_DATOS": cls.importacion_temporal.name}), \
                mock.patch.object(sys, "argv", [str(CARPETA_PROYECTO / "agencia.py")]):
            especificacion.loader.exec_module(cls.agencia)

    @classmethod
    def tearDownClass(cls):
        cls.importacion_temporal.cleanup()

    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.ruta = Path(self.temporal.name) / "agencia.db"
        self.originales = crear_base_legada(self.ruta)
        self.db = self.agencia.BaseDatos(self.ruta)

    def tearDown(self):
        self.db.con.close()
        self.temporal.cleanup()

    def comprobar_originales(self, db):
        for tabla, esperado in self.originales.items():
            with self.subTest(tabla=tabla):
                self.assertEqual(len(db.todos(tabla)), 1)
                actual = db.uno(tabla, esperado["id"])
                self.assertIsNotNone(actual)
                for clave, valor in esperado.items():
                    self.assertEqual(actual[clave], valor, f"{tabla}.{clave}")

    def test_conserva_todos_los_datos_columnas_y_referencias_anteriores(self):
        self.comprobar_originales(self.db)
        for tabla, columnas in COLUMNAS_ANTIGUAS.items():
            existentes = {r["name"] for r in self.db.con.execute(f"PRAGMA table_info({tabla})")}
            self.assertTrue(set(columnas).issubset(existentes))
        siguiente = self.db.insertar("clientes", {"nombre": "Cliente nuevo ficticio"})
        self.assertGreater(siguiente, self.originales["clientes"]["id"])

    def test_reabrir_no_repite_registros_ni_restaurar_areas_borradas(self):
        areas = self.db.todos("areas")
        self.assertEqual(len(areas), 6)
        self.db.eliminar("areas", areas[0]["id"])
        self.db.con.close()
        self.db = self.agencia.BaseDatos(self.ruta)
        self.comprobar_originales(self.db)
        self.assertEqual(len(self.db.todos("areas")), 5)
        self.assertEqual(self.db.con.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_restaurar_una_base_antigua_conserva_condiciones_y_firmas(self):
        copia = Path(self.temporal.name) / "copia-antigua.db"
        crear_base_legada(copia)
        self.db.actualizar("colocaciones", 113, {"comision": "111.11", "firma_cliente": ""})
        self.db.restaurar_desde(copia)
        self.comprobar_originales(self.db)
        self.assertEqual(self.db.con.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_comision_cobrada_antigua_alimenta_resumen_sin_recalcularla(self):
        resumen = self.agencia.resumen_ganancias(self.db.todos("colocaciones"), self.db.todos("clientes"))
        self.assertEqual(resumen["cobrado_total"], 900)
        self.assertEqual(resumen["por_cobrar"], 0)
        self.assertEqual(resumen["historial"][0]["monto"], 900)

    def test_contrato_antiguo_conserva_firmas_y_garantia_de_treinta_dias(self):
        contrato = self.db.uno("colocaciones", 113)
        cliente = self.db.uno("clientes", 71)
        pagina = self.agencia.html_contrato(contrato, cliente, self.db.uno("trabajadoras", 92))
        self.assertRegex(pagina, r"(?:30 días|treinta \(30\) días)")
        self.assertIn("900.00", pagina)
        self.assertIn("<polyline", pagina)
        self.assertIn("Cliente ficticio &amp; prueba", pagina)
        self.assertIn("Trabajadora ficticia &lt;prueba&gt;", pagina)
        self.assertEqual(contrato["fecha_inicio"], "27/09/2026")
        self.assertEqual(contrato["fin_garantia"], "27/10/2026")
        self.assertEqual(self.agencia.datos_contrato(contrato, cliente)["fecha_contrato"], "27/09/2026")

    def test_clientes_antiguos_sin_garantia_conservan_la_opcion(self):
        self.db.con.execute("UPDATE clientes SET garantia = 'No', meses_garantia = '' WHERE id = 71")
        self.db.con.commit()
        self.db.con.close()
        self.db = self.agencia.BaseDatos(self.ruta)
        cliente = self.db.uno("clientes", 71)
        self.assertEqual(cliente["garantia"], "No")
        self.assertEqual(self.agencia.meses_del_cliente(cliente), 0)

    def test_paleta_original_logo_e_identidad_de_servitotal(self):
        acentos_marca = {"azul_marca": PALETA_ANTIGUA["acento"], "azul_hover": PALETA_ANTIGUA["acento_osc"],
                         "rojo": PALETA_ANTIGUA["rojo"], "rojo_osc": PALETA_ANTIGUA["rojo_osc"]}
        for clave, color in acentos_marca.items():
            self.assertEqual(self.agencia.C[clave], color, clave)
        for clave in ("fondo", "lateral", "suave", "campo", "activo", "hover", "tabla_alt"):
            color = self.agencia.C[clave].lstrip("#")
            canales = [int(color[i:i + 2], 16) for i in (0, 2, 4)]
            self.assertLess(max(canales), 100, f"{clave} debe usar una superficie oscura")
        self.assertEqual(self.agencia.AGENCIA_ESLOGAN, "Servitotal")
        self.assertEqual(self.agencia.AGENCIA_REPRESENTANTE, "Xiomara Amaro Arellano")
        self.assertIn("2do piso, oficina 201", self.agencia.AGENCIA_DIRECCION)
        logo = CARPETA_PROYECTO / "logo.png"
        self.assertEqual(hashlib.sha256(logo.read_bytes()).hexdigest(),
                         "0415f3bbd7d35881f8716eaedfed305a5f85ad2cb4ffd71c5ee54b30631e1229")
        pagina = self.agencia.html_contrato(self.db.uno("colocaciones", 113),
                                          self.db.uno("clientes", 71), self.db.uno("trabajadoras", 92))
        self.assertIn("SERVITOTAL", pagina)
        self.assertIn("oficina 201", pagina)
        self.assertNotIn("SERVICIO EXCLUSIVO", pagina)
        self.assertNotIn("10436157334", pagina)

    def test_instaladas_guardan_en_carpeta_servitotal_separada(self):
        with mock.patch.object(sys, "frozen", True, create=True), \
                mock.patch.object(sys, "executable", str(Path(self.temporal.name) / "Programa" / "Agencia.exe")):
            for plataforma in ("win32", "darwin", "linux"):
                with self.subTest(plataforma=plataforma):
                    carpeta = self.agencia.carpeta_datos(argv=[], entorno={}, plataforma=plataforma,
                                                        casa=self.temporal.name)
                    self.assertEqual(Path(carpeta).name, "Servitotal")

    def test_copia_sin_fuente_no_crea_una_base_vacia_ni_sobrescribe_la_existente(self):
        inexistente = str(Path(self.temporal.name) / "fuente-desaparecida.db")
        destino = Path(self.temporal.name) / "respaldo-bueno.db"
        crear_base_legada(destino)
        antes = destino.read_bytes()
        with self.assertRaises((OSError, sqlite3.Error)):
            self.agencia.copiar_base(inexistente, str(destino))
        self.assertFalse(Path(inexistente).exists())
        self.assertEqual(destino.read_bytes(), antes)

    def test_restaurar_sin_fuente_conserva_la_base_abierta_y_el_archivo(self):
        inexistente = str(Path(self.temporal.name) / "fuente-desaparecida.db")
        with self.assertRaises((OSError, sqlite3.Error)):
            self.db.restaurar_desde(inexistente)
        self.comprobar_originales(self.db)
        self.assertFalse(Path(inexistente).exists())
        with self.assertRaises((OSError, sqlite3.Error)):
            self.agencia.restaurar_archivo(inexistente, str(self.ruta))
        self.comprobar_originales(self.db)
        self.assertFalse(Path(inexistente).exists())

    def test_restaurar_copia_elegida_sigue_funcionando_si_la_poda_la_retira(self):
        elegida = Path(self.temporal.name) / "agencia-manual-20260901-090000.db"
        crear_base_legada(elegida)
        self.db.actualizar("clientes", 71, {"nombre": "Cambió después del respaldo"})

        def copia_previa(*args, **kwargs):
            elegida.unlink()  # la retención elimina el respaldo seleccionado, durante la copia previa
            return {"archivo": None, "externas": [], "errores": [], "omitido": "Prueba de retención"}

        app = SimpleNamespace(root=None, db=self.db, clientes=mock.Mock(), trabajadoras=mock.Mock(),
                              hacer_copia=copia_previa, refrescar_todo=lambda: None)
        descriptor = {"ruta": str(elegida), "fecha": datetime(2026, 9, 1, 9),
                      "clientes": 1, "trabajadoras": 1, "colocaciones": 1}
        with mock.patch.object(self.agencia, "DB_PATH", str(self.ruta)), \
                mock.patch.object(self.agencia.messagebox, "askyesno", return_value=True):
            self.assertTrue(self.agencia.App.restaurar_copia(app, descriptor))
        self.comprobar_originales(self.db)
        self.assertFalse(elegida.exists())

    def test_dos_procesos_pueden_copiar_al_mismo_destino_sin_danar_la_copia(self):
        destino = Path(self.temporal.name) / "copia-compartida.db"
        barrera = Path(self.temporal.name) / "barrera"
        barrera.mkdir()
        # La barrera se activa después de abrir SQLite para escribir la copia:
        # reproduce dos instalaciones guardando a la vez en una carpeta compartida.
        codigo = r'''
import importlib.util, os, pathlib, sqlite3, sys, time
fuente, destino, barrera, numero, modulo = sys.argv[1:]
spec = importlib.util.spec_from_file_location("agencia_worker", modulo)
agencia = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agencia)
conectar = sqlite3.connect
avisado = False
def conectar_juntos(ruta, *args, **kwargs):
    global avisado
    conexion = conectar(ruta, *args, **kwargs)
    if not avisado and "agencia.db" not in str(ruta):
        avisado = True
        pathlib.Path(barrera, numero).touch()
        limite = time.monotonic() + 10
        while len(list(pathlib.Path(barrera).iterdir())) < 2:
            if time.monotonic() > limite:
                raise RuntimeError("No llegó el segundo proceso")
            time.sleep(.01)
    return conexion
sqlite3.connect = conectar_juntos
agencia.copiar_base(fuente, destino)
'''
        procesos = []
        try:
            for numero in ("1", "2"):
                procesos.append(subprocess.Popen(
                    [sys.executable, "-c", codigo, str(self.ruta), str(destino), str(barrera), numero,
                     str(CARPETA_PROYECTO / "agencia.py")],
                    env={**os.environ, "AGENCIA_DATOS": self.temporal.name},
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
            for proceso in procesos:
                salida, errores = proceso.communicate(timeout=30)
                self.assertEqual(proceso.returncode, 0, salida + errores)
        finally:
            for proceso in procesos:
                if proceso.poll() is None:
                    proceso.kill()
                    proceso.communicate()
        self.assertEqual(self.agencia.contar_datos(str(destino)),
                         {"clientes": 1, "trabajadoras": 1, "colocaciones": 1})
        copia = self.agencia.BaseDatos(destino)
        try:
            self.comprobar_originales(copia)
        finally:
            copia.con.close()

    def test_fallo_al_confirmar_un_lote_no_deja_cambios_parciales(self):
        conexion = self.db.con

        class ConfirmacionQueFallaUnaVez:
            fallado = False

            def execute(self, sql, *args, **kwargs):
                if sql.lstrip().upper().startswith("RELEASE") and not self.fallado:
                    self.fallado = True
                    raise sqlite3.OperationalError("Fallo de disco simulado al confirmar")
                return conexion.execute(sql, *args, **kwargs)

            def __getattr__(self, nombre):
                return getattr(conexion, nombre)

        self.db.con = ConfirmacionQueFallaUnaVez()
        with self.assertRaises(sqlite3.OperationalError):
            with self.db.lote():
                self.db.actualizar("colocaciones", 113, {"comision": "111.11"})
                self.db.actualizar("clientes", 71, {"nombre": "Cambio parcial"})
        self.comprobar_originales(self.db)
        with self.db.lote():
            self.db.actualizar("clientes", 71, {"nombre": "Después del fallo"})
        self.assertEqual(self.db.uno("clientes", 71)["nombre"], "Después del fallo")

    @contextmanager
    def programa_temporal(self):
        """Ventana real oculta, con todos los datos, ajustes y copias en carpeta temporal."""
        agencia = self.agencia
        try:
            root = agencia.tk.Tk()
        except agencia.tk.TclError:
            self.skipTest("No hay pantalla disponible")
        root.withdraw()
        carpeta = Path(self.temporal.name) / "programa"
        carpeta.mkdir()
        crear_base_legada(carpeta / "agencia.db")
        app = None
        try:
            with ExitStack() as parches:
                for nombre, ruta in (("DB_PATH", carpeta / "agencia.db"), ("CARPETA", carpeta),
                                     ("CARPETA_RESPALDOS", carpeta / "respaldos"),
                                     ("CONFIG_PATH", carpeta / "configuracion.json"),
                                     ("CARPETA_CONTRATOS", carpeta / "contratos"),
                                     ("ERRORES_PATH", carpeta / "errores.log")):
                    parches.enter_context(mock.patch.object(agencia, nombre, str(ruta)))
                parches.enter_context(mock.patch.object(agencia, "carpetas_externas", return_value=[]))
                parches.enter_context(mock.patch.object(agencia.App, "hacer_copia_en_segundo_plano", return_value=None))
                for nombre in ("showwarning", "showerror", "showinfo"):
                    parches.enter_context(mock.patch.object(agencia.messagebox, nombre))
                parches.enter_context(mock.patch.object(agencia.messagebox, "askyesno", return_value=True))
                app = agencia.App(root)
                yield app
        finally:
            if app is not None:
                app.db.con.close()
            root.destroy()
            agencia.restablecer_areas()

    def test_editar_notas_de_un_perfil_no_desocupa_una_trabajadora_asignada(self):
        with self.programa_temporal() as app:
            pagina = app.trabajadoras
            app.db.actualizar("trabajadoras", 92, {"estado": "Disponible"})
            app.refrescar_todo()
            app.mostrar(pagina)
            pagina.seleccionar(92)
            pagina.al_seleccionar()
            self.assertEqual(pagina.form.valor("estado"), "Disponible")
            app.sincronizar({"cliente_id": "71", "trabajadora_id": "92", "estado": "Activa"})
            pagina.form.poner_valor("notas", "Nota escrita por la usuaria")
            self.assertTrue(pagina.guardar())
            trabajadora = app.db.uno("trabajadoras", 92)
            self.assertEqual(trabajadora["estado"], "Trabajando")
            self.assertEqual(trabajadora["notas"], "Nota escrita por la usuaria")

    def test_cambios_en_campos_distintos_desde_otro_proceso_se_conservan(self):
        with self.programa_temporal() as app:
            pagina = app.trabajadoras
            app.mostrar(pagina)
            pagina.seleccionar(92)
            pagina.al_seleccionar()
            pagina.form.poner_valor("notas", "Nota escrita en esta instancia")
            otra = self.agencia.BaseDatos(self.agencia.DB_PATH)
            try:
                otra.actualizar("trabajadoras", 92, {"telefono": "900000099"})
            finally:
                otra.con.close()
            self.assertTrue(pagina.guardar())
            trabajadora = app.db.uno("trabajadoras", 92)
            self.assertEqual(trabajadora["telefono"], "900000099")
            self.assertEqual(trabajadora["notas"], "Nota escrita en esta instancia")

    def test_conflicto_en_el_mismo_campo_no_pisa_el_dato_externo_ni_el_formulario(self):
        with self.programa_temporal() as app:
            pagina = app.trabajadoras
            app.mostrar(pagina)
            pagina.seleccionar(92)
            pagina.al_seleccionar()
            pagina.form.poner_valor("telefono", "900000088")
            otra = self.agencia.BaseDatos(self.agencia.DB_PATH)
            try:
                otra.actualizar("trabajadoras", 92, {"telefono": "900000099"})
            finally:
                otra.con.close()
            self.assertFalse(pagina.guardar())
            self.assertEqual(app.db.uno("trabajadoras", 92)["telefono"], "900000099")
            self.assertEqual(pagina.form.valor("telefono"), "900000088")

    def test_un_conflicto_impide_descartar_la_edicion_al_navegar_o_cerrar(self):
        with self.programa_temporal() as app:
            pagina = app.trabajadoras
            segunda = app.db.insertar("trabajadoras", {"nombre": "Otra trabajadora ficticia", "telefono": "900000003"})
            app.mostrar(pagina)
            pagina.seleccionar(92)
            pagina.al_seleccionar()
            pagina.form.poner_valor("telefono", "900000088")
            otra = self.agencia.BaseDatos(self.agencia.DB_PATH)
            try:
                otra.actualizar("trabajadoras", 92, {"telefono": "900000099"})
            finally:
                otra.con.close()
            pagina.lista.selection_set(str(segunda))
            pagina.al_seleccionar()
            self.assertEqual(pagina.id_actual, 92)
            self.assertEqual(pagina.form.valor("telefono"), "900000088")
            app.mostrar(app.clientes)
            self.assertIs(app.visible, pagina)
            app.cerrar()
            self.assertTrue(app.root.winfo_exists())
            self.assertEqual(pagina.form.valor("telefono"), "900000088")

    def test_el_documento_legado_firmado_conserva_su_texto_tras_editar_y_reabrir(self):
        contrato = self.db.uno("colocaciones", 113)
        antes = self.agencia.html_contrato(contrato, self.db.uno("clientes", 71), self.db.uno("trabajadoras", 92))
        self.assertEqual(contrato["contrato_html"], antes)
        self.db.actualizar("clientes", 71, {"nombre": "Cliente modificado después de firmar", "direccion": "Nueva dirección"})
        self.db.actualizar("trabajadoras", 92, {"nombre": "Trabajadora modificada después de firmar"})
        self.db.actualizar("colocaciones", 113, {"comision": "123.45", "sueldo_acordado": "3000", "meses_garantia": "6"})
        self.db.con.close()
        self.db = self.agencia.BaseDatos(self.ruta)
        despues = self.agencia.html_contrato(self.db.uno("colocaciones", 113),
                                            self.db.uno("clientes", 71), self.db.uno("trabajadoras", 92))
        self.assertEqual(despues, antes)
        imprimir = self.agencia.html_contrato(self.db.uno("colocaciones", 113),
                                             self.db.uno("clientes", 71), self.db.uno("trabajadoras", 92), imprimir=True)
        self.assertIn("Cliente ficticio &amp; prueba", imprimir)
        self.assertNotIn("Cliente modificado después de firmar", imprimir)
        self.assertGreater(imprimir.count("window.print"), antes.count("window.print"))

    def test_firmar_conserva_valores_y_firmas_hasta_refirmar_explicitamente(self):
        with self.programa_temporal() as app:
            nuevo = {clave: "" for clave in self.agencia.claves(self.agencia.CAMPOS_COLOCACION)}
            nuevo.update(cliente_id="71", trabajadora_id="92", estado="En proceso", fecha_enlace="31/01/2028",
                         fecha_contrato="31/01/2028", sueldo_acordado="1800", comision="432.10", porcentaje="24.01",
                         garantia="Sí", dias_garantia="30", meses_garantia="0")
            identificador = app.db.insertar("colocaciones", nuevo)
            app.contratos.refrescar()

            def firmas(texto):
                return {clave: json.dumps({"tipo": "nombre", "texto": texto + " " + clave})
                        for clave in ("firma_cliente", "firma_trabajadora", "firma_agencia")}

            primera = firmas("Primera firma ficticia")
            with mock.patch.object(self.agencia, "DialogoFirmas",
                                   side_effect=lambda master, c, cli, t, guardar: guardar(primera)), \
                    mock.patch.object(self.agencia.messagebox, "askyesno", return_value=False):
                app.contratos.firmar(app.db.uno("colocaciones", identificador))
            firmado = app.db.uno("colocaciones", identificador)
            original = firmado["contrato_html"]
            self.assertIn("432.10", original)
            self.assertIn("Primera firma ficticia", original)
            for clave, firma in primera.items():
                self.assertEqual(firmado[clave], firma)

            app.db.actualizar("clientes", 71, {"nombre": "Cliente actualizado tras la primera firma"})
            app.db.actualizar("colocaciones", identificador, {"comision": "543.21"})
            app.contratos.refrescar()
            actual = app.db.uno("colocaciones", identificador)
            pagina = self.agencia.html_contrato(actual, app.db.uno("clientes", 71), app.db.uno("trabajadoras", 92))
            self.assertEqual(pagina, original)

            segunda = firmas("Segunda firma ficticia")
            with mock.patch.object(self.agencia, "DialogoFirmas",
                                   side_effect=lambda master, c, cli, t, guardar: guardar(segunda)), \
                    mock.patch.object(self.agencia.messagebox, "askyesno", side_effect=[True, False]):
                app.contratos.firmar(actual)
            refirmado = app.db.uno("colocaciones", identificador)
            self.assertIn("543.21", refirmado["contrato_html"])
            self.assertIn("Cliente actualizado tras la primera firma", refirmado["contrato_html"])
            self.assertIn("Segunda firma ficticia", refirmado["contrato_html"])
            self.assertNotIn("Primera firma ficticia", refirmado["contrato_html"])
            for clave, firma in segunda.items():
                self.assertEqual(refirmado[clave], firma)

    def test_garantia_en_dias_y_meses_respetan_el_plazo_acordado(self):
        dias = {"garantia": "Sí", "dias_garantia": "30", "meses_garantia": "0"}
        mes = {"garantia": "Sí", "dias_garantia": "0", "meses_garantia": "1"}
        self.assertEqual(self.agencia.vencimiento_garantia(date(2026, 1, 31), dias), date(2026, 3, 2))
        self.assertEqual(self.agencia.vencimiento_garantia(date(2026, 1, 31), mes), date(2026, 2, 28))
        self.assertEqual(self.agencia.vencimiento_garantia(date(2028, 1, 31), dias), date(2028, 3, 1))
        self.assertEqual(self.agencia.vencimiento_garantia(date(2028, 1, 31), mes), date(2028, 2, 29))
        self.assertIsNone(self.agencia.vencimiento_garantia(date(2026, 1, 31),
                                                          {"garantia": "No", "dias_garantia": "0", "meses_garantia": "0"}))
        firmado = {**dias, "estado": "En proceso", "contrato_firmado": "1", "fecha_contrato": "31/01/2026"}
        self.assertEqual(self.agencia.inicio_por_firma(firmado)["fin_garantia"], "02/03/2026")

    def test_el_dialogo_adapta_la_comision_y_permite_elegir_dias_o_meses(self):
        with self.programa_temporal() as app:
            guardados = []
            valores = self.agencia.datos_contrato(app.db.uno("colocaciones", 113), app.db.uno("clientes", 71))
            with mock.patch.object(self.agencia.tk.Toplevel, "grab_set", return_value=None):
                dialogo = self.agencia.DialogoContrato(app.root, 113, valores, guardados.append)
            dialogo.form.poner_valor("porcentaje", "12.5")
            self.assertEqual(self.agencia.leer_numero(dialogo.form.valor("comision")), 225)
            dialogo.form.poner_valor("sueldo_acordado", "2000")
            self.assertEqual(self.agencia.leer_numero(dialogo.form.valor("comision")), 250)
            dialogo.form.poner_valor("comision", "400")
            self.assertEqual(self.agencia.leer_numero(dialogo.form.valor("porcentaje")), 20)
            dialogo.form.poner_valor("sueldo_acordado", "2500")
            self.assertEqual(self.agencia.leer_numero(dialogo.form.valor("comision")), 400)
            self.assertEqual(self.agencia.leer_numero(dialogo.form.valor("porcentaje")), 16)
            dialogo.form.poner_valor("meses_garantia", "2")
            self.assertEqual(dialogo.form.valor("dias_garantia"), "0")
            dialogo.form.poner_valor("dias_garantia", "45")
            self.assertEqual(dialogo.form.valor("meses_garantia"), "0")
            dialogo.guardar()
            self.assertEqual(len(guardados), 1)
            self.assertEqual(guardados[0]["comision"], "400.00")
            self.assertEqual(guardados[0]["porcentaje"], "16")
            self.assertEqual(guardados[0]["dias_garantia"], "45")
            self.assertEqual(guardados[0]["meses_garantia"], "0")


if __name__ == "__main__":
    unittest.main()
