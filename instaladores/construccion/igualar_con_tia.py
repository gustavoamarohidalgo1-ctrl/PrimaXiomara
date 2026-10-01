"""Servitotal es el mismo programa que Servicio Exclusivo (el de la tía), con sus colores y sus datos propios.

Uso:  python igualar_con_tia.py CARPETA_DE_SERVICIO_EXCLUSIVO CARPETA_DE_SERVITOTAL

Toma el agencia.py de Servicio Exclusivo tal cual y le aplica solo la capa de Servitotal:
- la paleta de colores (programa, contrato, Word y PDF);
- los datos de la agencia (nombre en el contrato, domicilio, representante, sin RUC) y su carpeta de datos y copias,
  para que nunca se mezclen con los de otra agencia;
- la compatibilidad con los datos que ya tiene Servitotal: garantías guardadas en días (pasan a meses una sola vez,
  con copia previa), columnas que ya no se muestran y contratos firmados con tres firmas;
- sin comisión propuesta: en cada contrato se escribe el porcentaje.
Cada reemplazo comprueba que el texto de origen exista exactamente una vez: si Servicio Exclusivo cambia esas líneas,
el script se detiene y dice cuál revisar, en vez de dejar un programa a medias.
"""
import sys
from pathlib import Path


class TextoNoEncontrado(Exception):
    pass


def reemplazar(texto, viejo, nuevo, veces=1, motivo=""):
    encontrados = texto.count(viejo)
    if encontrados != veces:
        raise TextoNoEncontrado(f"{motivo or 'reemplazo'}: se esperaba {veces} vez/veces y hay {encontrados}:\n{viejo[:300]}")
    return texto.replace(viejo, nuevo)


CAMBIOS = []


def cambio(motivo, viejo, nuevo, veces=1):
    CAMBIOS.append((motivo, viejo, nuevo, veces))


# ---------------------------------------------------------------- Datos de la agencia
cambio("datos de la agencia", '''AGENCIA_NOMBRE = "Agencia de Empleos"
AGENCIA_ESLOGAN = "Servicio Exclusivo"
''', '''AGENCIA_NOMBRE = "Agencia de Empleos"
AGENCIA_ESLOGAN = "Servitotal"
''')
cambio("datos legales y comisión de Servitotal", '''AGENCIA_RUC = "10436157334"
AGENCIA_DOMICILIO = ("Av. Nicolás Ayllón N° 5695, 3er piso, oficina 304, distrito de Ate, "
                     "provincia y departamento de Lima")
CIUDAD_CONTRATO = "Lima"
MONEDA = "S/"
COBRO_DEFECTO = "300.00"   # lo que paga el empleador a la agencia, por única vez (si no se usa un porcentaje)
PORCENTAJE_DEFECTO = None  # p. ej. 20: la comisión propuesta sería el 20 % del sueldo; None = usar COBRO_DEFECTO
                           # (en cada contrato se puede cambiar el monto o el porcentaje)
''', '''# Servitotal usa el mismo programa que Servicio Exclusivo (instaladores/construccion/igualar_con_tia.py lo copia);
# solo cambian sus colores, sus datos y su carpeta de datos, que nunca se mezcla con la de otra agencia.
AGENCIA_CARPETA_DATOS = "Servitotal"      # datos en .../Servitotal y copias en Documentos/Respaldos Servitotal
AGENCIA_NOMBRE_EN_CONTRATO = "S.T Servitotal"   # «la agencia de empleos “S.T SERVITOTAL”»
AGENCIA_RUC = ""                          # Servitotal se identifica por su representante
AGENCIA_REPRESENTANTE = "Xiomara Amaro Arellano"
AGENCIA_DNI_REPRESENTANTE = "76395760"
AGENCIA_DOMICILIO = ("Av. Nicolás Ayllón N° 5695, 2do piso, oficina 201, Carretera Central, "
                     "distrito de Ate-Vitarte")
CIUDAD_CONTRATO = "Lima"
MONEDA = "S/"
COBRO_DEFECTO = ""         # sin propuesta: en cada contrato se escribe el porcentaje del sueldo (o el pago único)
PORCENTAJE_DEFECTO = None  # p. ej. 20: la comisión propuesta sería el 20 % del sueldo; None = sin propuesta
''')
for anterior, nuevo in (
        ('return os.path.join(entorno.get("LOCALAPPDATA") or os.path.join(casa, "AppData", "Local"), AGENCIA_NOMBRE)',
         'return os.path.join(entorno.get("LOCALAPPDATA") or os.path.join(casa, "AppData", "Local"), AGENCIA_CARPETA_DATOS)'),
        ('return os.path.join(casa, "Library", "Application Support", AGENCIA_NOMBRE)',
         'return os.path.join(casa, "Library", "Application Support", AGENCIA_CARPETA_DATOS)'),
        ('return os.path.join(entorno.get("XDG_DATA_HOME") or os.path.join(casa, ".local", "share"), AGENCIA_NOMBRE)',
         'return os.path.join(entorno.get("XDG_DATA_HOME") or os.path.join(casa, ".local", "share"), AGENCIA_CARPETA_DATOS)')):
    cambio("carpeta de datos propia", anterior, nuevo, veces=2 if "LOCALAPPDATA" in anterior else 1)
