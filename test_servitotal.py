"""Pruebas de lo propio de Servitotal: su nombre, su carpeta, sus colores, su contrato y sus datos de antes.

Lo demás es el programa de Servicio Exclusivo tal cual (instaladores/construccion/igualar_con_tia.py lo copia) y lo
prueban las mismas pruebas de la tía. Todo con datos ficticios en carpetas temporales."""
import difflib
import html
import importlib.util
import io
import json
import os
import re
import sqlite3
import struct
import tempfile
import unittest
import zipfile
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from xml.etree import ElementTree

if not os.environ.get("AGENCIA_DATOS"):      # nunca la carpeta de datos real, aunque se pruebe desde el proyecto
    os.environ["AGENCIA_DATOS"] = tempfile.mkdtemp(prefix="agencia-pruebas-")

import agencia
from agencia import BaseDatos, docx_contrato, esquema_desactualizado, html_contrato, pdf_contrato, tamano_firma

PALETA_SERVITOTAL = {   # tema oscuro de Servitotal con detalles rosa y fucsia (igualar_con_tia.PALETA_PRIMA)
    "fondo": "#17131A",
    "lateral": "#201823",
    "suave": "#211B25",
    "campo": "#2B222F",
    "hover": "#352438",
    "activo": "#2D2231",
    "borde": "#503C55",
    "barra": "#705A77",
    "tabla_alt": "#211B25",
    "texto": "#F7F0F6",
    "texto2": "#DDCDDE",
    "tenue": "#BDAABD",
    "acento": "#F58DBD",
    "acento_osc": "#F8D6E7",
    "acento_suave": "#482239",
    "azul_marca": "#C2156B",
    "azul_hover": "#99104F",
    "logo_fondo": "#2D2231",
    "rojo": "#E0197D",
    "rojo_osc": "#B8135F",
    "peligro": "#F595A9",
    "peligro_suave": "#46242D",
    "alerta": "#3D2F23",
}
COLORES_CONTRATO_SERVITOTAL = ("#99104F", "#2A2230", "#C2156B", "#F7F4F7", "#E0197D")
COLORES_CONTRATO_TIA = ("#1d3a8a", "#13213F", "#1B4DB1", "#E0282E", "#e8ecf2")
DATO, FIRMA = "99104F", "2A2230"              # colores del dato punteado y de la firma en Word y PDF
DATO_TIA, FIRMA_TIA = "1D3A8A", "13213F"


def color_pdf(hexa):
    """Cómo escribe el PDF un color de texto («0.600 0.063 0.310»)."""
    return " ".join(f"{int(hexa[i:i + 2], 16) / 255:.3f}" for i in (0, 2, 4))


class IdentidadDeServitotal(unittest.TestCase):
    def datos(self, **kw):
        return agencia.carpeta_datos(**{"argv": ["agencia.py"], "entorno": {}, "casa": "/Users/ana", **kw})

    def test_nombre_y_paleta_de_servitotal(self):
        self.assertEqual(agencia.AGENCIA_ESLOGAN, "Servitotal")
        self.assertEqual(agencia.AGENCIA_CARPETA_DATOS, "Servitotal")
        self.assertEqual(agencia.C, PALETA_SERVITOTAL)          # solo cambian los colores; nada de la paleta azul

    def test_menus_y_controles_desactivados_siguen_el_tema_oscuro(self):
        try:
            root = agencia.tk.Tk()
        except agencia.tk.TclError:
            self.skipTest("no hay pantalla disponible")
        root.withdraw()
        self.addCleanup(root.destroy)
        agencia.aplicar_tema(root)
        C = agencia.C
        menu = agencia.tk.Menu(root)
        self.assertEqual({opcion: str(menu.cget(opcion)) for opcion in (
            "background", "foreground", "activebackground", "activeforeground", "disabledforeground")},
            {"background": C["fondo"], "foreground": C["texto"], "activebackground": C["acento_suave"],
             "activeforeground": C["texto"], "disabledforeground": C["tenue"]})
        estilo = agencia.ttk.Style(root)
        for nombre, opcion, color in (("TEntry", "lightcolor", "suave"), ("TEntry", "darkcolor", "suave"),
                                      ("TCombobox", "background", "suave"), ("TCombobox", "arrowcolor", "tenue"),
                                      ("TCombobox", "lightcolor", "suave"), ("TCombobox", "darkcolor", "suave"),
                                      ("Enlace.TButton", "foreground", "tenue")):
            self.assertEqual(str(estilo.lookup(nombre, opcion, ["disabled"])), C[color], (nombre, opcion))

    def test_instalado_guarda_los_datos_en_la_carpeta_servitotal(self):
        agencia.sys.frozen = True
        try:
            with tempfile.TemporaryDirectory() as vacia:
                original = agencia.sys.executable
                agencia.sys.executable = os.path.join(vacia, "programa")
                try:
                    self.assertEqual(self.datos(plataforma="darwin"),
                                     os.path.join("/Users/ana", "Library", "Application Support", "Servitotal"))
                    self.assertEqual(self.datos(plataforma="win32", entorno={"LOCALAPPDATA": "C:\\L"}),
                                     os.path.join("C:\\L", "Servitotal"))
                    self.assertEqual(self.datos(plataforma="win32"),
                                     os.path.join("/Users/ana", "AppData", "Local", "Servitotal"))
                    self.assertEqual(self.datos(plataforma="linux"),
                                     os.path.join("/Users/ana", ".local", "share", "Servitotal"))
                finally:
                    agencia.sys.executable = original
        finally:
            del agencia.sys.frozen

    def test_instalacion_de_windows_abierta_sin_acceso_directo_tambien_usa_servitotal(self):
        with mock.patch.object(agencia, "instalado_con_runtime", return_value=True):
            self.assertEqual(self.datos(plataforma="win32", entorno={"LOCALAPPDATA": "C:\\L"}),
                             os.path.join("C:\\L", "Servitotal"))

    def test_copias_en_respaldos_servitotal_con_su_propia_marca(self):
        self.assertEqual(agencia.MARCA_COPIAS, ".copias-servitotal")
        self.assertEqual(os.path.basename(agencia.carpetas_externas({})[0]), "Respaldos Servitotal")
        with tempfile.TemporaryDirectory() as usb:
            # La memoria USB que eligió Servicio Exclusivo (su marca) no recibe los datos de Servitotal.
            Path(usb, ".copias-agencia").write_text("Carpeta elegida para las copias de seguridad de Agencia de "
                                                    "Empleos.\n", encoding="utf-8")
            self.assertFalse(agencia.carpeta_adicional_lista(usb))
            self.assertEqual(agencia.carpetas_externas({"copia_adicional": usb})[1:], [])
            agencia.marcar_carpeta_adicional(usb)
            self.assertIn("Servitotal", Path(usb, ".copias-servitotal").read_text(encoding="utf-8"))
            self.assertTrue(agencia.carpeta_adicional_lista(usb))
            self.assertEqual(agencia.carpetas_externas({"copia_adicional": usb})[1:], [usb])

    def test_el_leeme_de_las_copias_dice_servitotal(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "agencia.db")
            db = BaseDatos(ruta)
            db.insertar("clientes", {"nombre": "Cliente ficticio", "telefono": "900000001"})
            db.con.close()
            destino = os.path.join(carpeta, "Respaldos Servitotal")
            agencia.copia_externa(ruta, destino)
            leame = Path(destino, "LEEME.txt").read_text(encoding="utf-8")
            self.assertTrue(leame.startswith("Copias de seguridad de Servitotal\n"), leame[:80])


