#!/bin/bash
# Convierte el logo original a formatos de icono sin cambiar su diseño ni sus colores.
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
[ "$(uname -s)" = "Darwin" ] || { echo "Esta conversion usa sips e iconutil de macOS."; exit 1; }

/usr/bin/python3 - "$RAIZ" <<'PYTHON'
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

raiz = Path(sys.argv[1])
logo = raiz / "logo.png"
if not logo.is_file():
    sys.exit("Falta logo.png en la carpeta de Servitotal.")

with tempfile.TemporaryDirectory(prefix="servitotal-iconos-") as temporal:
    temporal = Path(temporal)
    iconset = temporal / "Servitotal.iconset"
    iconset.mkdir()
    for tam in (16, 32, 128, 256, 512):
        for escala in (1, 2):
            destino = iconset / f"icon_{tam}x{tam}{'@2x' if escala == 2 else ''}.png"
            subprocess.run(["sips", "-z", str(tam * escala), str(tam * escala),
                            str(logo), "--out", str(destino)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(temporal / "icono.icns")], check=True)

    imagenes = []
    for tam in (16, 32, 48, 64, 128):
        png = temporal / f"{tam}.png"
        ico = temporal / f"{tam}.ico"
        subprocess.run(["sips", "-z", str(tam), str(tam), str(logo), "--out", str(png)],
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["sips", "-s", "format", "ico", str(png), "--out", str(ico)],
                       check=True, stdout=subprocess.DEVNULL)
        datos = ico.read_bytes()
        reservado, formato, cantidad = struct.unpack("<HHH", datos[:6])
        if reservado != 0 or formato != 1 or cantidad < 1:
            raise ValueError(f"ICO invalido generado para {tam} pixeles.")
        for n in range(cantidad):
            entrada = struct.unpack("<BBBBHHII", datos[6 + n * 16:22 + n * 16])
            imagenes.append((entrada[:6], datos[entrada[7]:entrada[7] + entrada[6]]))
    posicion = 6 + 16 * len(imagenes)
    tabla, cuerpo = bytearray(), bytearray()
    for atributos, imagen in imagenes:
        tabla.extend(struct.pack("<BBBBHHII", *atributos, len(imagen), posicion + len(cuerpo)))
        cuerpo.extend(imagen)
    (temporal / "icono.ico").write_bytes(struct.pack("<HHH", 0, 1, len(imagenes)) + tabla + cuerpo)
    shutil.copy2(logo, raiz / "icono.png")
    for nombre in ("icono.ico", "icono.icns"):
        shutil.copy2(temporal / nombre, raiz / nombre)
print("Listo: icono.png, icono.ico e icono.icns conservan el logo original de Servitotal.")
PYTHON