cambio("copias en Documentos/Respaldos Servitotal",
       'carpetas = [os.path.join(carpeta_documentos(), f"Respaldos {AGENCIA_NOMBRE}")]',
       'carpetas = [os.path.join(carpeta_documentos(), f"Respaldos {AGENCIA_CARPETA_DATOS}")]')
cambio("marca de la carpeta adicional propia",
       'MARCA_COPIAS = ".copias-agencia"',
       'MARCA_COPIAS = ".copias-servitotal"')
cambio("texto de la marca", 'archivo.write(f"Carpeta elegida para las copias de seguridad de {AGENCIA_NOMBRE}.\\n")',
       'archivo.write(f"Carpeta elegida para las copias de seguridad de {AGENCIA_ESLOGAN}.\\n")')
cambio("LEEME de la carpeta de copias", 'archivo.write(f"Copias de seguridad de {AGENCIA_NOMBRE}\\n\\n"',
       'archivo.write(f"Copias de seguridad de {AGENCIA_ESLOGAN}\\n\\n"')

# ---------------------------------------------------------------- Contrato con los datos de Servitotal
cambio("nombre de la agencia en el contrato", '''    agencia = f"“{AGENCIA_ESLOGAN.upper()}”"
''', '''    agencia = f"“{AGENCIA_NOMBRE_EN_CONTRATO.upper()}”"
    identificacion = (f"con RUC N° {e(AGENCIA_RUC)} y domicilio fiscal en {e(AGENCIA_DOMICILIO)}" if AGENCIA_RUC else
                      f"con domicilio en {e(AGENCIA_DOMICILIO)}, representada por {e(AGENCIA_REPRESENTANTE)} "
                      f"con DNI N° {e(AGENCIA_DNI_REPRESENTANTE)}")
''')
cambio("identificación de la agencia en el contrato", '''de una parte, la agencia de empleos {e(agencia)}, con RUC N° {e(AGENCIA_RUC)} y domicilio fiscal en
{e(AGENCIA_DOMICILIO)}, en adelante LA AGENCIA;''', '''de una parte, la agencia de empleos {e(agencia)}, {identificacion},
en adelante LA AGENCIA;''')

# ---------------------------------------------------------------- Comisión sin propuesta
cambio("sin comisión propuesta, el porcentaje se escribe en cada contrato",
       '''        valores = dict(datos_contrato(nuevo, cli), ocupacion=cli.get("ocupacion") or "")
''', '''        valores = dict(datos_contrato(nuevo, cli), ocupacion=cli.get("ocupacion") or "")
        if not nuevo["comision"]:          # sin comisión propuesta: se escribe en cada contrato
            valores.update(comision="", porcentaje="")
''')
cambio("aviso si falta la comisión", '''    comision = leer_decimal(datos.get("comision"))
''', '''    if str(datos.get("comision") or "").strip() == "":
        if str(datos.get("porcentaje") or "").strip() and not str(datos.get("sueldo_acordado") or "").strip():
            return "Para calcular la comisión con el porcentaje, escriba el sueldo mensual (o escriba el pago único)."
        return "Escriba la comisión: el porcentaje del sueldo o el pago único a la agencia."
    comision = leer_decimal(datos.get("comision"))
''')

