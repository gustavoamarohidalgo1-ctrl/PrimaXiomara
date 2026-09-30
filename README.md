# Agencia de Empleos S.T Servitotal

Aplicación de escritorio para registrar clientes y trabajadoras, gestionar áreas y asignaciones, preparar y firmar contratos, cobrar comisiones y administrar garantías. **Versión de distribución para Windows: 1.7.2.** El paquete de Mac sigue en 1.7.1.

Conserva el logo propio de Servitotal y su tema oscuro con detalles rosa y fucsia. La comisión admite un importe o un porcentaje del sueldo: el 50 % es una propuesta inicial editable para cada contrato. La garantía inicial es de 30 días y permite acordar otros plazos en días o meses, o sin garantía.

## Descargar e instalar

Los paquetes incluyen Python; no hace falta instalarlo por separado.

| Equipo | Paquete |
| --- | --- |
| Windows 10 u 11 de 64 bits, **recomendado** | [Servitotal-1.7.2-Windows-portable.zip](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/raw/refs/heads/main/instaladores/Servitotal-1.7.2-Windows-portable.zip) |
| Windows 10 u 11 de 64 bits, con instalador | [Servitotal-Windows-x64.exe](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/raw/refs/heads/main/instaladores/Servitotal-Windows-x64.exe) |
| Mac con chip Apple Silicon, macOS 11.0 o posterior | [Servitotal-Mac-arm64.dmg](instaladores/Servitotal-Mac-arm64.dmg) |

Los enlaces descargan el archivo directamente. En Mac, abra el DMG y arrastre Servitotal a Aplicaciones. Consulte [LEEME.txt](LEEME.txt) para instalación y uso. Las huellas de los paquetes están en [SHA256SUMS.txt](instaladores/SHA256SUMS.txt).

### Windows: ZIP sin instalar (recomendado)

1. Descargue el ZIP. Si Edge avisa que el archivo no se descarga habitualmente, use **⋯ → Conservar**.
2. Antes de extraerlo: **clic derecho sobre el ZIP → Propiedades**, marque **Desbloquear** si aparece y pulse **Aceptar**.
3. **Clic derecho → Extraer todo**. Puede extraerlo en Documentos.
4. Abra la carpeta `Servitotal-1.7.2` y haga doble clic en **Servitotal.exe**.

`Servitotal.exe` es el Python oficial (`pythonw.exe`, firmado por Python Software Foundation) con otro nombre: sus bytes y su firma no cambian, y un archivo `python312._pth` hace que sólo use las carpetas del ZIP. El paquete no tiene `.bat` ni ejecutables propios sin firma: Windows ve la firma de Python Software Foundation en lugar de un programa desconocido. Para tenerlo a mano: clic derecho en `Servitotal.exe` → **Enviar a → Escritorio (crear acceso directo)**.

Los datos se guardan en `%LOCALAPPDATA%\Servitotal`, igual que con el instalador. Conserve completa la carpeta extraída. Si no abre, **Diagnosticar Servitotal.exe** muestra el error en una ventana; los fallos de inicio también quedan en `%LOCALAPPDATA%\Servitotal\errores_inicio.log`.

### Datos de la versión anterior

La versión anterior guardaba `agencia.db` junto al programa. La primera vez que Servitotal 1.7.2 se abre sin datos, busca ese archivo en el Escritorio, Documentos y Descargas (también en OneDrive) y pregunta si desea traerlo. Al aceptar, copia y actualiza los datos; el archivo original no se modifica.

Si no lo encuentra, pulse **Ctrl+Shift+B → Traer datos de otra carpeta…** y elija el `agencia.db` de la carpeta anterior. El programa guarda antes una copia de lo que tenga. Cierre el programa anterior antes de traer sus datos.

### Windows: instalador

El instalador no tiene firma Authenticode de editor. Instala sólo para el usuario actual, sin pedir administrador, en `%LOCALAPPDATA%\Programs\Servitotal`.

