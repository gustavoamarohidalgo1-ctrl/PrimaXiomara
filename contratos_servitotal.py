"""Contrato de servicio propio de Servitotal, sin dependencias de la interfaz."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from html import escape


ORDINALES = (
    "PRIMERA", "SEGUNDA", "TERCERA", "CUARTA", "QUINTA", "SEXTA", "SÉPTIMA", "OCTAVA", "NOVENA",
)


def renderizar_hoja_servicio(c, cli, t, datos, *, config, monto, sueldo, plazo, equivalencia, firmas):
    """Genera el contrato original de servicio con los datos revisados antes de firmar.

    Los valores son texto y se escapan aquí. ``firmas`` contiene exclusivamente
    el HTML de firmas que la aplicación ya validó, dibujadas o con nombre.
    ``plazo`` expresa días o meses; el estado ``garantia = No`` permite prescindir
    de la garantía sin cambiar las condiciones propias del contrato de Servitotal.
    """
    def texto(valor):
        return escape(str(valor if valor is not None else ""), quote=True)

    def campo(valor, clase="medio"):
        return f'<span class="campo {clase}">{texto(valor) or "&nbsp;"}</span>'

    def fila(etiqueta_a, valor_a, etiqueta_b, valor_b):
        return (f'<div class="fila"><b>{etiqueta_a}</b>{campo(valor_a, "largo")}'
                f'<b>{etiqueta_b}</b>{campo(valor_b, "dni")}</div>')

    def firma(clave, rol, nombre):
        return (f'<div class="firma"><div class="trazo">{firmas.get(clave, "")}</div>'
                f'<div class="linea">{rol}</div><div class="quien">{texto(nombre)}</div></div>')

    fecha = None
    for valor in (datos.get("fecha_contrato"), c.get("fecha_contrato"), c.get("fecha_enlace")):
        try:
            fecha = datetime.strptime(str(valor or "").strip(), "%d/%m/%Y").date()
            break
        except ValueError:
            continue
    fecha = fecha or date.today()

    con_garantia = c.get("garantia") != "No" and bool(str(plazo or "").strip())
    if con_garantia:
        detalle = str(plazo).strip()
        if c.get("fecha_inicio") and c.get("fin_garantia"):
            detalle += f" (del {c['fecha_inicio']} al {c['fin_garantia']})"
        else:
            detalle += " contados desde el inicio del trabajo"
        garantia = f"con una garantía de {campo(detalle + ', con reemplazo sin costo')}"
    else:
        garantia = "<b>sin garantía</b>"

    try:
        sin_costo = Decimal(str(datos.get("comision", c.get("comision", ""))).strip()) == 0
    except InvalidOperation:
        sin_costo = False
    if c.get("reemplazo_de") and sin_costo:
        pago = (f"<b>EL EMPLEADOR</b> selecciona un personal del hogar en reemplazo del contrato "
                f"N° {campo(c['reemplazo_de'], 'corto')}, dentro de la garantía, por lo que no pagará monto "
                f"adicional a <b>LA EMPRESA</b>. Este cambio de personal sin costo se otorga {garantia}.")
    else:
        porcentaje = f", equivalente al {campo(equivalencia)}" if equivalencia else ""
        pago = (f"<b>EL EMPLEADOR</b> selecciona un personal del hogar y pagará a <b>LA EMPRESA</b> "
                f"la suma de {campo(monto)}{porcentaje} al momento de tomar al personal calificado "
                f"y con documentos en regla, {garantia}.")

    tercera = ("<b>EL EMPLEADOR</b> tendrá la facultad de solicitar el cambio del personal en caso no esté "
               "conforme con su servicio." if con_garantia else
               "Por haber optado <b>EL EMPLEADOR</b> por el servicio sin garantía, <b>LA EMPRESA</b> no está "
               "obligada a efectuar cambios del personal contratado.")
    novena = ("<b>EL EMPLEADOR</b> manifiesta que acepta llevar a la empleada con goce de haber, dejando "
              "abierta la posibilidad de cambiarla por un nuevo personal si no estuviera conforme con ella, "
              "sin reclamo a la empresa." if con_garantia else
              "<b>EL EMPLEADOR</b> manifiesta que acepta llevar a la empleada con goce de haber, conforme "
              "al servicio sin garantía elegido.")
    clausulas = [
        "<b>LA EMPRESA</b> ofrece seleccionar y calificar personal doméstico u otro para colocarlo al "
        "servicio de <b>EL EMPLEADOR</b>, quien a su vez lo entrevistará y calificará atendiendo a sus "
        "necesidades y condiciones propias, siendo de su exclusiva responsabilidad tomar los servicios "
        "de dicho personal, ya que es quien decide tomar los servicios de la empresa.",
        pago,
        tercera,
        f"<b>EL EMPLEADOR</b> se compromete a pagar puntualmente la remuneración mensual de la "
        f"empleada del hogar, pactada en la suma de {campo(sueldo)}, así como a respetar los días feriados.",
        "<b>EL EMPLEADOR</b> declara su conformidad con la empleada que trata y acepta las condiciones "
        "estipuladas en el presente contrato, obligándose a darles fiel cumplimiento.",
        "<b>LA EMPRESA</b> no se hace responsable de cualquier préstamo o adelanto de sueldo que "
        "pudiera otorgar <b>EL EMPLEADOR</b> a la empleada.",
        "Las partes declaran que en el presente contrato no existe coacción ni mala fe, sino la buena "
        "voluntad de servirse mutuamente.",
        f"En la fecha, <b>LA EMPRESA</b> selecciona a la Sra. {campo(t.get('nombre'))}, "
        f"identificada con DNI {campo(t.get('dni'), 'dni')}, percibiendo una remuneración de {campo(sueldo)}, "
        "correspondiente a sus servicios, con documentos en conformidad.",
        novena,
    ]
    cuerpo = "\n".join(f"<p><b>{ordinal}:</b> {clausula}</p>"
                       for ordinal, clausula in zip(ORDINALES, clausulas))
    empleador = "\n".join((
        fila("Sr.(a)", cli.get("nombre"), "con DNI", cli.get("dni")),
        fila("Ocupación", cli.get("ocupacion"), "celular", cli.get("telefono")),
        fila("Domicilio", cli.get("direccion"), "Distrito", cli.get("zona")),
    ))
    nota = (f'<p class="nota">Firmas registradas en el sistema de la agencia el '
            f'{texto(c.get("fecha_firma"))}.</p>' if c.get("contrato_firmado") == "1" else "")

    return f"""<section class="hoja">