# ---------------------------------------------------------------- Colores de Servitotal
PALETA_TIA = '''C = {
    "fondo": "#1A293B",        # paneles elevados, tarjetas y ventanas
    "lateral": "#0B1522",      # navegación y zona de marca
    "suave": "#101D2C",        # lienzo de las páginas
    "campo": "#122235",        # entradas y listas desplegables
    "hover": "#253A51",
    "activo": "#243C58",
    "borde": "#304359",
    "barra": "#64788E",
    "tabla_alt": "#1D3045",
    "texto": "#F5F8FC",
    "texto2": "#D4E0EC",
    "tenue": "#9FB1C4",
    "acento": "#A5C7FF",       # azul claro legible sobre fondos oscuros
    "acento_osc": "#D1E2FF",
    "acento_suave": "#2B4B72",
    "azul_marca": "#1B4DB1",   # azul rey original para botones
    "azul_hover": "#2864D4",
    "logo_fondo": "#CBE3FB",   # respaldo celeste del logo transparente
    "rojo": "#E0282E",         # rojo original de la flecha
    "rojo_osc": "#BD1F27",
    "peligro": "#FF7B80",
    "peligro_suave": "#382632",
    "alerta": "#3D3221",
}'''
PALETA_PRIMA = '''C = {   # tema oscuro de Servitotal con detalles rosa y fucsia
    "fondo": "#17131A",        # paneles elevados, tarjetas y ventanas
    "lateral": "#201823",      # navegación y zona de marca
    "suave": "#211B25",        # lienzo de las páginas
    "campo": "#2B222F",        # entradas y listas desplegables
    "hover": "#352438",
    "activo": "#2D2231",
    "borde": "#503C55",
    "barra": "#705A77",
    "tabla_alt": "#211B25",
    "texto": "#F7F0F6",
    "texto2": "#DDCDDE",
    "tenue": "#BDAABD",
    "acento": "#F58DBD",       # rosa claro legible sobre fondos oscuros
    "acento_osc": "#F8D6E7",
    "acento_suave": "#482239",
    "azul_marca": "#C2156B",   # fucsia de los botones principales
    "azul_hover": "#99104F",
    "logo_fondo": "#2D2231",   # fondo del logo de Servitotal
    "rojo": "#E0197D",
    "rojo_osc": "#B8135F",
    "peligro": "#F595A9",
    "peligro_suave": "#46242D",
    "alerta": "#3D2F23",
}'''
cambio("paleta de Servitotal", PALETA_TIA, PALETA_PRIMA)
cambio("controles clásicos con el tema", '''def aplicar_tema(root):
''', '''def aplicar_tema(root):
    # Controles clásicos, incluidos los menús de Tk, siguen el tema oscuro.
    root.option_add("*background", C["fondo"])
    root.option_add("*foreground", C["texto"])
    root.option_add("*Menu.activeBackground", C["acento_suave"])
    root.option_add("*Menu.activeForeground", C["texto"])
    root.option_add("*Menu.disabledForeground", C["tenue"])
''')
cambio("campos desactivados", '''          lightcolor=[("readonly", C["suave"])], darkcolor=[("readonly", C["suave"])])''',
       '''          lightcolor=[("disabled", C["suave"]), ("readonly", C["suave"])],
          darkcolor=[("disabled", C["suave"]), ("readonly", C["suave"])])''')
cambio("listas desactivadas", '''          background=[("active", C["hover"]), ("readonly", C["campo"])],''',
       '''          background=[("disabled", C["suave"]), ("active", C["hover"]), ("readonly", C["campo"])],''')
cambio("flecha de listas desactivadas", '''          lightcolor=[("focus", C["campo"])], darkcolor=[("focus", C["campo"])])''',
       '''          arrowcolor=[("disabled", C["tenue"])],
          lightcolor=[("disabled", C["suave"]), ("focus", C["campo"])],
          darkcolor=[("disabled", C["suave"]), ("focus", C["campo"])])''')
cambio("enlaces desactivados", '''    s.map("Enlace.TButton", foreground=[("active", C["acento_osc"])])''',
       '''    s.map("Enlace.TButton", foreground=[("disabled", C["tenue"]), ("active", C["acento_osc"])])''')