class ContratoDeServitotal(unittest.TestCase):
    """El contrato de la tía, a nombre de «S.T Servitotal», con su domicilio, su representante y sus colores."""
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

    def setUp(self):
        self.c = {"id": 12, "estado": "Activa", "garantia": "Sí", "meses_garantia": "1", "comision": "360.00",
                  "sueldo_acordado": "1800", "fecha_contrato": "15/09/2026", "reemplazo_de": "",
                  "contrato_firmado": "", "fecha_firma": "", "firma_cliente": "", "firma_trabajadora": "",
                  "firma_agencia": "", "puesto": "", "modalidad": "", "descanso": ""}
        self.cli = {"nombre": "Carla Ficticia Ramos", "dni": "11223344", "direccion": "Jr. Prueba 123",
                    "zona": "Ate", "telefono": "900111222", "ocupacion": "Docente", "tipo_servicio": "Cama adentro",
                    "dias_libres": "Domingo", "horario": ""}
        self.t = {"nombre": "Julia Inventada Soto", "dni": "55667788", "direccion": "", "zona": "Vitarte"}

    def firmado(self):
        return dict(self.c, contrato_firmado="1", fecha_firma="15/09/2026 11:00",
                    firma_cliente=json.dumps({"tipo": "nombre", "texto": "Carla Ficticia Ramos"}),
                    firma_trabajadora=json.dumps({"w": 330, "h": 150, "trazos": [[10, 10, 200, 120, 320, 20]]}))

    def test_a_nombre_de_servitotal_con_su_representante_y_sin_ruc(self):
        pagina = html_contrato(self.c, self.cli, self.t)
        self.assertIn("CONTRATO Y GARANTÍA", pagina)
        self.assertIn("CONTRATO DE TRABAJO", pagina)
        self.assertIn("“S.T SERVITOTAL”", pagina)
        self.assertIn("la agencia de empleos “S.T SERVITOTAL”, con domicilio en Av. Nicolás Ayllón N° 5695, "
                      "2do piso, oficina 201, Carretera Central, distrito de Ate-Vitarte, representada por "
                      "Xiomara Amaro Arellano con DNI N° 76395760", pagina)
        self.assertIn("Agencia de Empleos “S.T SERVITOTAL”", pagina)       # bajo la firma de LA AGENCIA
        for de_la_tia in ("10436157334", "con RUC", "SERVICIO EXCLUSIVO", "Servicio Exclusivo", "3er piso"):
            self.assertNotIn(de_la_tia, pagina)

    def test_colores_de_servitotal_en_el_contrato(self):
        pagina = html_contrato(self.firmado(), self.cli, self.t)
        estilo = pagina.split("<style>", 1)[1].split("</style>", 1)[0]
        for color in COLORES_CONTRATO_SERVITOTAL:
            self.assertIn(color, estilo)
        for color in COLORES_CONTRATO_TIA:
            self.assertNotIn(color.lower(), pagina.lower())
        self.assertIn('stroke="#2A2230"', pagina)                         # la firma dibujada

    def test_word_con_los_colores_de_servitotal(self):
        contenido = docx_contrato(html_contrato(self.firmado(), self.cli, self.t), fuente_firma="Segoe Script")
        with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
            partes = {nombre: paquete.read(nombre) for nombre in paquete.namelist()}
        documento = ElementTree.fromstring(partes["word/document.xml"])
        W = self.W
        texto = "".join(t.text or "" for t in documento.iter(W + "t"))
        self.assertIn("“S.T SERVITOTAL”", texto)
        self.assertIn("representada por Xiomara Amaro Arellano con DNI N° 76395760", texto)
        punteados, datos, firmas, colores = [], [], [], set()
        for tramo in documento.iter(W + "r"):
            color = tramo.find(f"{W}rPr/{W}color")
            color = color.get(W + "val") if color is not None else None
            colores.add(color)
            letra = tramo.find(f"{W}rPr/{W}rFonts")
            subrayado = tramo.find(f"{W}rPr/{W}u")
            escrito = "".join(t.text or "" for t in tramo.iter(W + "t"))
            if subrayado is not None and subrayado.get(W + "val") == "dotted":
                punteados.append(color)
            if escrito.strip("\xa0 ") in ("11223344", "55667788"):          # DNI escritos en los renglones de datos
                datos.append(color)
            if letra is not None and letra.get(W + "ascii") == "Segoe Script":
                firmas.append(color)
        self.assertTrue(punteados and set(punteados) == {DATO}, punteados)
        self.assertTrue(datos and set(datos) == {DATO}, datos)
        self.assertEqual(firmas, [FIRMA] * 2)                    # la firma con nombre del empleador, en las dos hojas
        self.assertFalse(colores & {DATO_TIA, FIRMA_TIA})
        png = partes["word/media/firma1.png"]                    # la trabajadora firmó dibujando
        inicio = png.index(b"PLTE")
        largo = struct.unpack(">I", png[inicio - 4:inicio])[0]
        self.assertEqual(png[inicio + 4:inicio + 4 + largo], bytes.fromhex("000000" + FIRMA))

    def test_pdf_con_los_colores_de_servitotal(self):
        import zlib
        pdf = pdf_contrato(html_contrato(self.firmado(), self.cli, self.t))
        self.assertIn(b"/ColorSpace [/Indexed /DeviceRGB 1 <000000" + FIRMA.encode("ascii") + b">]", pdf)
        self.assertNotIn(FIRMA_TIA.encode("ascii"), pdf)
        trozos = []                                               # (texto, fuente, color)
        for flujo in re.findall(rb"stream\n(.*?)\nendstream", pdf, re.S):
            try:
                contenido = zlib.decompress(flujo).decode("ascii")
            except zlib.error:
                continue                                          # la imagen de la firma dibujada
            for fuente, color, cadena in re.findall(
                    r"/F(\d) [\d.]+ Tf ([\d. ]+) rg 1 0 0 1 [\d.]+ [\d.]+ Tm \((.*?)\) Tj ET", contenido):
                datos = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), cadena).encode("latin-1")
                trozos.append((datos.decode("cp1252"), agencia._FUENTES_PDF[int(fuente) - 1], color))
        palabras = " ".join(texto for texto, _, _ in trozos)
        self.assertIn("SERVITOTAL”", palabras)
        self.assertIn("Xiomara", palabras)
        datos = [color for texto, _, color in trozos if texto.strip("\xa0 ") in ("11223344", "55667788")]
        self.assertTrue(datos and set(datos) == {color_pdf(DATO)}, datos)
        firmas = [color for _, fuente, color in trozos if fuente == "Times-Italic"]
        self.assertTrue(firmas and set(firmas) == {color_pdf(FIRMA)}, firmas)
        self.assertFalse({color for _, _, color in trozos} & {color_pdf(DATO_TIA), color_pdf(FIRMA_TIA)})


