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
        ("avisos: una tabla más en la base",
         '''self.assertEqual(set(contar_datos(self.ruta)), {"clientes", "trabajadoras", "colocaciones"})''',
         '''self.assertEqual(set(contar_datos(self.ruta)), {"clientes", "trabajadoras", "colocaciones", "avisos"})'''),
        ("avisos: una tabla más en la base",
         '''self.assertEqual(contar_datos(antigua), {"clientes": 1, "trabajadoras": 0, "colocaciones": 0})''',
         '''self.assertEqual(contar_datos(antigua), {"clientes": 1, "trabajadoras": 0, "colocaciones": 0, "avisos": 0})'''),
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
        ("avisos: también Avisos.csv", '''NOMBRES = ("Clientes.csv", "Trabajadoras.csv", "Asignaciones.csv", "Areas.csv")''',
         '''NOMBRES = ("Clientes.csv", "Trabajadoras.csv", "Asignaciones.csv", "Areas.csv", "Avisos.csv")'''),
    ],
    "test_fiabilidad_exportacion.py": [
        ("avisos: también Avisos.csv", '''NOMBRES = ("Clientes.csv", "Trabajadoras.csv", "Asignaciones.csv", "Areas.csv")''',
         '''NOMBRES = ("Clientes.csv", "Trabajadoras.csv", "Asignaciones.csv", "Areas.csv", "Avisos.csv")'''),
    ],
    "test_fiabilidad_finanzas.py": [
        ("avisos: Ganancias también muestra las finanzas del día",
         '''            resumen = ag.resumen_ganancias(self.filas(["1e308", "1e308"]), [], date(2026, 9, 29))
            app = SimpleNamespace(db=SimpleNamespace(), resumen_financiero=lambda: resumen,''',
         '''            resumen = ag.resumen_con_avisos(ag.resumen_ganancias(self.filas(["1e308", "1e308"]), [],
                                                                 date(2026, 9, 29)), [])
            app = SimpleNamespace(db=SimpleNamespace(), resumen_financiero=lambda: resumen,
                                  finanzas=lambda dia: ag.finanzas_del_dia([], [], dia),'''),
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


# ---------------------------------------------------------------- Avisos y finanzas del día (solo Servitotal)
# La agencia cobra por cada aviso que pega afuera de su local (S/ 10). En Ganancias se ven la ganancia de avisos, la
# de colocación de personal y las finanzas del día (con su semana y su mes), y ahí se anotan los avisos uno por uno.
cambio("versión de Servitotal con avisos", 'VERSION = "1.8.0"', 'VERSION = "1.9.0"')
cambio("avisos: tabla", '''TABLAS = {
''', '''# Avisos que la agencia pega afuera de su local: cuándo, de quién (opcional) y cuánto pagaron.
CAMPOS_AVISO = [("fecha", "Fecha"), ("detalle", "Aviso de"), ("monto", "Monto"), ("registrado", "Anotado")]

TABLAS = {
''')
cambio("avisos: tabla (en TABLAS)", '''    "colocaciones": CAMPOS_COLOCACION + [("dias_garantia", "dias_garantia")],   # garantía en días de Servitotal
}''', '''    "colocaciones": CAMPOS_COLOCACION + [("dias_garantia", "dias_garantia")],   # garantía en días de Servitotal
    "avisos": CAMPOS_AVISO,
}''')
cambio("avisos: cálculos", '''

# ---------------------------------------------------------------- Campos
''', r'''

# ---------------------------------------------------------------- Avisos y finanzas del día
PRECIO_AVISO = "10.00"      # lo que pagan por cada aviso pegado afuera del local
MONTO_MAXIMO_AVISO = Decimal("99999.99")
DIAS_SEMANA = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MESES_DEL_ANIO = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
                  "octubre", "noviembre", "diciembre")


def monto_aviso(aviso):
    """Lo que pagaron por un aviso; None si el monto no es válido."""
    monto = leer_decimal(aviso.get("monto"))
    return monto if monto is not None and 0 < monto <= MONTO_MAXIMO_AVISO else None


def validar_aviso(datos):
    """Revisa un aviso antes de guardarlo: (datos listos para guardar, None) o (None, qué corregir)."""
    fecha = leer_fecha(str(datos.get("fecha") or ""))
    if fecha is None:
        return None, f"Escriba la fecha del aviso como día/mes/año, por ejemplo {hoy()}."
    # «S/. 10»: el punto es del símbolo de la moneda, no de los decimales
    escrito = re.sub(r"^\s*" + re.escape(MONEDA) + r"\.?", "", str(datos.get("monto") or "")).strip()
    monto = leer_decimal(escrito)
    centavos = importe_texto(monto) if monto is not None else None      # como se guardará
    if centavos is None or Decimal(centavos) <= 0:
        return None, "Escriba cuánto pagaron por el aviso, por ejemplo 10."
    if monto > MONTO_MAXIMO_AVISO:
        return None, f"Revise el monto del aviso: {dinero(monto)} parece un error."
    detalle = " ".join(str(datos.get("detalle") or "").split())[:120]
    return {"fecha": fecha.strftime(FMT_FECHA), "detalle": detalle, "monto": centavos}, None


def nombre_del_dia(dia):
    """«martes 14/10/2026»."""
    return f"{DIAS_SEMANA[dia.weekday()]} {dia.strftime(FMT_FECHA)}"


def periodos_de(dia):
    """(desde, hasta) del día, de su semana (de lunes a domingo, como en Ganancias) y de su mes."""
    lunes = dia - timedelta(days=dia.weekday())
    mes_siguiente = (dia.replace(day=28) + timedelta(days=4)).replace(day=1)
    return {"dia": (dia, dia), "semana": (lunes, lunes + timedelta(days=6)),
            "mes": (dia.replace(day=1), mes_siguiente - timedelta(days=1))}


def finanzas_del_dia(colocaciones, avisos, dia):
    """Finanzas del día elegido, de su semana y de su mes:
    - avisos: los anotados con esa fecha; su ganancia es lo que pagaron por ellos;
    - personal colocado: las asignaciones hechas ese día (su fecha de asignación), sin las deshechas;
    - ganancia de colocación de personal: las comisiones cobradas ese día (su fecha de pago, como en Ganancias).
    Devuelve {"dia", "desde_hasta", "periodos": {"dia"|"semana"|"mes": {...}}, "avisos_del_dia"}."""
    periodos = periodos_de(dia)
    cuentas = {periodo: {"avisos": 0, "ganancia_avisos": Decimal(0), "colocados": 0,
                         "ganancia_colocacion": Decimal(0)} for periodo in periodos}

    def sumar(fecha, campo, cantidad):
        for periodo, (desde, hasta) in periodos.items():
            if desde <= fecha <= hasta:
                cuentas[periodo][campo] += cantidad

    del_dia = []
    for aviso in avisos:
        fecha = leer_fecha(str(aviso.get("fecha") or ""))
        if fecha is None:
            continue
        sumar(fecha, "avisos", 1)
        monto = monto_aviso(aviso)
        if monto is not None:
            sumar(fecha, "ganancia_avisos", monto)
        if fecha == dia:
            del_dia.append(aviso)
    for colocacion in colocaciones:
        asignada = leer_fecha(str(colocacion.get("fecha_enlace") or ""))
        if asignada is not None and colocacion.get("estado") != "Cancelada":      # «Deshacer asignación»
            sumar(asignada, "colocados", 1)
        if colocacion.get("comision_pagada") == "1":
            pagada = leer_fecha(str(colocacion.get("fecha_pago") or ""))
            monto = leer_decimal(colocacion.get("comision"))
            if pagada is not None and monto is not None and monto > 0:
                sumar(pagada, "ganancia_colocacion", monto)
    for cuenta in cuentas.values():
        cuenta["total"] = cuenta["ganancia_avisos"] + cuenta["ganancia_colocacion"]
    del_dia.sort(key=lambda aviso: (str(aviso.get("registrado") or ""), aviso.get("id") or 0))
    return {"dia": dia, "desde_hasta": periodos, "periodos": cuentas, "avisos_del_dia": del_dia}


def resumen_con_avisos(resumen, avisos):
    """El resumen de Ganancias más «Ganancia de avisos» y «Ganancia total» (comisiones cobradas más avisos), con el
    mismo tipo que los demás importes: float, o Decimal si el resumen se desbordó."""
    total = sum((monto for monto in map(monto_aviso, avisos) if monto is not None), Decimal(0))
    cobrado = resumen["cobrado_total"]
    ganancia = (cobrado if isinstance(cobrado, Decimal) else Decimal(repr(cobrado))) + total
    if isinstance(cobrado, Decimal) or not math.isfinite(float(ganancia)):
        return dict(resumen, avisos_total=total, ganancia_total=ganancia)
    return dict(resumen, avisos_total=float(total), ganancia_total=float(ganancia))


# ---------------------------------------------------------------- Campos
''')
cambio("avisos: en la exportación a Excel", '''con.execute("BEGIN")  # las cuatro tablas corresponden a la misma instantánea de solo lectura''',
       '''con.execute("BEGIN")  # las cinco tablas corresponden a la misma instantánea de solo lectura''')
cambio("avisos: en la exportación a Excel (tabla)", '''            for tabla, nombre in (("clientes", "Clientes"), ("trabajadoras", "Trabajadoras"),
                                  ("colocaciones", "Asignaciones"), ("areas", "Areas")):''',
       '''            for tabla, nombre in (("clientes", "Clientes"), ("trabajadoras", "Trabajadoras"),
                                  ("colocaciones", "Asignaciones"), ("areas", "Areas"), ("avisos", "Avisos")):''')
cambio("avisos: ventana y finanzas del día", '''class PaginaGanancias(ttk.Frame):''', r'''class DialogoAviso(tk.Toplevel):
    """Anotar o corregir un aviso: la fecha, de quién es (opcional) y cuánto pagaron."""

    def __init__(self, master, valores, al_guardar, titulo="Nuevo aviso"):
        principal = master.winfo_toplevel()
        super().__init__(principal)
        self.al_guardar = al_guardar
        self.title(titulo)
        self.configure(bg=C["fondo"])
        self.resizable(False, False)
        self.transient(principal)
        centrar(self, 520, 390, principal)
        cont = ttk.Frame(self, padding=(26, 22, 26, 20))
        cont.pack(fill="both", expand=True)
        botones = ttk.Frame(cont)
        botones.pack(side="bottom", fill="x", pady=(18, 0))   # se reservan primero: nunca quedan cortados
        ttk.Button(botones, text="Guardar", style="Primario.TButton", command=self.guardar).pack(side="right")
        ttk.Button(botones, text="Cancelar", style="Secundario.TButton",
                   command=self.destroy).pack(side="right", padx=(0, 8))
        ttk.Label(cont, text=titulo, style="Detalle.TLabel").pack(anchor="w")
        ttk.Label(cont, text="Lo que pagan por un aviso pegado afuera del local.", style="Tenue.TLabel",
                  wraplength=round(420 * escala_pantalla(self)), justify="left").pack(anchor="w", pady=(4, 14))
        campos = ttk.Frame(cont)
        campos.pack(fill="x")
        campos.columnconfigure(1, weight=1)
        self.valores, entradas = {}, {}
        for fila, (clave, etiqueta) in ((0, ("fecha", "Fecha")), (1, ("detalle", "Aviso de")),
                                        (3, ("monto", f"Monto ({MONEDA})"))):
            ttk.Label(campos, text=etiqueta).grid(row=fila, column=0, sticky="w", padx=(0, 14), pady=5)
            self.valores[clave] = tk.StringVar(value=str(valores.get(clave) or ""))
            entradas[clave] = ttk.Entry(campos, textvariable=self.valores[clave])
            entradas[clave].grid(row=fila, column=1, sticky="ew", pady=5)
        ttk.Label(campos, text="Opcional. Por ejemplo: Sra. Rosa, busca niñera.", style="Tenue.TLabel").grid(
            row=2, column=1, sticky="w", pady=(0, 4))
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Return>", self.guardar)
        self.bind("<Escape>", lambda _evento: self.destroy())
        entradas["detalle"].focus_set()
        self.grab_set()

    def guardar(self, _evento=None):
        datos, error = validar_aviso({clave: valor.get() for clave, valor in self.valores.items()})
        if error:
            messagebox.showwarning(self.title(), error, parent=self)
            return
        if self.al_guardar(datos) is not False:
            self.destroy()


class PanelFinanzas(ttk.Frame):
    """«Finanzas del día» en Ganancias: avisos y personal colocado del día elegido, de su semana y de su mes, y la
    lista de los avisos de ese día. Las flechas cambian de día y «Hoy» vuelve al día de hoy."""
    FILAS = (("avisos", "Avisos", "cantidad"), ("ganancia_avisos", "Ganancia de avisos", "dinero"),
             ("colocados", "Personal colocado", "cantidad"),
             ("ganancia_colocacion", "Ganancia de colocación de personal", "dinero"),
             ("total", "Total", "dinero"))
    COLUMNAS = (("dia", "Ese día"), ("semana", "Esa semana"), ("mes", "Ese mes"))

    def __init__(self, master, app):
        super().__init__(master, style="Fondo.TFrame")
        self.app = app
        self.dia = None          # None: hoy (también si el programa sigue abierto después de medianoche)
        self._mostrado = None
        self._avisos = {}
        borde, dentro = tarjeta(self)
        borde.pack(fill="both", expand=True)

        ttk.Label(dentro, text="Finanzas del día", style="Detalle.TLabel").pack(anchor="w")
        navegar = ttk.Frame(dentro)                 # en su propia fila: cabe también con letra grande (125-150 %)
        navegar.pack(anchor="w", pady=(10, 0))
        ttk.Button(navegar, text="←", width=3, style="Pequeno.TButton",
                   command=lambda: self.mover(-1)).pack(side="left")
        self.etiqueta_dia = ttk.Label(navegar, font=F["negrita"], anchor="center")
        self.etiqueta_dia.pack(side="left", padx=10)
        ttk.Button(navegar, text="→", width=3, style="Pequeno.TButton",
                   command=lambda: self.mover(1)).pack(side="left")
        self.boton_hoy = ttk.Button(navegar, text="Hoy", style="Pequeno.TButton", command=self.ir_a_hoy)
        self.boton_hoy.pack(side="left", padx=(8, 0))
        explicacion = ttk.Label(dentro, style="Tenue.TLabel", justify="left", text=(
            "Avisos: lo que pagan por cada aviso pegado afuera del local. Personal colocado: asignaciones hechas "
            "ese día. Ganancia de colocación de personal: comisiones cobradas ese día."))
        explicacion.pack(fill="x", anchor="w", pady=(8, 14))
        self._titulos_filas = []

        def ajustar_textos(evento):
            explicacion.configure(wraplength=max(200, evento.width - 50))
            for titulo in self._titulos_filas:          # «Ganancia de colocación de personal» pasa a dos renglones
                titulo.configure(wraplength=max(110, int(evento.width * 0.34)))

        dentro.bind("<Configure>", ajustar_textos, add="+")

        tabla = ttk.Frame(dentro)
        tabla.pack(fill="x")
        tabla.columnconfigure(0, weight=2)
        self.rangos, self.celdas = {}, {}
        for columna, (periodo, titulo) in enumerate(self.COLUMNAS, start=1):
            tabla.columnconfigure(columna, weight=1, uniform="periodo")
            ttk.Label(tabla, text=titulo, font=F["negrita"]).grid(row=0, column=columna, sticky="e", padx=(12, 0))
            self.rangos[periodo] = ttk.Label(tabla, style="Tenue.TLabel")
            self.rangos[periodo].grid(row=1, column=columna, sticky="e", padx=(12, 0))
        fila = 2
        for clave, titulo, _tipo in self.FILAS:
            tk.Frame(tabla, bg=C["borde"], height=1).grid(row=fila, column=0, columnspan=4, sticky="ew",
                                                          pady=(8, 4) if fila == 2 else (4, 4))
            fila += 1
            fuente = F["negrita"] if clave == "total" else F["base"]
            titulo_fila = ttk.Label(tabla, text=titulo, font=fuente, justify="left")
            titulo_fila.grid(row=fila, column=0, sticky="w", pady=3)
            self._titulos_filas.append(titulo_fila)
            for columna, (periodo, _) in enumerate(self.COLUMNAS, start=1):
                celda = ttk.Label(tabla, font=fuente, foreground=C["acento"] if clave == "total" else C["texto"])
                celda.grid(row=fila, column=columna, sticky="e", padx=(12, 0), pady=3)
                self.celdas[clave, periodo] = celda
            fila += 1

        cab_lista = ttk.Frame(dentro)
        cab_lista.pack(fill="x", pady=(22, 0))
        self.titulo_lista = ttk.Label(cab_lista, font=F["marca"])
        self.titulo_lista.pack(side="left")
        ttk.Button(cab_lista, text="Eliminar", style="Peligro.TButton", command=self.eliminar).pack(side="right")
        ttk.Button(cab_lista, text="Corregir", style="Pequeno.TButton",
                   command=self.corregir).pack(side="right", padx=8)
        marco, self.lista = crear_tabla(dentro, [("hora", "Anotado", 110), ("detalle", "Aviso de", 300),
                                                 ("monto", "Monto", 120)], horizontal=True)
        self.lista.configure(height=5)
        self._estado_lista = {}
        marco.pack(fill="x", pady=(10, 0))
        self.lista.bind("<Double-1>", lambda _evento: self.corregir())
        self.sin_avisos = ttk.Label(dentro, text="No hay avisos anotados este día.", style="Tenue.TLabel")

    def dia_elegido(self):
        return self.dia or date.today()

    def ir_a(self, dia):
        self.dia = None if dia == date.today() else dia
        self.refrescar()

    def mover(self, dias):
        self.ir_a(self.dia_elegido() + timedelta(days=dias))

    def ir_a_hoy(self):
        self.ir_a(date.today())

    def refrescar(self):
        dia = self.dia_elegido()
        finanzas = self.app.finanzas(dia)
        if self._mostrado is finanzas:
            return
        self._mostrado = finanzas
        es_hoy = dia == date.today()
        self.etiqueta_dia.configure(text=("hoy, " if es_hoy else "") + nombre_del_dia(dia))
        self.boton_hoy.state(["disabled"] if es_hoy else ["!disabled"])
        lunes, domingo = finanzas["desde_hasta"]["semana"]
        self.rangos["dia"].configure(text=dia.strftime("%d/%m"))
        self.rangos["semana"].configure(text=f"{lunes:%d/%m} al {domingo:%d/%m}")
        self.rangos["mes"].configure(text=f"{MESES_DEL_ANIO[dia.month - 1]} {dia.year}")
        for clave, _titulo, tipo in self.FILAS:
            for periodo, _ in self.COLUMNAS:
                valor = finanzas["periodos"][periodo][clave]
                self.celdas[clave, periodo].configure(text=dinero(valor) if tipo == "dinero" else str(valor))
        self.titulo_lista.configure(text="Avisos de hoy" if es_hoy else f"Avisos del {dia:%d/%m/%Y}")
        self._avisos = {str(aviso["id"]): aviso for aviso in finanzas["avisos_del_dia"]}
        entradas = []
        for indice, (iid, aviso) in enumerate(self._avisos.items()):
            registrado = str(aviso.get("registrado") or "")
            entradas.append((iid, (PAD + (registrado[11:16] if len(registrado) >= 16 else "-"),
                                   PAD + (aviso.get("detalle") or "-"), PAD + dinero(aviso.get("monto"))),
                             ("impar" if indice % 2 else "par",)))
        Pagina._sincronizar_tabla(self.lista, self._estado_lista, entradas, set(self._avisos))   # conserva la selección
        if self._avisos:
            self.sin_avisos.pack_forget()
        elif not self.sin_avisos.winfo_manager():
            self.sin_avisos.pack(anchor="w", pady=(10, 0))

    def rueda_propia(self):
        """La rueda sobre la lista de avisos la recorre si hay más avisos de los que se ven; si no, mueve la página.
        (Se llama después de que la página dirige la rueda a su desplazamiento.)"""
        etiqueta = f"ListaAvisos{id(self)}"

        def rueda(evento, pasos=None):
            if pasos is None:
                pasos = -1 if evento.delta > 0 else 1
            inicio, fin = self.lista.yview()
            if (pasos > 0 and fin < 1) or (pasos < 0 and inicio > 0):
                self.lista.yview_scroll(pasos, "units")
                return "break"
            return None

        self.lista.bind_class(etiqueta, "<MouseWheel>", rueda)
        self.lista.bind_class(etiqueta, "<Button-4>", lambda evento: rueda(evento, -1))
        self.lista.bind_class(etiqueta, "<Button-5>", lambda evento: rueda(evento, 1))
        self.lista.bindtags((etiqueta,) + tuple(t for t in self.lista.bindtags() if t != etiqueta))

    def nuevo_aviso(self):
        return DialogoAviso(self, {"fecha": self.dia_elegido().strftime(FMT_FECHA), "monto": PRECIO_AVISO},
                            self._guardar_nuevo)

    def _guardar_nuevo(self, datos):
        self.app.guardar_aviso(datos)
        self.ir_a(leer_fecha(datos["fecha"]))

    def elegido(self, accion):
        seleccion = self.lista.selection()
        if not seleccion or seleccion[0] not in self._avisos:
            messagebox.showinfo(accion, "Primero elija un aviso de la lista.", parent=self.winfo_toplevel())
            return None
        return self._avisos[seleccion[0]]

    def corregir(self):
        aviso = self.elegido("Corregir aviso")
        if aviso is not None:
            return DialogoAviso(self, aviso, lambda datos: self._guardar_cambio(aviso["id"], datos),
                                titulo="Corregir aviso")
        return None

    def _guardar_cambio(self, id_, datos):
        if self.app.guardar_aviso(datos, id_) is None:
            messagebox.showwarning("Corregir aviso", "Este aviso ya no existe: se eliminó desde otra ventana del "
                                   "programa. Revise la lista.", parent=self.winfo_toplevel())
            return
        self.ir_a(leer_fecha(datos["fecha"]))

    def eliminar(self):
        aviso = self.elegido("Eliminar aviso")
        if aviso is not None:
            self.app.eliminar_aviso(aviso, parent=self.winfo_toplevel())


class PaginaGanancias(ttk.Frame):''')
cambio("avisos: botón «Nuevo aviso» en Ganancias", '''        ttk.Button(cab, text="Ver comisiones", style="Pequeno.TButton",
                   command=lambda: app.mostrar(app.comisiones)).pack(side="right")''',
       '''        ttk.Button(cab, text="Ver comisiones", style="Pequeno.TButton",
                   command=lambda: app.mostrar(app.comisiones)).pack(side="right")
        ttk.Button(cab, text="Nuevo aviso", style="Primario.TButton",
                   command=lambda: self.finanzas.nuevo_aviso()).pack(side="right", padx=(0, 8))''')
cambio("avisos: ganancia de avisos y de colocación de personal", '''        definicion = (("cobrado_total", "Cobrado en total", C["acento"]),
                      ("cobrado_semana", "Cobrado esta semana", C["texto"]),
                      ("cobrado_mes", "Cobrado este mes", C["texto"]),
                      ("por_cobrar", "Pendiente de cobro", C["peligro"]))''',
       '''        # Lo de la semana y el mes está en «Finanzas del día», con los avisos y el personal colocado.
        definicion = (("ganancia_total", "Ganancia total", C["acento"]),
                      ("cobrado_total", "Ganancia de colocación de personal", C["texto"]),
                      ("avisos_total", "Ganancia de avisos", C["texto"]),
                      ("por_cobrar", "Pendiente de cobro", C["peligro"]))''')
cambio("avisos: títulos largos de las cifras", '''            ttk.Label(interior, text=titulo, style="Tenue.TLabel").pack(anchor="w", pady=(5, 0))''',
       '''            leyenda = ttk.Label(interior, text=titulo, style="Tenue.TLabel", justify="left")
            leyenda.pack(anchor="w", pady=(5, 0))
            interior.bind("<Configure>", lambda evento, leyenda=leyenda: leyenda.configure(
                wraplength=max(90, evento.width - 52)), add="+")       # menos el margen de la tarjeta''')
cambio("avisos: finanzas del día en Ganancias", '''        paneles = ttk.Frame(cuerpo, style="Fondo.TFrame")
        paneles.pack(fill="both", expand=True, pady=(16, 0))''',
       '''        # Las cuatro cifras van en una fila si caben enteras; si no (ventana angosta o letra grande), de dos en dos.
        self._indicadores = indicadores
        self._tarjetas = sorted(indicadores.grid_slaves(), key=lambda borde: int(borde.grid_info()["column"]))
        self._columnas_cifras = len(self._tarjetas)
        indicadores.bind("<Configure>", lambda evento: self.acomodar_cifras(evento.width), add="+")
        self.finanzas = PanelFinanzas(cuerpo, app)
        self.finanzas.pack(fill="x", pady=(16, 0))
        paneles = ttk.Frame(cuerpo, style="Fondo.TFrame")
        paneles.pack(fill="both", expand=True, pady=(16, 0))''')
cambio("avisos: finanzas del día al refrescar Ganancias", '''    def refrescar(self):
        resumen = self.app.resumen_financiero()
        if self.resumen is resumen:
            return''', '''    def ancho_por_cifra(self):
        """Lo que necesita cada tarjeta para que su cifra se vea entera (con su margen y la separación)."""
        return max(max(cifra.winfo_reqwidth() for cifra in self.cifras.values()), 110) + 64

    def acomodar_cifras(self, ancho=None):
        ancho = ancho or self._indicadores.winfo_width()
        if ancho <= 1:
            return
        cantidad, pide = len(self._tarjetas), self.ancho_por_cifra()
        columnas = next((n for n in (cantidad, 2) if n * pide <= ancho + 14), 1)
        if columnas == self._columnas_cifras:
            return
        self._columnas_cifras = columnas
        for indice, borde in enumerate(self._tarjetas):
            fila, columna = divmod(indice, columnas)
            borde.grid_configure(row=fila, column=columna, pady=(0 if fila == 0 else 14, 0),
                                 padx=(0 if columna == 0 else 7, 0 if columna == columnas - 1 else 7))
        for columna in range(cantidad):
            self._indicadores.columnconfigure(columna, weight=1 if columna < columnas else 0,
                                              uniform="cifras" if columna < columnas else "")

    def refrescar(self):
        self.finanzas.refrescar()
        resumen = self.app.resumen_financiero()
        if self.resumen is resumen:
            return''')
cambio("avisos: resumen, finanzas del día y guardar o borrar avisos", '''        clave = (self.db.revision("colocaciones"), self.db.revision("clientes"),
                 fecha_hoy, tuple(AREAS.items()))
        anterior = getattr(self, "_resumen_financiero", None)
        if anterior is None or anterior[0] != clave:
            resumen = resumen_ganancias(self.db.todos("colocaciones"), self.db.todos("clientes"), fecha_hoy)
            self._resumen_financiero = (clave, resumen)
        return self._resumen_financiero[1]''', '''        clave = (self.db.revision("colocaciones"), self.db.revision("clientes"), self.db.revision("avisos"),
                 fecha_hoy, tuple(AREAS.items()))
        anterior = getattr(self, "_resumen_financiero", None)
        if anterior is None or anterior[0] != clave:
            resumen = resumen_ganancias(self.db.todos("colocaciones"), self.db.todos("clientes"), fecha_hoy)
            resumen = resumen_con_avisos(resumen, self.db.todos("avisos"))
            self._resumen_financiero = (clave, resumen)
        return self._resumen_financiero[1]

    def finanzas(self, dia):
        """Finanzas del día (avisos y personal colocado) para Ganancias; se recalculan solo si cambian los datos."""
        clave = (self.db.revision("colocaciones"), self.db.revision("avisos"), dia)
        anterior = getattr(self, "_finanzas", None)
        if anterior is None or anterior[0] != clave:
            self._finanzas = (clave, finanzas_del_dia(self.db.todos("colocaciones"), self.db.todos("avisos"), dia))
        return self._finanzas[1]

    def guardar_aviso(self, datos, id_=None):
        """Anota un aviso nuevo o corrige uno anotado (datos revisados con validar_aviso). Devuelve su número, o None
        si el aviso que se corregía ya no existe (se eliminó desde otra ventana del programa)."""
        with self.db.lote():
            self.db.con.execute("UPDATE avisos SET fecha = fecha WHERE 0")    # reserva la escritura antes de leer
            if id_ is None:
                id_ = self.db.insertar("avisos", dict(datos, registrado=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            elif leer_registro_actual(self.db, "avisos", id_) is None:
                id_ = None
            else:
                self.db.actualizar("avisos", id_, datos)
        self.refrescar_todo()
        return id_

    def eliminar_aviso(self, aviso, parent=None):
        """Borra un aviso después de confirmarlo y de guardar una copia de seguridad. True si se borró."""
        if leer_registro_actual(self.db, "avisos", aviso["id"]) is None:
            messagebox.showinfo("Eliminar aviso", "Este aviso ya no existe: se eliminó desde otra ventana del programa.",
                                parent=parent or self.root)
            self.refrescar_todo()
            return False
        de_quien = f" de {aviso['detalle']}" if aviso.get("detalle") else ""
        if not messagebox.askyesno(
                "Eliminar aviso", f"¿Eliminar el aviso{de_quien} del {aviso.get('fecha')} ({dinero(aviso.get('monto'))})?"
                "\\n\\nAntes se guarda una copia de seguridad.", parent=parent or self.root) \\
                or not self.copia_antes_de_borrar():
            return False
        with self.db.lote():
            self.db.eliminar("avisos", aviso["id"])
        self.refrescar_todo()
        return True''')

cambio("avisos: la rueda recorre la lista de avisos", """        self.desplazable.activar_rueda()

    def contar(self):
        return len(self.db.todos("colocaciones"))""", """        self.desplazable.activar_rueda()
        self.finanzas.rueda_propia()

    def contar(self):
        return len(self.db.todos("colocaciones"))""")
cambio("avisos: las cifras se acomodan cuando cambian", """            texto = dinero(self.resumen[clave])
            if etiqueta.cget("text") != texto:
                etiqueta.configure(text=texto)
        self.actualizar_areas()""", """            texto = dinero(self.resumen[clave])
            if etiqueta.cget("text") != texto:
                etiqueta.configure(text=texto)
        self.after_idle(self.acomodar_cifras)       # una cifra más larga puede necesitar otra disposición
        self.actualizar_areas()""")
cambio("avisos: restaurar una copia dice también cuántos avisos tiene", """                f"La copia tiene {copia['clientes']} clientes, {copia['trabajadoras']} trabajadoras y "
                f"{copia['colocaciones']} asignaciones.\\nAhora el programa tiene {ahora['clientes']} clientes, "
                f"{ahora['trabajadoras']} trabajadoras y {ahora['colocaciones']} asignaciones.\\n\\n\"""",
       """                f"La copia tiene {copia['clientes']} clientes, {copia['trabajadoras']} trabajadoras, "
                f"{copia['colocaciones']} asignaciones y {copia.get('avisos', 0)} avisos.\\nAhora el programa tiene "
                f"{ahora['clientes']} clientes, {ahora['trabajadoras']} trabajadoras, {ahora['colocaciones']} "
                f"asignaciones y {ahora.get('avisos', 0)} avisos.\\n\\n\"""")
cambio("avisos: traer datos dice también cuántos avisos", """        cantidades = (f"{copia['clientes']} clientes, {copia['trabajadoras']} trabajadoras y "
                      f"{copia['colocaciones']} asignaciones")""",
       """        cantidades = (f"{copia['clientes']} clientes, {copia['trabajadoras']} trabajadoras, "
                      f"{copia['colocaciones']} asignaciones y {copia.get('avisos', 0)} avisos")""")
cambio("avisos: columna en la lista de copias", """            ("clientes", "Clientes", 90), ("trab", "Trabajadoras", 120), ("asig", "Asignaciones", 120)])""",
       """            ("clientes", "Clientes", 90), ("trab", "Trabajadoras", 120), ("asig", "Asignaciones", 120),
            ("avisos", "Avisos", 80)])""")
cambio("avisos: columna en la lista de copias (valores)", """                f"{c['fecha']:%d/%m/%Y %H:%M}", c["tipo"], c["donde"], c["clientes"], c["trabajadoras"],
                c["colocaciones"])])""", """                f"{c['fecha']:%d/%m/%Y %H:%M}", c["tipo"], c["donde"], c["clientes"], c["trabajadoras"],
                c["colocaciones"], c.get("avisos", 0))])""")


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