cambio("color de la firma dibujada", 'stroke="#13213F" stroke-width="2.5"', 'stroke="#2A2230" stroke-width="2.5"')
for anterior, nuevo in (("background: #e8ecf2;", "background: #F7F4F7;"),
                        (".barra {{ position: sticky; top: 0; background: #1B4DB1;",
                         ".barra {{ position: sticky; top: 0; background: #C2156B;"),
                        (".barra button {{ background: #E0282E;", ".barra button {{ background: #E0197D;"),
                        ("border-bottom: 1.6px dotted #444; color: #1d3a8a;", "border-bottom: 1.6px dotted #444; color: #99104F;"),
                        (".nombre-firma {{ color: #13213F;", ".nombre-firma {{ color: #2A2230;")):
    cambio("colores del contrato", anterior, nuevo)
cambio("colores del contrato en Word y PDF", '''ANCHO_WORD = 10092''', '''COLOR_DATO_CONTRATO = "99104F"     # dato escrito sobre la línea punteada, como en el contrato HTML
COLOR_FIRMA_CONTRATO = "2A2230"    # nombre en letra manuscrita y trazo de la firma dibujada
ANCHO_WORD = 10092''')
cambio("dato en Word", 'color="1D3A8A", punteado=True)', 'color=COLOR_DATO_CONTRATO, punteado=True)')
cambio("dato de renglón en Word", '''_tramo_word("\\xa0" + texto if variante == "largo" else texto, color="1D3A8A")''',
       '''_tramo_word("\\xa0" + texto if variante == "largo" else texto, color=COLOR_DATO_CONTRATO)''')
cambio("texto del PNG", '"""Firma dibujada como PNG: trazo azul oscuro sobre fondo transparente."""',
       '"""Firma dibujada como PNG: trazo del color de las firmas del contrato sobre fondo transparente."""')
cambio("color del PNG", 'seccion(b"PLTE", bytes((0, 0, 0, 0x13, 0x21, 0x3F)))',
       'seccion(b"PLTE", bytes(3) + bytes.fromhex(COLOR_FIRMA_CONTRATO))')
cambio("firma con nombre en Word", 'color="13213F", tamano=trazo[2], fuente=fuente)',
       'color=COLOR_FIRMA_CONTRATO, tamano=trazo[2], fuente=fuente)')
cambio("dato en PDF", '("Helvetica", "1D3A8A", numero)', '("Helvetica", COLOR_DATO_CONTRATO, numero)')
cambio("dato de renglón en PDF", 'else ("Helvetica", "1D3A8A")', 'else ("Helvetica", COLOR_DATO_CONTRATO)')
cambio("firma con nombre en PDF", '_palabras_sueltas(trazo[1], "Times-Italic", "13213F")',
       '_palabras_sueltas(trazo[1], "Times-Italic", COLOR_FIRMA_CONTRATO)')
cambio("texto de la firma en PDF", '# índice 0 transparente (máscara por color) y 1 azul oscuro, como el PNG',
       '# índice 0 transparente (máscara por color) y 1 el color de la firma, como el PNG')
cambio("color de la firma en PDF", '''"/ColorSpace [/Indexed /DeviceRGB 1 <00000013213F>] /BitsPerComponent 8 /Mask [0 0] "''',
       '''f"/ColorSpace [/Indexed /DeviceRGB 1 <000000{COLOR_FIRMA_CONTRATO}>] /BitsPerComponent 8 /Mask [0 0] "''')

# ---------------------------------------------------------------- Compatibilidad con los datos de Servitotal
cambio("columnas que Servitotal ya tenía (clientes)",
       '''CAMPOS_OCULTOS_CLIENTE = [("fecha_necesita", "fecha_necesita"), ("notas", "notas"),
                          ("estado", "estado"), ("meses_garantia", "meses_garantia")]''',
       '''CAMPOS_OCULTOS_CLIENTE = [("fecha_necesita", "fecha_necesita"), ("notas", "notas"),
                          ("estado", "estado"), ("meses_garantia", "meses_garantia"),
                          ("dias_garantia", "dias_garantia")]   # Servitotal guardaba la garantía en días''')
