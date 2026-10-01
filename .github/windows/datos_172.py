"""Datos ficticios creados con el propio código de Servitotal 1.7.2 (el que tiene instalado la agencia)."""
import json
import os
import sys

sys.path.insert(0, sys.argv[1])
import agencia  # noqa: E402

os.makedirs(agencia.CARPETA, exist_ok=True)
db = agencia.BaseDatos(agencia.DB_PATH)
try:
    ids = {
        "c30": db.insertar("clientes", {"nombre": "Clienta Ficticia Ñuñoa", "telefono": "900000001",
                                        "dias_garantia": "30"}),
        "c_sin": db.insertar("clientes", {"nombre": "Cliente Sin Plazo", "telefono": "900000002"}),
        "c60": db.insertar("clientes", {"nombre": "Cliente Dos Meses", "telefono": "900000003",
                                        "dias_garantia": "60"}),
        "t1": db.insertar("trabajadoras", {"nombre": "Trabajadora Ficticia Peña", "telefono": "900000004"}),
        "t2": db.insertar("trabajadoras", {"nombre": "Trabajadora Ficticia Dos", "telefono": "900000005"}),
    }
    ids["a45"] = db.insertar("colocaciones", {
        "cliente_id": str(ids["c30"]), "trabajadora_id": str(ids["t1"]), "estado": "Activa", "garantia": "Sí",
        "dias_garantia": "45", "comision": "300.00", "sueldo_acordado": "1200", "fecha_enlace": "01/09/2026",
        "fecha_contrato": "01/09/2026", "fecha_inicio": "01/09/2026", "contrato_firmado": "1",
        "contrato_html": "<html><body>Contrato firmado de Clienta Ficticia Ñuñoa</body></html>"})
    ids["a_no"] = db.insertar("colocaciones", {
        "cliente_id": str(ids["c60"]), "trabajadora_id": str(ids["t2"]), "estado": "Activa", "garantia": "No",
        "dias_garantia": "0", "comision": "200.00", "sueldo_acordado": "1000", "fecha_enlace": "02/09/2026"})
finally:
    db.con.close()
import sqlite3  # noqa: E402
con = sqlite3.connect(agencia.DB_PATH)
con.row_factory = sqlite3.Row
filas = {t: [dict(f) for f in con.execute(f"SELECT * FROM {t}")] for t in ("clientes", "colocaciones")}
con.close()
print(json.dumps({"version": getattr(agencia, "VERSION", "?"), "ids": ids,
                  "clientes": [{k: f.get(k) for k in ("id", "garantia", "dias_garantia", "meses_garantia")} for f in filas["clientes"]],
                  "colocaciones": [{k: f.get(k) for k in ("id", "garantia", "dias_garantia", "meses_garantia", "fin_garantia")} for f in filas["colocaciones"]]},
                 ensure_ascii=True, indent=1))
