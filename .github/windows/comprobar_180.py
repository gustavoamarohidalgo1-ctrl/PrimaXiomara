"""Después de actualizar Servitotal 1.7.2 -> 1.8.0 y abrirlo: datos completos y garantías en meses."""
import glob
import os
import sqlite3
import sys

base, datos = sys.argv[1], sys.argv[2]
con = sqlite3.connect(base)
con.row_factory = sqlite3.Row
assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
clientes = {f["nombre"]: dict(f) for f in con.execute("SELECT * FROM clientes")}
colocaciones = {f["id"]: dict(f) for f in con.execute("SELECT * FROM colocaciones")}
assert len(clientes) == 3 and len(colocaciones) == 2, (len(clientes), len(colocaciones))
assert con.execute("SELECT COUNT(*) FROM trabajadoras").fetchone()[0] == 2
meses = {nombre: f["meses_garantia"] for nombre, f in clientes.items()}
assert meses == {"Clienta Ficticia Ñuñoa": "1 mes", "Cliente Sin Plazo": "1 mes", "Cliente Dos Meses": "2 meses"}, meses
assert colocaciones[1]["meses_garantia"] == "2", colocaciones[1]          # 45 días -> 2 meses
assert colocaciones[1]["dias_garantia"] == "45"                          # los días quedan guardados
assert colocaciones[2]["garantia"] == "No" and colocaciones[2]["meses_garantia"] in ("", "0"), colocaciones[2]
assert "Clienta Ficticia Ñuñoa" in colocaciones[1]["contrato_html"], "el contrato firmado no se conservó"
copias = glob.glob(os.path.join(datos, "respaldos", "agencia-antes-de-actualizar-*.db"))
assert len(copias) == 1, copias
v = sqlite3.connect(copias[0])
assert v.execute("SELECT meses_garantia FROM colocaciones WHERE id = 1").fetchone()[0] in ("", None), \
    "la copia previa no es la base de 1.7.2"
v.close()
print("Servitotal 1.7.2 -> 1.8.0: datos completos, garantías en meses y copia previa", os.path.basename(copias[0]))