cambio("columnas que Servitotal ya tenía (trabajadoras)",
       '''CAMPOS_OCULTOS_TRABAJADORA = [("estado", "estado"), ("notas", "notas")]''',
       '''CAMPOS_OCULTOS_TRABAJADORA = [("estado", "estado"), ("notas", "notas"),
                              # lo que Servitotal pedía antes en la ficha: se conserva aunque ya no se muestre
                              ("sueldo_esperado", "sueldo_esperado"), ("entrevista_fecha", "entrevista_fecha"),
                              ("entrevista_resultado", "entrevista_resultado"), ("entrevista_notas", "entrevista_notas")]''')
cambio("columna de días de las asignaciones", '''    "colocaciones": CAMPOS_COLOCACION,''',
       '''    "colocaciones": CAMPOS_COLOCACION + [("dias_garantia", "dias_garantia")],   # garantía en días de Servitotal''')
cambio("garantías en días: foto del esquema antes de agregar columnas",
       '''        self.con.execute("BEGIN IMMEDIATE")  # reservar escritura antes de leer el esquema evita upgrade BUSY
        try:
''', '''        self.con.execute("BEGIN IMMEDIATE")  # reservar escritura antes de leer el esquema evita upgrade BUSY
        try:
            antes = {tabla: {r["name"] for r in self.con.execute(f"PRAGMA table_info({tabla})")} for tabla in TABLAS}
''')
cambio("garantías en días: pasan a meses", '''            if "garantia" in {r["name"] for r in self.con.execute("PRAGMA table_info(clientes)")}:
''', '''            _garantias_en_meses(self.con, antes)
            if "garantia" in {r["name"] for r in self.con.execute("PRAGMA table_info(clientes)")}:
''')
cambio("garantías en días: la conversión", '''class BaseDatos:
''', '''def _garantias_pendientes(con):
    """True si quedan garantías de Servitotal guardadas en días que todavía no pasaron a meses."""
    for tabla, necesarias, condicion in (
            ("colocaciones", {"dias_garantia", "meses_garantia", "garantia"},
             "COALESCE(garantia, '') <> 'No' AND (meses_garantia IS NULL OR meses_garantia IN ('', '0'))"),
            ("clientes", {"dias_garantia", "meses_garantia"}, "(meses_garantia IS NULL OR meses_garantia = '')")):
        columnas = {fila[1] for fila in con.execute(f"PRAGMA table_info({tabla})")}
        if necesarias <= columnas and con.execute(
                f"SELECT 1 FROM {tabla} WHERE CAST(dias_garantia AS INTEGER) > 0 AND {condicion} LIMIT 1").fetchone():
            return True
    return False


def _garantias_en_meses(con, antes):
    """Servitotal guardaba la garantía en días (30 por defecto); el programa la maneja en meses, como Servicio
    Exclusivo. Se convierte una sola vez, redondeando hacia arriba (30 días = 1 mes), solo donde falta el dato en meses:
    la fecha de fin de una garantía ya iniciada y los contratos firmados no se tocan, y los días quedan guardados."""
    primera_conversion = _garantias_pendientes(con)
    if "garantia" in antes["colocaciones"] and "meses_garantia" not in antes["colocaciones"]:
        # Base de la primera versión de Servitotal: garantía Sí/No de 30 días y la fecha del contrato en la firma.
        con.execute("UPDATE colocaciones SET meses_garantia = CASE WHEN garantia = 'No' THEN '0' ELSE '1' END "
                    "WHERE meses_garantia IS NULL OR meses_garantia = ''")
        con.execute("UPDATE colocaciones SET fecha_contrato = substr(fecha_firma, 1, 10) WHERE contrato_firmado = '1' "
                    "AND (fecha_contrato IS NULL OR fecha_contrato = '') AND COALESCE(fecha_firma, '') <> ''")
    if "garantia" in antes["clientes"] and "meses_garantia" not in antes["clientes"]:
        for id_, garantia in con.execute("SELECT id, garantia FROM clientes WHERE meses_garantia IS NULL "
                                         "OR meses_garantia = ''").fetchall():
            con.execute("UPDATE clientes SET meses_garantia = ? WHERE id = ?",
                        (texto_meses(0 if garantia == "No" else 1), id_))
    con.execute("UPDATE colocaciones SET meses_garantia = CAST((CAST(dias_garantia AS INTEGER) + 29) / 30 AS TEXT) "
                "WHERE CAST(dias_garantia AS INTEGER) > 0 AND COALESCE(garantia, '') <> 'No' "
                "AND (meses_garantia IS NULL OR meses_garantia IN ('', '0'))")
    for id_, meses in con.execute("SELECT id, (CAST(dias_garantia AS INTEGER) + 29) / 30 FROM clientes "
                                  "WHERE CAST(dias_garantia AS INTEGER) > 0 "
                                  "AND (meses_garantia IS NULL OR meses_garantia = '')").fetchall():
        con.execute("UPDATE clientes SET meses_garantia = ? WHERE id = ?", (texto_meses(meses), id_))
    if primera_conversion:
        # Servitotal proponía 30 días a los clientes sin plazo escrito: siguen con un mes (y no con los 2 por defecto).
        sin_no = " AND COALESCE(garantia, '') <> 'No'" if "garantia" in {
            fila[1] for fila in con.execute("PRAGMA table_info(clientes)")} else ""
        con.execute("UPDATE clientes SET meses_garantia = ? WHERE (meses_garantia IS NULL OR meses_garantia = '') "
                    "AND (dias_garantia IS NULL OR dias_garantia = '')" + sin_no, (texto_meses(1),))


class BaseDatos:
''')
cambio("copia previa también para pasar las garantías a meses", '''                if not existentes or set(claves(campos)) - existentes:
                    return True
            return not con.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'areas'").fetchone()''',
       '''                if not existentes or set(claves(campos)) - existentes:
                    return True
            if _garantias_pendientes(con):      # garantías de Servitotal en días: pasan a meses con copia previa
                return True
            return not con.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'areas'").fetchone()''')