class ContratosConTresFirmas(unittest.TestCase):
    """Servitotal firmó contratos con tres firmas por renglón (EMPRESA, EMPLEADOR y PERSONA): sus nombres se achican
    para un recuadro de 120 pt, no de 200 pt como en el contrato actual de dos firmas."""
    LARGO, MEDIO, CORTO = "Xiomara Amaro Arellano", "Lucía Fernández Quispe", "Rosa Sol"

    def contrato_anterior(self, firmas):
        recuadros = "".join(
            f'<div class="firma"><div class="trazo"><span class="nombre-firma" style="font-size:22pt">'
            f'{html.escape(nombre)}</span></div><div class="linea">{rol}</div>'
            f'<div class="quien">{html.escape(nombre)}</div></div>' for rol, nombre in firmas)
        return ('<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><style>'
                '.nombre-firma { color: #2A2230; line-height: 1.1; white-space: nowrap; }</style></head><body>'
                f'<section class="hoja"><h1>CONTRATO DE TRABAJO</h1><div class="firmas">{recuadros}</div></section>'
                '</body></html>')

    def tamanos(self, documento):
        return [int(t) for t in re.findall(r'<span class="nombre-firma" style="font-size:(\d+)pt">', documento)]

    def test_un_contrato_de_tres_firmas_las_achica_para_su_recuadro(self):
        for nombre in (self.LARGO, self.MEDIO):      # nombres que cambian de tamaño según el recuadro
            self.assertNotEqual(tamano_firma(nombre, 120), tamano_firma(nombre))
        nombres = (self.LARGO, self.MEDIO, self.CORTO)
        anterior = self.contrato_anterior(zip(("EMPRESA", "EMPLEADOR", "PERSONA"), nombres))
        self.assertEqual(self.tamanos(agencia.ajustar_firmas(anterior)), [tamano_firma(n, 120) for n in nombres])
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "agencia.db"
            db = BaseDatos(ruta)
            try:
                numero = db.insertar("colocaciones", {"estado": "Activa", "contrato_firmado": "1",
                                                      "fecha_firma": "10/03/2026 12:00", "contrato_html": anterior})
                mostrado = html_contrato(db.uno("colocaciones", numero), {}, {})
                self.assertEqual(self.tamanos(mostrado), [tamano_firma(n, 120) for n in nombres])
                self.assertNotIn("nowrap", mostrado)
            finally:
                db.con.close()
            with closing(sqlite3.connect(ruta)) as con:                  # el documento guardado no se modifica
                self.assertEqual(con.execute("SELECT contrato_html FROM colocaciones WHERE id = ?",
                                             (numero,)).fetchone()[0], anterior)

    def test_un_contrato_de_dos_firmas_sigue_con_el_recuadro_de_200_pt(self):
        nombres = (self.MEDIO, self.CORTO)
        anterior = self.contrato_anterior(zip(("EMPLEADOR", "TRABAJADORA"), nombres))
        firmado = {"contrato_firmado": "1", "contrato_html": anterior}
        self.assertEqual(self.tamanos(html_contrato(firmado, {}, {})), [tamano_firma(n) for n in nombres])
        self.assertEqual(firmado["contrato_html"], anterior)


