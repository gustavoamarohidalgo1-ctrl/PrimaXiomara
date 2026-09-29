"""Verifica el contrato propio sin abrir Tk ni consultar una base de datos."""

import unittest
from html.parser import HTMLParser

from contratos_servitotal import ORDINALES, renderizar_hoja_servicio


class InspeccionHTML(HTMLParser):
    def __init__(self, documento):
        super().__init__()
        self.etiquetas = []
        self.textos = []
        self.feed(documento)

    def handle_starttag(self, tag, attrs):
        self.etiquetas.append(tag)

    def handle_data(self, data):
        self.textos.append(data)


class ContratoServitotalTests(unittest.TestCase):
    def setUp(self):
        self.c = {"id": 12, "garantia": "Sí", "fecha_enlace": "02/01/2026", "comision": "750.00",
                  "contrato_firmado": "1", "fecha_firma": "25/09/2026 18:30"}
        self.cli = {"nombre": "Empleador de prueba", "dni": "12345678", "ocupacion": "Docente",
                    "telefono": "987654321", "direccion": "Calle de prueba 123", "zona": "Ate"}
        self.t = {"nombre": "Trabajadora de prueba", "dni": "87654321"}
        self.datos = {"fecha_contrato": "29/09/2026"}
        self.argumentos = {
            "config": {
                "nombre": "Agencia de Empleos S.T Servitotal",
                "direccion": "Av. Nicolás Ayllón N° 5695, 2do piso, oficina 201, Carretera Central, distrito de Ate-Vitarte",
                "representante": "Xiomara Amaro Arellano", "dni": "76395760", "ciudad": "Lima",
            },
            "monto": "S/ 750.00", "sueldo": "S/ 1,500.00", "plazo": "treinta (30) días",
            "equivalencia": "cincuenta por ciento (50 %) del sueldo mensual pactado de S/ 1,500.00",
            "firmas": {"firma_cliente": '<span class="nombre-firma">Empleador de prueba</span>',
                       "firma_agencia": '<svg viewBox="0 0 330 150"><polyline points="0,0 1,1"/></svg>',
                       "firma_trabajadora": '<span class="nombre-firma">Trabajadora de prueba</span>'},
        }

    def renderizar(self, **argumentos):
        return renderizar_hoja_servicio(self.c, self.cli, self.t, self.datos,
                                       **{**self.argumentos, **argumentos})

    def test_identidad_clausulas_telefono_y_firmas_propias(self):
        documento = self.renderizar()
        for texto in ("AGENCIA DE EMPLEOS S.T SERVITOTAL", "oficina 201", "Xiomara Amaro Arellano",
                      "76395760", "987654321", "S/ 750.00", "cincuenta por ciento (50 %)",
                      "15 días de anticipación", "NO TIENE RECLAMO A SUS DÍAS TRABAJADOS"):
            self.assertIn(texto, documento)
        self.assertEqual(documento.count("<section"), 1)
        for ordinal in ORDINALES:
            self.assertEqual(documento.count(f"<b>{ordinal}:</b>"), 1)
        for contenido in self.argumentos["firmas"].values():
            self.assertIn(contenido, documento)
        for ajeno in ("10436157334", "Servicio Exclusivo", "oficina 304"):
            self.assertNotIn(ajeno, documento)

    def test_fecha_elegida_no_fecha_firma_ni_fecha_enlace(self):
        documento = self.renderizar()
        self.assertIn('DÍA <span class="campo corto">29</span>', documento)
        self.assertIn('MES <span class="campo corto">09</span>', documento)
        self.assertIn('AÑO <span class="campo corto">2026</span>', documento)

    def test_garantia_por_dias_meses_y_sin_garantia(self):
        self.assertIn("treinta (30) días contados desde el inicio del trabajo", self.renderizar())
        self.c.update(fecha_inicio="29/09/2026", fin_garantia="29/10/2026")
        self.assertIn("treinta (30) días (del 29/09/2026 al 29/10/2026)", self.renderizar())
        self.assertIn("dos (2) meses", self.renderizar(plazo="dos (2) meses"))
        self.c["garantia"] = "No"
        documento = self.renderizar()
        self.assertIn("<b>sin garantía</b>", documento)
        self.assertNotIn("con reemplazo sin costo", documento)
        self.assertIn("no está obligada a efectuar cambios", documento)
        self.assertNotIn("tendrá la facultad de solicitar el cambio", documento)
        self.assertNotIn("posibilidad de cambiarla por un nuevo personal", documento)

    def test_reemplazo_conserva_exencion_del_cobro(self):
        self.c["reemplazo_de"] = "7"
        self.datos["comision"] = "0.00"
        documento = self.renderizar(monto="S/ 0.00", equivalencia="")
        self.assertIn('N° <span class="campo corto">7</span>', documento)
        self.assertIn("no pagará monto adicional", documento)
        self.assertNotIn("pagará a <b>LA EMPRESA</b> la suma", documento)

    def test_reemplazo_con_cobro_explicito_no_imprime_exencion(self):
        self.c["reemplazo_de"] = "7"
        self.datos["comision"] = "150.00"
        documento = self.renderizar(monto="S/ 150.00", equivalencia="diez por ciento (10 %) del sueldo mensual")
        self.assertIn('la suma de <span class="campo medio">S/ 150.00</span>', documento)
        self.assertIn("diez por ciento (10 %)", documento)
        self.assertNotIn("no pagará monto adicional", documento)
        self.assertNotIn("Este cambio de personal sin costo", documento)

    def test_todos_los_datos_son_texto_incluidos_config_y_montos(self):
        ataque = '<script>alert("x")</script>&'
        self.c.update(id=ataque, fecha_inicio=ataque, fin_garantia=ataque, fecha_firma=ataque)
        self.cli = {clave: ataque for clave in self.cli}
        self.t = {clave: ataque for clave in self.t}
        config = {clave: ataque for clave in self.argumentos["config"]}
        documento = self.renderizar(config=config, monto=ataque, sueldo=ataque,
                                    plazo=ataque, equivalencia=ataque, firmas={})
        inspeccion = InspeccionHTML(documento)
        self.assertNotIn("script", inspeccion.etiquetas)
        self.assertIn(ataque, "".join(inspeccion.textos))
        self.assertIn("&lt;script&gt;", documento)
        self.assertIn("&quot;x&quot;", documento)


if __name__ == "__main__":
    unittest.main()