cambio("firmas de contratos de Servitotal con tres firmas", '''def tamano_firma(nombre):''', '''def tamano_firma(nombre, ancho=200):''')
cambio("firmas de contratos de Servitotal con tres firmas (ancho)",
       '''    return max(9, min(16, int(200 / (0.6 * max(len(nombre), 1)))))''',
       '''    return max(9, min(16, int(ancho / (0.6 * max(len(nombre), 1)))))''')
cambio("contratos firmados antes con tres firmas", '''    documento = re.sub(r'<span class="nombre-firma" style="font-size:\\d+pt">([^<]*)</span>',
                       lambda m: (f'<span class="nombre-firma" style="font-size:{tamano_firma(html.unescape(m[1]))}pt">'
                                  f'{m[1]}</span>'), documento)''',
       '''    # Los contratos que Servitotal firmó antes tienen tres firmas por renglón (EMPRESA, EMPLEADOR y PERSONA),
    # en recuadros de unos 133 pt: el nombre ocupa como mucho 120 pt.
    ancho = 120 if '<div class="linea">PERSONA</div>' in documento else 200
    documento = re.sub(r'<span class="nombre-firma" style="font-size:\\d+pt">([^<]*)</span>',
                       lambda m: (f'<span class="nombre-firma" style="font-size:{tamano_firma(html.unescape(m[1]), ancho)}pt">'
                                  f'{m[1]}</span>'), documento)''')
cambio("nunca ofrecer la base de otra agencia", '''    mejor = None
    for ruta in candidatas.values():
        datos = contar_datos(ruta)''', '''    mejor = None
    for ruta in candidatas.values():
        if _de_otra_agencia(ruta):      # p. ej. la de Servicio Exclusivo, si su programa está en el mismo equipo
            continue
        datos = contar_datos(ruta)''')
cambio("nunca ofrecer la base de otra agencia (función)", '''def buscar_datos_anteriores(''', '''def _de_otra_agencia(ruta):
    """True si junto a esa base está el programa de otra agencia (su agencia.py tiene otro AGENCIA_ESLOGAN)."""
    try:
        texto = Path(ruta).with_name("agencia.py").read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    eslogan = re.search(r'^AGENCIA_ESLOGAN = "([^"]*)"', texto, re.M)
    return bool(eslogan) and eslogan.group(1) != AGENCIA_ESLOGAN


def buscar_datos_anteriores(''')