class ComisionSinPropuesta(unittest.TestCase):
    """Servitotal no propone comisión: en cada contrato se escribe el porcentaje (o el pago único)."""

    def test_no_hay_comision_propuesta(self):
        self.assertEqual(agencia.COBRO_DEFECTO, "")
        self.assertIsNone(agencia.PORCENTAJE_DEFECTO)

    def test_sin_comision_se_pide_escribir_el_porcentaje(self):
        for vacia in ("", "   ", None):
            aviso = agencia.validar_condiciones_financieras({"comision": vacia})
            self.assertIsNotNone(aviso, repr(vacia))
            self.assertIn("porcentaje", aviso)
        self.assertIsNone(agencia.validar_condiciones_financieras(
            {"comision": "360.00", "sueldo_acordado": "1800", "porcentaje": "20"}))

    def test_al_asignar_la_comision_queda_por_escribir(self):
        with tempfile.TemporaryDirectory() as carpeta:
            db = BaseDatos(Path(carpeta) / "agencia.db")
            try:
                cli = db.insertar("clientes", {"nombre": "Cliente ficticio", "telefono": "900000001",
                                               "sueldo_ofrecido": "1800", "estado": "Buscando"})
                t = db.insertar("trabajadoras", {"nombre": "Trabajadora ficticia", "telefono": "900000002",
                                                 "estado": "Disponible"})
                app = agencia.App.__new__(agencia.App)
                app.db = db
                app._reemplazos = (-1, {})
                app.refrescar_todo = mock.Mock()
                app.abrir_contratos = mock.Mock()
                pagina = SimpleNamespace(db=db, app=app,
                                         elegidos=lambda: (db.uno("clientes", cli), db.uno("trabajadoras", t)),
                                         after_idle=mock.Mock())
                with mock.patch.object(agencia, "DialogoContrato") as dialogo:
                    agencia.PaginaEnlazar.asignar(pagina)
                valores, confirmar = dialogo.call_args.args[2:4]
                self.assertEqual((valores["comision"], valores["porcentaje"]), ("", ""))
                self.assertEqual(valores["sueldo_acordado"], agencia.normalizar_sueldo("1800"))
                # «Confirmar asignación» sin comisión: pide el porcentaje y no asigna nada.
                ventana = SimpleNamespace(form=SimpleNamespace(obtener=lambda: dict(valores)),
                                          al_guardar=confirmar, destroy=mock.Mock())
                with mock.patch.object(agencia.messagebox, "showwarning") as aviso:
                    self.assertFalse(agencia.DialogoContrato.guardar(ventana))
                self.assertIn("porcentaje", aviso.call_args.args[1])
                self.assertEqual(db.todos("colocaciones"), [])
                # Con el porcentaje escrito (y su monto, como lo calcula la ventana) se asigna.
                ventana.form.obtener = lambda: dict(valores, porcentaje="20", comision="360")
                self.assertTrue(agencia.DialogoContrato.guardar(ventana))
                [asignacion] = db.todos("colocaciones")
                self.assertEqual((asignacion["comision"], asignacion["porcentaje"]), ("360.00", "20"))
            finally:
                db.con.close()


