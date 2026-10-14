"""Datos ficticios escritos por el propio Servitotal 1.8.0 (sin avisos), para probar la actualización a la versión
nueva. Guarda en el JSON indicado cómo quedaron sus tablas, para comprobar después que no cambió nada."""
import json
import os
import sqlite3
import sys

sys.path.insert(0, sys.argv[1])
import agencia  # noqa: E402

os.makedirs(agencia.CARPETA, exist_ok=True)
db = agencia.BaseDatos(agencia.DB_PATH)
try:
    cliente = db.insertar("clientes", {"nombre": "Clienta Ficticia Ñuñoa", "telefono": "900000001",
                                       "meses_garantia": "2 meses"})
    trabajadora = db.insertar("trabajadoras", {"nombre": "Trabajadora Ficticia Peña", "telefono": "900000002"})
    db.insertar("colocaciones", {
        "cliente_id": str(cliente), "trabajadora_id": str(trabajadora), "estado": "Activa", "garantia": "Sí",
        "meses_garantia": "2", "comision": "300.00", "comision_pagada": "1", "fecha_pago": "01/10/2026",
        "sueldo_acordado": "1200", "fecha_enlace": "01/10/2026", "contrato_firmado": "1",
        "contrato_html": "<html><body>Contrato firmado de Clienta Ficticia Ñuñoa</body></html>"})
finally:
    db.con.close()
con = sqlite3.connect(agencia.DB_PATH)
con.row_factory = sqlite3.Row
tablas = {t: [dict(f) for f in con.execute(f"SELECT * FROM {t} ORDER BY id")]
          for t in ("clientes", "trabajadoras", "colocaciones", "areas")}
tiene_avisos = bool(con.execute("SELECT 1 FROM sqlite_master WHERE name = 'avisos'").fetchone())
con.close()
with open(sys.argv[2], "w", encoding="utf-8") as archivo:
    json.dump(tablas, archivo, ensure_ascii=False)
print("Servitotal", agencia.VERSION, "con datos ficticios; tabla avisos:", tiene_avisos)
if tiene_avisos:
    sys.exit("La versión anterior ya tenía avisos: esta prueba no compara lo que debe")