cambio("al frente al abrirlo desde «Terminar» del instalador (función)", '''def reabrir_con_tk_moderno():''', '''def traer_al_frente(root):
    """Windows puede dejar detrás de las demás ventanas un programa abierto por otro que se está cerrando (el botón
    «Terminar» del instalador): parecería que no se abrió nada. Se muestra un momento por encima de todo y toma el
    foco; luego vuelve a ser una ventana normal."""
    if not ES_WINDOWS:
        return

    def soltar():
        try:
            root.attributes("-topmost", False)
        except tk.TclError:          # la ventana ya se cerró
            pass

    try:
        root.deiconify()
        root.lift()
        root.attributes("-topmost", True)
        root.focus_force()
        root.after(1500, soltar)
    except tk.TclError:
        pass


def reabrir_con_tk_moderno():''')
cambio("al frente al abrirlo desde «Terminar» del instalador", '''        root.destroy()
        return
    if aviso:
        root.after(400, lambda: messagebox.showwarning("Base de datos restaurada", aviso))
    elif oferta:''', '''        root.destroy()
        return
    traer_al_frente(root)
    if aviso:
        root.after(400, lambda: messagebox.showwarning("Base de datos restaurada", aviso))
    elif oferta:''')


# ---------------------------------------------------------------- Pruebas de Servicio Exclusivo
# Se usan las mismas pruebas; solo cambian las que miran los datos propios de cada agencia.
PRUEBAS = {
    "test_agencia.py": [
        ("carpeta de datos propia", '''"Library", "Application Support", agencia.AGENCIA_NOMBRE))''',
         '''"Library", "Application Support", agencia.AGENCIA_CARPETA_DATOS))'''),
        ("carpeta de datos propia", '''os.path.join("C:\\\\L", agencia.AGENCIA_NOMBRE))''',
         '''os.path.join("C:\\\\L", agencia.AGENCIA_CARPETA_DATOS))'''),
        ("carpeta de datos propia", '''".local", "share", agencia.AGENCIA_NOMBRE))''',
         '''".local", "share", agencia.AGENCIA_CARPETA_DATOS))'''),
        ("copias en Respaldos Servitotal", '''endswith("Respaldos " + agencia.AGENCIA_NOMBRE)''',
         '''endswith("Respaldos " + agencia.AGENCIA_CARPETA_DATOS)'''),
        ("ícono propio de Servitotal (120 px)", '''self.assertEqual(struct.unpack(">II", png[16:24]), (256, 256))''',
         '''self.assertEqual(struct.unpack(">II", png[16:24]), (120, 120))      # el ícono de Servitotal'''),
        ("ícono propio de Servitotal (120 px)", '''self.assertEqual(root._icono.width(), 256)''',
         '''self.assertEqual(root._icono.width(), 120)      # el ícono de Servitotal'''),
        ("clientes de la primera versión de Servitotal: 30 días = 1 mes",
         '''{"Con": "2 meses", "Sin": "Sin garantía", "Vacio": "2 meses"})''',
         '''{"Con": "1 mes", "Sin": "Sin garantía", "Vacio": "1 mes"})     # sus 30 días'''),
    ],
    "test_windows.py": [
        ("carpeta de datos propia", '''os.path.join("L", agencia.AGENCIA_NOMBRE))''',
         '''os.path.join("L", agencia.AGENCIA_CARPETA_DATOS))'''),
        ("carpeta de datos propia", '''self.base("AppData/Local/Agencia de Empleos/agencia.db", clientes=9)''',
         '''self.base("AppData/Local/Servitotal/agencia.db", clientes=9)'''),
        ("Python 3.8 y 3.9 (Servitotal los admite)", '''import unittest\n''',
         '''import unittest\n\n# ignore_cleanup_errors existe desde Python 3.10; Servitotal también se prueba con 3.8 y 3.9\n'''
         '''SIN_ERRORES_AL_LIMPIAR = {"ignore_cleanup_errors": True} if sys.version_info >= (3, 10) else {}\n'''),
        ("Python 3.8 y 3.9", '''tempfile.TemporaryDirectory(prefix="csv-excel-", ignore_cleanup_errors=True)''',
         '''tempfile.TemporaryDirectory(prefix="csv-excel-", **SIN_ERRORES_AL_LIMPIAR)'''),
        ("Python 3.8 y 3.9", '''tempfile.TemporaryDirectory(prefix="rutas ñ #% ", ignore_cleanup_errors=True)''',
         '''tempfile.TemporaryDirectory(prefix="rutas ñ #% ", **SIN_ERRORES_AL_LIMPIAR)'''),
        ("Python 3.8 y 3.9", '''tempfile.TemporaryDirectory(prefix="casa-ficticia-", ignore_cleanup_errors=True)''',
         '''tempfile.TemporaryDirectory(prefix="casa-ficticia-", **SIN_ERRORES_AL_LIMPIAR)'''),
    ],
}
EJEMPLOS = [".github/windows/vieja_1_7_0.sql"]     # base ficticia de Servicio Exclusivo 1.7.0 que usan las pruebas