class GarantiasEnDias(unittest.TestCase):
    """Servitotal guardaba la garantía en días; al abrir la base pasa a meses una sola vez (30 días = 1 mes), con
    copia previa, sin tocar las garantías ya iniciadas ni los contratos firmados."""

    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(prefix="garantias-ficticias-")
        self.carpeta = Path(self.temporal.name)
        self.ruta = str(self.carpeta / "agencia.db")

    def tearDown(self):
        self.temporal.cleanup()

    def fila(self, tabla, id_):
        with closing(sqlite3.connect(self.ruta)) as con:
            con.row_factory = sqlite3.Row
            return dict(con.execute(f"SELECT * FROM {tabla} WHERE id = ?", (id_,)).fetchone())

    def base_con_dias(self):
        """Base con la estructura actual y garantías guardadas en días, como las dejaba Servitotal."""
        BaseDatos(self.ruta).con.close()
        firmado = "<html><body>Contrato firmado ficticio de 30 días</body></html>"
        with closing(sqlite3.connect(self.ruta)) as con, con:
            cliente = con.execute("INSERT INTO clientes (nombre, telefono, meses_garantia, dias_garantia) "
                                  "VALUES ('Cliente ficticio', '900000001', '', '30')").lastrowid
            trabajadora = con.execute("INSERT INTO trabajadoras (nombre, telefono) "
                                      "VALUES ('Trabajadora ficticia', '900000002')").lastrowid
            ids = {}
            for clave, datos in (
                    ("sin_firmar", {"estado": "En proceso", "garantia": "Sí", "meses_garantia": "0",
                                    "dias_garantia": "30", "fecha_enlace": "01/09/2026"}),
                    ("firmada", {"estado": "Activa", "garantia": "Sí", "meses_garantia": "", "dias_garantia": "30",
                                 "contrato_firmado": "1", "fecha_firma": "02/09/2026 10:00",
                                 "fecha_contrato": "02/09/2026", "fecha_inicio": "02/09/2026",
                                 "fin_garantia": "02/10/2026", "contrato_html": firmado}),
                    ("sin_garantia", {"estado": "Activa", "garantia": "No", "meses_garantia": "0",
                                      "dias_garantia": "0"}),
                    ("cuarenta_y_cinco", {"estado": "En proceso", "garantia": "Sí", "meses_garantia": "",
                                          "dias_garantia": "45"})):
                datos = dict(datos, cliente_id=str(cliente), trabajadora_id=str(trabajadora))
                ids[clave] = con.execute(f"INSERT INTO colocaciones ({', '.join(datos)}) "
                                         f"VALUES ({', '.join('?' * len(datos))})", list(datos.values())).lastrowid
        return cliente, ids, firmado

    def test_pasan_a_meses_una_sola_vez_y_con_copia_previa(self):
        cliente, ids, firmado = self.base_con_dias()
        self.assertTrue(esquema_desactualizado(self.ruta))       # la estructura está al día: faltan los meses
        copia = {"archivo": str(self.carpeta / "copia.db"), "externas": [], "omitido": None, "errores": []}
        with mock.patch.object(agencia, "DB_PATH", self.ruta), \
                mock.patch.object(agencia, "CARPETA_RESPALDOS", str(self.carpeta / "respaldos")), \
                mock.patch.object(agencia, "carpetas_externas", lambda configuracion=None: []), \
                mock.patch.object(agencia, "respaldar", return_value=copia) as respaldar:
            agencia.preparar_base()
        respaldar.assert_called_once_with("antes-de-actualizar")
        self.assertEqual(self.fila("colocaciones", ids["sin_firmar"])["meses_garantia"], "0")   # aún sin convertir

        BaseDatos(self.ruta).con.close()
        sin_firmar, firmada = self.fila("colocaciones", ids["sin_firmar"]), self.fila("colocaciones", ids["firmada"])
        self.assertEqual((sin_firmar["meses_garantia"], sin_firmar["dias_garantia"]), ("1", "30"))
        self.assertEqual((firmada["meses_garantia"], firmada["dias_garantia"]), ("1", "30"))
        self.assertEqual((firmada["fin_garantia"], firmada["contrato_html"]), ("02/10/2026", firmado))
        sin_garantia = self.fila("colocaciones", ids["sin_garantia"])
        self.assertEqual((sin_garantia["garantia"], sin_garantia["meses_garantia"], sin_garantia["dias_garantia"]),
                         ("No", "0", "0"))
        self.assertEqual(self.fila("colocaciones", ids["cuarenta_y_cinco"])["meses_garantia"], "2")
        self.assertEqual(self.fila("clientes", cliente)["meses_garantia"], "1 mes")
        self.assertFalse(esquema_desactualizado(self.ruta))

        # Si después la asignación queda sin garantía, sus 30 días guardados no la vuelven a convertir.
        db = BaseDatos(self.ruta)
        db.actualizar("colocaciones", ids["sin_firmar"], {"garantia": "No", "meses_garantia": "0"})
        db.con.close()
        self.assertFalse(esquema_desactualizado(self.ruta))
        BaseDatos(self.ruta).con.close()
        sin_firmar = self.fila("colocaciones", ids["sin_firmar"])
        self.assertEqual((sin_firmar["garantia"], sin_firmar["meses_garantia"], sin_firmar["dias_garantia"]),
                         ("No", "0", "30"))

    def test_base_de_la_primera_version_de_servitotal(self):
        with closing(sqlite3.connect(self.ruta)) as con, con:
            con.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT DEFAULT '', "
                        "telefono TEXT DEFAULT '', garantia TEXT DEFAULT '')")
            con.execute("CREATE TABLE trabajadoras (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT DEFAULT '', "
                        "telefono TEXT DEFAULT '')")
            con.execute("CREATE TABLE colocaciones (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id TEXT DEFAULT '', "
                        "trabajadora_id TEXT DEFAULT '', estado TEXT DEFAULT '', garantia TEXT DEFAULT '', "
                        "comision TEXT DEFAULT '', contrato_firmado TEXT DEFAULT '', fecha_firma TEXT DEFAULT '')")
            con_garantia = con.execute("INSERT INTO clientes (nombre, telefono, garantia) "
                                       "VALUES ('Cliente con garantía', '900000001', 'Sí')").lastrowid
            sin_garantia = con.execute("INSERT INTO clientes (nombre, telefono, garantia) "
                                       "VALUES ('Cliente sin garantía', '900000002', 'No')").lastrowid
            trabajadora = con.execute("INSERT INTO trabajadoras (nombre, telefono) "
                                      "VALUES ('Trabajadora ficticia', '900000003')").lastrowid
            firmada = con.execute(
                "INSERT INTO colocaciones (cliente_id, trabajadora_id, estado, garantia, comision, contrato_firmado, "
                "fecha_firma) VALUES (?, ?, 'Activa', 'Sí', '360.00', '1', '15/03/2026 10:30')",
                (str(con_garantia), str(trabajadora))).lastrowid
            sin_firmar = con.execute(
                "INSERT INTO colocaciones (cliente_id, trabajadora_id, estado, garantia, comision, contrato_firmado, "
                "fecha_firma) VALUES (?, ?, 'En proceso', 'No', '300.00', '', '')",
                (str(sin_garantia), str(trabajadora))).lastrowid
        self.assertTrue(esquema_desactualizado(self.ruta))
        BaseDatos(self.ruta).con.close()
        con_firma, sin_firma = self.fila("colocaciones", firmada), self.fila("colocaciones", sin_firmar)
        self.assertEqual((con_firma["meses_garantia"], con_firma["fecha_contrato"]), ("1", "15/03/2026"))
        self.assertEqual((sin_firma["meses_garantia"], sin_firma["fecha_contrato"]), ("0", ""))
        # El contrato firmado se guarda con su garantía de 30 días (un mes) y la fecha en que se firmó.
        self.assertIn("un (1)", con_firma["contrato_html"])
        self.assertIn("marzo", con_firma["contrato_html"])
        self.assertEqual(self.fila("clientes", con_garantia)["meses_garantia"], "1 mes")
        self.assertEqual(self.fila("clientes", sin_garantia)["meses_garantia"], "Sin garantía")
        self.assertFalse(esquema_desactualizado(self.ruta))