<div class="numero">Contrato N° {texto(c.get('id'))}</div>
<h1>CONTRATO DE SERVICIO</h1>
<p>Conste por el presente documento privado de contrato de servicio que celebran, de una parte,
<b>{texto(str(config.get('nombre') or '').upper())}</b>, con domicilio legal en <b>{texto(config.get('direccion'))}</b>,
debidamente representada por <b>{texto(config.get('representante'))}</b> con DNI {texto(config.get('dni'))}
(en adelante, <b>LA EMPRESA</b>); y de la otra parte:</p>
{empleador}
<p>A quien en adelante se le denominará <b>EL EMPLEADOR</b>, en los términos y condiciones siguientes:</p>
{cuerpo}
<p class="aviso"><b>EL PERSONAL tiene 15 días de anticipación para informar cualquier inquietud a la
agencia (no estar conforme con el trabajo establecido, salir por motivos personales, etc.).</b></p>
<p class="aviso"><b>EN CASO DE ABANDONO DE TRABAJO NO TIENE RECLAMO A SUS DÍAS TRABAJADOS.</b></p>
<div class="firmas">
{firma('firma_agencia', 'EMPRESA', config.get('representante'))}
{firma('firma_cliente', 'EMPLEADOR', cli.get('nombre'))}
{firma('firma_trabajadora', 'PERSONA', t.get('nombre'))}
</div>
<p class="cierre">En {texto(config.get('ciudad'))}, DÍA {campo(f'{fecha.day:02d}', 'corto')}
MES {campo(f'{fecha.month:02d}', 'corto')} AÑO {campo(fecha.year, 'corto')}.</p>
{nota}
</section>"""