cambio("nunca usar la carpeta de copias de otra agencia",
       '''        if os.path.isdir(carpeta) and any(PATRON_EXTERNA.fullmatch(nombre) for nombre in os.listdir(carpeta)):''',
       '''        if os.path.isdir(carpeta) and any(nombre.startswith(".copias-") for nombre in os.listdir(carpeta)):
            return False     # la eligió el programa de otra agencia: sus copias no se tocan
        if os.path.isdir(carpeta) and any(PATRON_EXTERNA.fullmatch(nombre) for nombre in os.listdir(carpeta)):''')
cambio("el fin de una garantía iniciada solo cambia si cambia su plazo",
       '''                    inicio = leer_fecha(actual["fecha_inicio"])
                    if inicio:
                        acuerdo = dict(actual, **d)''',
       '''                    inicio = leer_fecha(actual["fecha_inicio"])
                    # Una garantía ya iniciada conserva su fecha de fin si no cambian el plazo ni la fecha del contrato
                    # (las de Servitotal en días, por ejemplo, terminan a los 30 días aunque ahora digan «1 mes»).
                    if inicio and (not actual.get("fin_garantia") or any(
                            str(d.get(clave, actual.get(clave))) != str(actual.get(clave))
                            for clave in ("meses_garantia", "fecha_contrato"))):
                        acuerdo = dict(actual, **d)''')
cambio("«1 mes» en la lista de contratos", '''f"{meses_de_garantia(c)} meses" if con_garantia(c) else "No",''',
       '''texto_meses(meses_de_garantia(c)) if con_garantia(c) else "No",''')


def igualar(texto_tia, cambios=None):
    texto = texto_tia
    for motivo, viejo, nuevo, veces in (CAMBIOS if cambios is None else cambios):
        texto = reemplazar(texto, viejo, nuevo, veces, motivo)
    return texto


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    tia, prima = Path(argv[1]), Path(argv[2])
    salidas = {}
    try:
        salidas["agencia.py"] = igualar((tia / "agencia.py").read_text(encoding="utf-8"))
        for prueba in sorted(tia.glob("test_*.py")):
            if prueba.name == "test_instaladores_fiabilidad.py":      # los paquetes de cada agencia son distintos
                continue
            cambios = [(m, v, n, 1) for m, v, n in PRUEBAS.get(prueba.name, [])]
            salidas[prueba.name] = igualar(prueba.read_text(encoding="utf-8"), cambios)
    except TextoNoEncontrado as error:
        print(f"No se igualó nada. Revise este cambio en igualar_con_tia.py:\n{error}", file=sys.stderr)
        return 1
    for nombre, texto in salidas.items():
        compile(texto, nombre, "exec")
    for nombre, texto in salidas.items():
        (prima / nombre).write_text(texto, encoding="utf-8")
    for ejemplo in EJEMPLOS:
        (prima / ejemplo).parent.mkdir(parents=True, exist_ok=True)
        (prima / ejemplo).write_bytes((tia / ejemplo).read_bytes())
    print(f"Listo: {prima} tiene el programa y las pruebas de {tia} con los colores y datos de Servitotal "
          f"({len(CAMBIOS)} cambios en el programa).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