class ColumnasConservadas(unittest.TestCase):
    """Lo que Servitotal pedía antes en sus fichas se conserva en la base, aunque los formularios ya no lo muestren."""
    TRABAJADORA = ("sueldo_esperado", "entrevista_fecha", "entrevista_resultado", "entrevista_notas")

    def test_una_base_nueva_tiene_las_columnas_y_los_formularios_no_las_muestran(self):
        with tempfile.TemporaryDirectory() as carpeta:
            db = BaseDatos(Path(carpeta) / "agencia.db")
            try:
                columnas = {tabla: {r["name"] for r in db.con.execute(f"PRAGMA table_info({tabla})")}
                            for tabla in agencia.TABLAS}
                self.assertLessEqual(set(self.TRABAJADORA), columnas["trabajadoras"])
                self.assertIn("dias_garantia", columnas["clientes"])
                self.assertIn("dias_garantia", columnas["colocaciones"])
                anteriores = {"sueldo_esperado": "1200", "entrevista_fecha": "01/09/2026",
                              "entrevista_resultado": "Aprobada", "entrevista_notas": "Notas ficticias"}
                t = db.insertar("trabajadoras", {"nombre": "Trabajadora ficticia", **anteriores})
                db.actualizar("trabajadoras", t, {"telefono": "900000002"})      # editar la ficha no los borra
                self.assertEqual({clave: db.uno("trabajadoras", t)[clave] for clave in anteriores}, anteriores)
            finally:
                db.con.close()
        formularios = {
            "trabajadoras": agencia.claves(agencia.PaginaTrabajadoras.campos),
            "clientes": agencia.claves(agencia.PaginaClientes.campos),
            "contrato": agencia.claves(agencia.DialogoContrato.CAMPOS),
        }
        for nombre, campos in formularios.items():
            for oculta in (*self.TRABAJADORA, "dias_garantia"):
                self.assertNotIn(oculta, campos, nombre)


class BaseDeOtraAgencia(unittest.TestCase):
    """Al buscar los datos de una versión anterior nunca se ofrece la base de Servicio Exclusivo, aunque su programa
    esté en el mismo equipo y su base sea la más reciente."""

    def test_se_ofrece_la_base_de_servitotal_y_nunca_la_de_servicio_exclusivo(self):
        with tempfile.TemporaryDirectory() as raiz:
            rutas = {}
            for carpeta, eslogan, fecha in (("ServicioExclusivo", "Servicio Exclusivo", 1_790_000_000),
                                            ("Servitotal", "Servitotal", 1_780_000_000),
                                            ("Portable", None, 1_770_000_000)):
                Path(raiz, carpeta).mkdir()
                if eslogan:
                    Path(raiz, carpeta, "agencia.py").write_text(
                        f'AGENCIA_NOMBRE = "Agencia de Empleos"\nAGENCIA_ESLOGAN = "{eslogan}"\n', encoding="utf-8")
                rutas[carpeta] = os.path.join(raiz, carpeta, "agencia.db")
                db = BaseDatos(rutas[carpeta])
                db.insertar("clientes", {"nombre": f"Cliente ficticio de {carpeta}", "telefono": "900000001"})
                db.con.close()
                os.utime(rutas[carpeta], (fecha, fecha))
            self.assertTrue(agencia._de_otra_agencia(rutas["ServicioExclusivo"]))
            self.assertFalse(agencia._de_otra_agencia(rutas["Servitotal"]))
            self.assertFalse(agencia._de_otra_agencia(rutas["Portable"]))     # sin programa al lado: no se sabe
            oferta = agencia.buscar_datos_anteriores(lugares=[(raiz, 1)])
            self.assertEqual(Path(oferta["ruta"]), Path(rutas["Servitotal"]))
            os.remove(rutas["Servitotal"])
            oferta = agencia.buscar_datos_anteriores(lugares=[(raiz, 1)])
            self.assertEqual(Path(oferta["ruta"]), Path(rutas["Portable"]))
            os.remove(rutas["Portable"])
            self.assertIsNone(agencia.buscar_datos_anteriores(lugares=[(raiz, 1)]))


