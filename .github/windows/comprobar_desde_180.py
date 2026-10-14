"""Después de actualizar Servitotal 1.8.0 a la versión con avisos y abrirlo: la tabla de avisos existe, lo anterior
quedó igual (fila por fila) y antes se guardó una copia de la base de 1.8.0."""
import glob
import json
import os
import sqlite3
import sys

base, datos, antes = sys.argv[1], sys.argv[2], sys.argv[3]
with open(antes, encoding="utf-8") as archivo:
    esperado = json.load(archivo)
con = sqlite3.connect(base)
con.row_factory = sqlite3.Row
assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
columnas = {f[1] for f in con.execute("PRAGMA table_info(avisos)")}
assert {"fecha", "detalle", "monto", "registrado"} <= columnas, columnas
assert con.execute("SELECT count(*) FROM avisos").fetchone()[0] == 0
for tabla, filas in esperado.items():
    ahora = [dict(f) for f in con.execute(f"SELECT * FROM {tabla} ORDER BY id")]
    assert len(ahora) == len(filas), (tabla, len(ahora), len(filas))
    for nueva, vieja in zip(ahora, filas):
        assert {k: nueva.get(k) for k in vieja} == vieja, (tabla, vieja.get("id"))
con.close()
copias = glob.glob(os.path.join(datos, "respaldos", "agencia-antes-de-actualizar-*.db"))
assert len(copias) == 1, copias
copia = sqlite3.connect(copias[0])
copia.row_factory = sqlite3.Row
assert not copia.execute("SELECT 1 FROM sqlite_master WHERE name = 'avisos'").fetchone(), "la copia no es la de 1.8.0"
for tabla, filas in esperado.items():          # la copia previa tiene exactamente los datos de antes
    assert [dict(f) for f in copia.execute(f"SELECT * FROM {tabla} ORDER BY id")] == filas, ("copia previa", tabla)
copia.close()
print("Servitotal 1.8.0 -> version nueva: avisos listos, datos intactos y copia previa", os.path.basename(copias[0]))