- **«Windows protegió su PC» (SmartScreen):** si descargó el archivo de [este repositorio oficial](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara) y confía en su procedencia, pulse **Más información** y **Ejecutar de todas formas**. Son los pasos que documenta [Microsoft para aplicaciones nuevas](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/publish-first-app#step-6-handle-smartscreen-for-new-apps).
- **«Control inteligente de aplicaciones bloqueó…»:** ese aviso de Windows 11 no ofrece continuar para programas sin firma. Use el ZIP recomendado. No hace falta desactivar ninguna protección.

Para actualizar, cierre Servitotal y abra el instalador nuevo: la instalación conserva la carpeta de datos. Si el programa está abierto, el instalador se detiene sin cambiar nada. Si el antivirus revisa los archivos nuevos, el instalador reintenta durante unos segundos antes de rendirse, y en ese caso recupera la instalación anterior.

En **Propiedades**, el instalador 1.7.2 completo ocupa **{{BYTES_EXE}} bytes**. Si Windows detecta una amenaza concreta, conserve el texto de **Seguridad de Windows → Protección contra virus y amenazas → Historial de protección** para revisarlo.

### Windows: Python oficial instalado por separado

Como alternativa, [descargue el paquete de código de Servitotal](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/raw/refs/heads/main/instaladores/Servitotal-1.7.2-Windows-Python.zip) e instale **Python 3.14.7 completo de 64 bits** desde [python.org](https://www.python.org/downloads/release/python-3147/). Elija «Windows installer (64-bit)» y mantenga «tcl/tk and IDLE», el lanzador de Python y la asociación de archivos. No use el Python de Microsoft Store: guarda los datos en una carpeta privada, y Servitotal avisa si se abre con él.

Extraiga todo el ZIP y abra **Abrir Servitotal.pyw**. Este acceso utiliza `%LOCALAPPDATA%\Servitotal`, igual que el instalador. **Diagnosticar Servitotal.py** muestra los errores en consola.

## Ejecutar desde el código

Requiere Python 3.8 o posterior con Tk 8.6 o posterior y SQLite. Se comprobó en Windows con Python 3.8 a 3.14. La aplicación utiliza la biblioteca estándar de Python.

```sh
python agencia.py --datos ./datos-locales
```

Copie **todos** los archivos juntos: `agencia.py` necesita [contratos_servitotal.py](contratos_servitotal.py) y los recursos gráficos. Si falta un archivo o Python es demasiado antiguo, [Iniciar.bat](Iniciar.bat) y el propio programa lo avisan en pantalla, y los fallos de inicio quedan en `errores.log`. Ejecutado desde el código, el programa guarda los datos junto a `agencia.py`, como la versión anterior. En Mac, [Crear_App_Mac.command](Crear_App_Mac.command) crea un lanzador junto al código; su requisito de macOS depende del Python instalado en ese equipo.

## Datos y actualizaciones

Cada cambio confirmado se guarda en SQLite. El programa mantiene copias locales y externas, permite elegir una carpeta adicional y conserva borradores de registros nuevos incompletos.

Los paquetes guardan la información en una carpeta separada:

- Windows: `%LOCALAPPDATA%\Servitotal`.
- Mac: `~/Library/Application Support/Servitotal`.

Guarde su trabajo y cierre la aplicación antes de actualizarla. La instalación normal conserva la carpeta de datos. Para los datos de la versión anterior, vea [Datos de la versión anterior](#datos-de-la-versión-anterior).

Este repositorio contiene únicamente el programa Servitotal y sus instaladores. Los registros reales de clientes y trabajadoras, contratos generados, respaldos, configuración y borradores permanecen fuera de Git. `.gitignore` utiliza una lista explícita de archivos permitidos.

## Pruebas

Las **{{PRUEBAS}} pruebas de Servitotal** pasan en macOS con Python 3.12 y en [Windows Server 2022 y 2025]({{RUN_PRUEBAS}}) con Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13 y 3.14 de 64 bits y con el mismo Python incluido en el instalador. Usan registros ficticios y bases temporales. Con Python que incluya Tk y una sesión gráfica disponible:

```sh
python -m unittest discover -v
```

Las pruebas del constructor de Windows requieren `makensis`; las del lanzador de Mac, macOS.

Los paquetes 1.7.2 se comprobaron de principio a fin en [Windows Server 2022 y 2025]({{RUN_WINDOWS}}), con carpetas que contienen espacios y «ñ». En cada apertura, la prueba cierra el programa con el botón de la ventana, como lo haría la usuaria.

- **Instalador:**
  - Se instaló sobre la versión 1.7.1 publicada.
  - Se negó a actualizar mientras la versión anterior estaba abierta, sin tocar nada.
  - Abrió el programa con el mismo acceso directo del Escritorio.
  - Trajo una base ficticia de la versión anterior respondiendo «Sí» a su aviso.
  - Abrió con variables de otro Python (`PYTHONHOME`, `PYTHONPATH`, `TCL_LIBRARY`).
  - Se desinstaló conservando los datos.
- **ZIP portable:** verificó la firma de Python Software Foundation en `Servitotal.exe` y repitió la apertura, los datos anteriores, el entorno ajeno y el diagnóstico.
- **Python oficial:** la [prueba con Python oficial]({{RUN_PYTHON}}) instaló Python 3.14.7 desde python.org y abrió dos veces el paquete de código.

Ninguna de estas pruebas reproduce SmartScreen, el Control inteligente de aplicaciones ni el antivirus del equipo de una usuaria. Los scripts [verificar_windows.py](instaladores/construccion/verificar_windows.py) y [verificar_portable_windows.py](instaladores/construccion/verificar_portable_windows.py) modifican accesos, registro y Escritorio del usuario de prueba; están destinados a un Windows de pruebas efímero.

## Construir instaladores

- [crear_instalador_windows.sh](instaladores/construccion/crear_instalador_windows.sh): construye el instalador Windows desde un Mac con las herramientas indicadas en el script. Se detiene si el Python incluido tiene algún binario sin firma.
- [crear_portable_windows.py](instaladores/construccion/crear_portable_windows.py): crea el ZIP portable a partir de ese instalador. Necesita 7-Zip (`7zz` o `7z`).
- [crear_paquete_python.py](instaladores/construccion/crear_paquete_python.py): crea el ZIP de código para Python oficial.
- [crear_instalador_mac.sh](instaladores/construccion/crear_instalador_mac.sh): construye y verifica el DMG desde un Mac con Apple Silicon.
- [crear_iconos.sh](instaladores/construccion/crear_iconos.sh): convierte el logo propio a los formatos de icono desde macOS.
- [Crear_EXE.bat](Crear_EXE.bat): genera un `Servitotal.exe` con PyInstaller desde Windows. El nombre cambió respecto de `Agencia.exe` de la versión anterior.

Los paquetes incluyen el código y los recursos gráficos de Servitotal; los datos operativos se mantienen separados.