class DatosQueYaTeniaServitotal(unittest.TestCase):
    """Lo que la revisión encontró al abrir datos de Servitotal 1.7.2 con el programa de la tía."""

    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(prefix="servitotal-ficticio-")
        self.carpeta = Path(self.temporal.name)
        self.ruta = str(self.carpeta / "agencia.db")

    def tearDown(self):
        self.temporal.cleanup()

    def test_clientes_sin_plazo_escrito_siguen_con_un_mes_y_los_nuevos_con_el_de_siempre(self):
        BaseDatos(self.ruta).con.close()
        with closing(sqlite3.connect(self.ruta)) as con, con:
            sin_plazo = con.execute("INSERT INTO clientes (nombre, telefono) VALUES ('Sin plazo', '1')").lastrowid
            raro = con.execute("INSERT INTO clientes (nombre, telefono, dias_garantia) "
                               "VALUES ('Con 30.0', '2', '30.0')").lastrowid        # escrito fuera del programa
            con.execute("INSERT INTO colocaciones (cliente_id, garantia, meses_garantia, dias_garantia) "
                        "VALUES (?, 'Sí', '0', '30')", (str(sin_plazo),))
        db = BaseDatos(self.ruta)                                   # Servitotal les proponía 30 días: un mes
        try:
            self.assertEqual(db.uno("clientes", sin_plazo)["meses_garantia"], "1 mes")
            self.assertEqual(db.uno("clientes", raro)["meses_garantia"], "1 mes")
            nuevo = db.insertar("clientes", {"nombre": "Cliente nuevo", "telefono": "3"})
        finally:
            db.con.close()
        db = BaseDatos(self.ruta)                                   # los nuevos siguen la regla de siempre
        try:
            self.assertEqual(db.uno("clientes", nuevo)["meses_garantia"], "")
            self.assertEqual(agencia.meses_del_cliente(db.uno("clientes", nuevo)), agencia.MESES_GARANTIA)
        finally:
            db.con.close()
        self.assertFalse(esquema_desactualizado(self.ruta))

    def test_guardar_los_datos_del_contrato_sin_cambios_conserva_el_fin_de_la_garantia(self):
        db = BaseDatos(self.ruta)
        try:
            cli = db.insertar("clientes", {"nombre": "Cliente ficticio", "telefono": "1"})
            t = db.insertar("trabajadoras", {"nombre": "Trabajadora ficticia", "telefono": "2"})
            aid = db.insertar("colocaciones", {
                "cliente_id": str(cli), "trabajadora_id": str(t), "estado": "Activa", "garantia": "Sí",
                "meses_garantia": "1", "dias_garantia": "30", "comision": "360.00", "sueldo_acordado": "1800",
                "fecha_contrato": "31/01/2026", "fecha_inicio": "31/01/2026", "fin_garantia": "02/03/2026"})
            app = SimpleNamespace(refrescar_todo=mock.Mock())
            pagina = SimpleNamespace(db=db, app=app)
            with mock.patch.object(agencia, "DialogoContrato") as dialogo:
                agencia.PaginaContratos.editar_datos(pagina, db.uno("colocaciones", aid))
            valores, guardar = dialogo.call_args.args[2:4]
            self.assertTrue(guardar(dict(valores)))                       # «Guardar» sin cambiar nada
            self.assertEqual(db.uno("colocaciones", aid)["fin_garantia"], "02/03/2026")   # sus 30 días
            with mock.patch.object(agencia, "DialogoContrato") as dialogo:
                agencia.PaginaContratos.editar_datos(pagina, db.uno("colocaciones", aid))
            valores, guardar = dialogo.call_args.args[2:4]
            self.assertTrue(guardar(dict(valores, meses_garantia="2")))     # si cambia el plazo, se recalcula
            self.assertEqual(db.uno("colocaciones", aid)["fin_garantia"], "31/03/2026")
        finally:
            db.con.close()

    def test_la_lista_de_contratos_dice_1_mes(self):
        c = {"id": 1, "cliente_id": "1", "trabajadora_id": "2", "fecha_enlace": "01/09/2026", "garantia": "Sí",
             "meses_garantia": "1", "contrato_firmado": "", "fecha_firma": ""}
        pagina = SimpleNamespace(clientes={}, nombre=lambda c, rol: rol)
        self.assertIn("1 mes", agencia.PaginaContratos.valores(pagina, c))
        self.assertNotIn("1 meses", agencia.PaginaContratos.valores(pagina, c))
        self.assertIn("2 meses", agencia.PaginaContratos.valores(pagina, dict(c, meses_garantia="2")))

    def test_la_carpeta_de_copias_de_otra_agencia_nunca_se_usa(self):
        usb = self.carpeta / "USB de la otra agencia"
        usb.mkdir()
        (usb / ".copias-agencia").write_text("Carpeta elegida por otra agencia.\n", encoding="utf-8")
        (usb / "agencia-20260930.db").write_bytes(b"copia de la otra agencia")
        self.assertFalse(agencia.carpeta_adicional_lista(str(usb)))
        self.assertEqual(agencia.carpetas_externas({"copia_adicional": str(usb)})[1:], [])
        self.assertFalse((usb / agencia.MARCA_COPIAS).exists())                  # tampoco se marca como propia
        self.assertEqual((usb / "agencia-20260930.db").read_bytes(), b"copia de la otra agencia")

    def test_con_porcentaje_y_sin_sueldo_el_aviso_pide_el_sueldo(self):
        aviso = agencia.validar_condiciones_financieras({"comision": "", "porcentaje": "20", "sueldo_acordado": ""})
        self.assertIn("sueldo", aviso)
        self.assertIn("porcentaje", agencia.validar_condiciones_financieras({"comision": "", "porcentaje": ""}))


class AlFrenteAlAbrir(unittest.TestCase):
    """Abierto desde «Terminar» del instalador, Servitotal se muestra por encima de todo un momento (Windows 11 lo
    dejaba detrás de las demás ventanas y parecía que no se abría)."""

    def test_en_windows_se_pone_encima_y_luego_vuelve_a_ser_normal(self):
        root = mock.Mock()
        with mock.patch.object(agencia, "ES_WINDOWS", True):
            agencia.traer_al_frente(root)
        root.attributes.assert_called_once_with("-topmost", True)
        root.focus_force.assert_called_once_with()
        milisegundos, soltar = root.after.call_args.args
        self.assertEqual(milisegundos, 1500)
        soltar()
        root.attributes.assert_called_with("-topmost", False)

    def test_fuera_de_windows_no_hace_nada(self):
        root = mock.Mock()
        with mock.patch.object(agencia, "ES_WINDOWS", False):
            agencia.traer_al_frente(root)
        root.assert_not_called()
        self.assertEqual(root.method_calls, [])

    def test_main_lo_llama_al_abrir(self):
        principal = agencia.main.__code__.co_names
        self.assertIn("traer_al_frente", principal)


class IgualAlProgramaDeLaTia(unittest.TestCase):
    """agencia.py de Servitotal es el de Servicio Exclusivo con solo la capa de Servitotal (igualar_con_tia.py).
    En la carpeta real, Servitotal vive dentro de la carpeta de la tía."""
    AQUI = Path(__file__).resolve().parent
    TIA = AQUI.parent / "agencia.py"
    IGUALAR = AQUI / "instaladores" / "construccion" / "igualar_con_tia.py"

    def test_es_el_programa_de_la_tia_con_la_capa_de_servitotal(self):
        if not self.TIA.is_file():
            self.skipTest(f"no está el programa de Servicio Exclusivo en {self.TIA}")
        texto_tia = self.TIA.read_text(encoding="utf-8")
        eslogan = re.search(r'^AGENCIA_ESLOGAN = "([^"]*)"', texto_tia, re.M)
        if not eslogan or eslogan.group(1) != "Servicio Exclusivo":
            self.skipTest(f"{self.TIA} no es el programa de Servicio Exclusivo")
        especificacion = importlib.util.spec_from_file_location("igualar_con_tia", self.IGUALAR)
        igualar_con_tia = importlib.util.module_from_spec(especificacion)
        especificacion.loader.exec_module(igualar_con_tia)
        como = (f"Para volver a igualar Servitotal con la tía:\n"
                f'  cd "{self.AQUI}"\n'
                f'  python3 instaladores/construccion/igualar_con_tia.py "{self.TIA.parent}" "{self.AQUI}"\n'
                "y vuelva a pasar las pruebas. Un cambio propio de Servitotal va en igualar_con_tia.py, "
                "no en agencia.py.")
        try:
            esperado = igualar_con_tia.igualar(texto_tia)
        except igualar_con_tia.TextoNoEncontrado as error:
            esperado, revisar = None, str(error)
        if esperado is None:
            self.fail(f"Servicio Exclusivo cambió líneas que Servitotal adapta. Revise este cambio en "
                      f"instaladores/construccion/igualar_con_tia.py:\n{revisar}\n\nDespués: {como}")
        actual = (self.AQUI / "agencia.py").read_text(encoding="utf-8")
        if esperado != actual:
            diferencias = list(difflib.unified_diff(esperado.splitlines(), actual.splitlines(),
                                                    "agencia.py de la tía igualado", "agencia.py de Servitotal",
                                                    n=1, lineterm=""))
            self.fail("agencia.py de Servitotal ya no es el de Servicio Exclusivo con la capa de Servitotal "
                      "(o la tía tiene cambios nuevos).\n" + "\n".join(diferencias[:40]) + "\n\n" + como)


if __name__ == "__main__":
    unittest.main()
