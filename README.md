# Agencia de Empleos S.T Servitotal

Aplicación de escritorio para registrar clientes y trabajadoras, gestionar áreas y asignaciones, preparar y firmar contratos, cobrar comisiones y administrar garantías. **Versiones de distribución: Windows 1.8.0 · Mac 1.7.1.**

## El mismo programa que Servicio Exclusivo

Servitotal usa el mismo programa que Servicio Exclusivo: [igualar_con_tia.py](instaladores/construccion/igualar_con_tia.py) genera `agencia.py` y sus pruebas a partir de los de Servicio Exclusivo. Solo cambian los colores (tema oscuro con detalles rosa y fucsia, también en el contrato, en Word y en PDF), el logo y los datos propios:

- el nombre Servitotal, la carpeta de datos `Servitotal` y las copias en `Documentos\Respaldos Servitotal`; la carpeta adicional de copias lleva la marca `.copias-servitotal`, así los datos nunca se mezclan con los de otra agencia;
- el contrato de Servicio Exclusivo a nombre de la agencia «S.T Servitotal», con su domicilio y su representante, Xiomara Amaro Arellano (sin RUC);
- la comisión sin propuesta: en cada contrato se escribe el porcentaje del sueldo (o el pago único);
- la garantía en meses, como en Servicio Exclusivo: por defecto 2; 0 = sin garantía.

Al abrir la 1.8.0 por primera vez, después de una copia de seguridad, las garantías guardadas en días pasan a meses (30 días = 1 mes, redondeando hacia arriba), sin tocar los contratos firmados ni las fechas de fin ya calculadas. Lo que se escribió en la entrevista y en «Sueldo que pide» ya no aparece en la ficha, pero se conserva en la base y en las copias .csv.

Los cambios del programa se hacen en Servicio Exclusivo y se traen con `python instaladores/construccion/igualar_con_tia.py CARPETA_DE_SERVICIO_EXCLUSIVO CARPETA_DE_SERVITOTAL`. Los datos y colores de Servitotal se cambian en ese script, no en `agencia.py`: lo que se cambie solo en `agencia.py` se pierde al volver a igualar.

## Descargar e instalar

Los paquetes incluyen Python; no hace falta instalarlo por separado.

| Equipo | Paquete |
| --- | --- |
| Windows 10 u 11 de 64 bits, **recomendado** | [Servitotal-1.8.0-Windows-portable.zip](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/raw/refs/heads/main/instaladores/Servitotal-1.8.0-Windows-portable.zip) |
| Windows 10 u 11 de 64 bits, con instalador | [Servitotal-Windows-x64.exe](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/raw/refs/heads/main/instaladores/Servitotal-Windows-x64.exe) |
| Mac con chip Apple Silicon, macOS 11.0 o posterior | [Servitotal-Mac-arm64.dmg](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/raw/refs/heads/main/instaladores/Servitotal-Mac-arm64.dmg) |

Los enlaces descargan el archivo directamente. En Mac, abra el DMG y arrastre Servitotal a Aplicaciones. Consulte [LEEME.txt](LEEME.txt) para instalación y uso. Las huellas de los paquetes están en [SHA256SUMS.txt](instaladores/SHA256SUMS.txt).

### Windows: ZIP sin instalar (recomendado)

1. Descargue el ZIP. Si Edge avisa que el archivo no se descarga habitualmente, use **⋯ → Conservar**.
2. Antes de extraerlo: **clic derecho sobre el ZIP → Propiedades**, marque **Desbloquear** si aparece y pulse **Aceptar**.
3. **Clic derecho → Extraer todo**. Puede extraerlo en Documentos.
4. Abra la carpeta `Servitotal-1.8.0` y haga doble clic en **Servitotal.exe**.

`Servitotal.exe` es el Python oficial (`pythonw.exe`, firmado por Python Software Foundation) con otro nombre: sus bytes y su firma no cambian, y un archivo `python312._pth` hace que sólo use las carpetas del ZIP. El paquete no tiene `.bat` ni ejecutables propios sin firma: Windows ve la firma de Python Software Foundation en lugar de un programa desconocido. Para tenerlo a mano: clic derecho en `Servitotal.exe` → **Enviar a → Escritorio (crear acceso directo)**.

Los datos se guardan en `%LOCALAPPDATA%\Servitotal`, igual que con el instalador. Conserve completa la carpeta extraída. Si no abre, **Diagnosticar Servitotal.exe** muestra el error en una ventana; los fallos de inicio también quedan en `%LOCALAPPDATA%\Servitotal\errores_inicio.log`.

### Datos de la versión anterior

La versión anterior guardaba `agencia.db` junto al programa. La primera vez que Servitotal instalado se abre sin datos en Windows, busca ese archivo en el Escritorio, Documentos, Descargas, OneDrive, la carpeta personal y las carpetas de primer nivel del disco del sistema, y pregunta si desea traerlo. El aviso muestra la carpeta, las cantidades y la fecha del último cambio, para que reconozca sus datos. Al aceptar, guarda antes una copia de lo que tenga, copia y actualiza los datos y, si aquí no hay una, trae también la carpeta adicional de copias que usaba; el archivo original no se modifica. Si responde No, no vuelve a preguntar por ese archivo.

Si en el equipo también está el programa de otra agencia (por ejemplo, Servicio Exclusivo), su `agencia.db` no se ofrece: el programa la reconoce por el `agencia.py` que la acompaña. Si además hay una copia de seguridad, se ofrece la más reciente de las dos.

Con el ZIP portable o el de Python oficial, o si no lo encuentra, pulse **Ctrl+Shift+B → Traer datos de otro archivo…** y elija el `agencia.db` de la carpeta anterior. El programa guarda antes una copia de lo que tenga y el original no se modifica. Cierre el programa anterior antes de traer sus datos.

### Windows: instalador

El instalador no tiene firma Authenticode de editor. Instala sólo para el usuario actual, sin pedir administrador, en `%LOCALAPPDATA%\Programs\Servitotal`. Si lo recibe por **WhatsApp**, no lo abra desde dentro de WhatsApp (la aplicación de Windows no ejecuta archivos `.exe` y no muestra nada): guárdelo en **Descargas** y ábralo desde allí con doble clic.

- **«Windows protegió su PC» (SmartScreen):** si descargó el archivo de [este repositorio oficial](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara) y confía en su procedencia, pulse **Más información** y **Ejecutar de todas formas**. Son los pasos que documenta [Microsoft para aplicaciones nuevas](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/publish-first-app#step-6-handle-smartscreen-for-new-apps).
- **«Control inteligente de aplicaciones bloqueó…»:** ese aviso de Windows 11 no ofrece continuar para programas sin firma. Use el ZIP recomendado. No hace falta desactivar ninguna protección.

Para actualizar, abra el instalador nuevo: la instalación conserva la carpeta de datos. Si Servitotal está abierto, el instalador pide cerrarlo y pulsar Reintentar, sin cambiar nada mientras tanto. Si el antivirus revisa los archivos nuevos, el instalador reintenta durante unos segundos antes de rendirse, y en ese caso recupera la instalación anterior. Si el programa no llegara a abrir, el motivo queda en `errores_inicio.log`, dentro de la carpeta de datos (menú Inicio → Servitotal → Datos de la agencia).

En **Propiedades**, el instalador 1.8.0 completo ocupa **11.830.956 bytes**. Si Windows detecta una amenaza concreta, conserve el texto de **Seguridad de Windows → Protección contra virus y amenazas → Historial de protección** para revisarlo.

### Windows: Python oficial instalado por separado

Como alternativa, [descargue el paquete de código de Servitotal](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/raw/refs/heads/main/instaladores/Servitotal-1.8.0-Windows-Python.zip) e instale **Python 3.14.7 completo de 64 bits** desde [python.org](https://www.python.org/downloads/release/python-3147/). Elija «Windows installer (64-bit)» y mantenga «tcl/tk and IDLE», el lanzador de Python y la asociación de archivos. No use el Python de Microsoft Store: guarda los datos en una carpeta privada, y Servitotal avisa si se abre con él.

Extraiga todo el ZIP y abra **Abrir Servitotal.pyw**. Este acceso utiliza `%LOCALAPPDATA%\Servitotal`, igual que el instalador. **Diagnosticar Servitotal.py** muestra los errores en consola.

## Ejecutar desde el código

Requiere Python con Tk 8.6 o posterior y SQLite. Se comprobó con Python 3.12 y 3.14. La aplicación utiliza la biblioteca estándar de Python.

```sh
python agencia.py --datos ./datos-locales
```

En Windows también puede usar [Iniciar.bat](Iniciar.bat), que avisa en pantalla si falta `agencia.py` o si Python es demasiado antiguo. Sin `--datos`, el programa guarda los datos junto a `agencia.py`, como la versión anterior, y los fallos quedan en `errores.log`. En Mac, [Crear_App_Mac.command](Crear_App_Mac.command) crea un lanzador junto al código; su requisito de macOS depende del Python instalado en ese equipo.

## Datos y actualizaciones

Cada cambio confirmado se guarda en SQLite. El programa mantiene copias locales y externas, permite elegir una carpeta adicional y conserva borradores de registros nuevos incompletos.

Los paquetes guardan la información en una carpeta separada:

- Windows: `%LOCALAPPDATA%\Servitotal`.
- Mac: `~/Library/Application Support/Servitotal`.

Las copias externas van a `Documentos\Respaldos Servitotal`, y la carpeta adicional que se elija (un USB, OneDrive…) se marca con `.copias-servitotal`.

Guarde su trabajo y cierre la aplicación antes de actualizarla. La instalación normal conserva la carpeta de datos. Para los datos de la versión anterior, vea [Datos de la versión anterior](#datos-de-la-versión-anterior).

Este repositorio contiene únicamente el programa Servitotal y sus instaladores. Los registros reales de clientes y trabajadoras, documentos de clientes, contratos generados, respaldos, configuración y borradores permanecen fuera de Git. `.gitignore` utiliza una lista explícita de archivos permitidos.

## Pruebas

Las **389 pruebas** pasan en macOS con Python 3.12 (se omiten 4 que son solo de Windows), salvo las 4 que comprueban que los paquetes de `instaladores/` lleven este mismo código: fallan hasta que se vuelvan a generar. Son las pruebas de Servicio Exclusivo, que `igualar_con_tia.py` copia con los datos de Servitotal, más dos propias:

- [test_servitotal.py](test_servitotal.py): lo propio de Servitotal (nombre, carpeta, colores, contrato, comisión sin propuesta, garantías en días, columnas conservadas y la base de otra agencia). También comprueba que `agencia.py` sea el de Servicio Exclusivo con solo esa capa; esa prueba se omite si el programa de Servicio Exclusivo no está en la carpeta de arriba.
- [test_instaladores_fiabilidad.py](test_instaladores_fiabilidad.py): los paquetes de Servitotal.

Usan registros ficticios y bases temporales, y nunca la carpeta de datos real aunque se ejecuten desde el proyecto. [test_windows.py](test_windows.py) cubre comportamientos propios de Windows (archivos retenidos por el antivirus, CSV abiertos en Excel, rutas de red, datos de la versión anterior); las marcadas «solo Windows» se omiten en otros sistemas. Con Python que incluya Tk y una sesión gráfica disponible:

```sh
python -m unittest discover -v
```

Las pruebas del constructor de Windows requieren `makensis`; las del lanzador de Mac, macOS.

### Pruebas en Windows

Cuatro flujos de GitHub Actions, que se lanzan a mano, comprueban Servitotal en Windows Server 2022 y 2025:

- [windows-pruebas.yml](.github/workflows/windows-pruebas.yml): todas las pruebas con Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13 y 3.14 de 64 bits.
- [windows-smoke.yml](.github/workflows/windows-smoke.yml): el instalador, con la protección en tiempo real de Microsoft Defender activada.
- [windows-python.yml](.github/workflows/windows-python.yml): el paquete de código con Python oficial.
- [windows-completo.yml](.github/workflows/windows-completo.yml): las mismas pruebas que pasa el instalador de Servicio Exclusivo (asistente con clics y en silencio, recorrido completo con impresión en Word y PDF, ocho actualizaciones seguidas con el antivirus encendido, cuentas estándar con tildes, pantallas al 100 %, 125 % y 150 %, EXE de Crear_EXE.bat y doble clic con SmartScreen), más la actualización desde la 1.7.2 publicada con garantías en días.

Con el código anterior, las 346 pruebas de entonces pasaron en [Windows Server 2022 y 2025](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/actions/runs/36737030968) con todas esas versiones de Python y con el mismo Python incluido en el instalador. El programa igualado con Servicio Exclusivo todavía no se ejecutó en Windows: falta lanzar esos flujos.

Los paquetes 1.7.2 se comprobaron de principio a fin en [Windows Server 2022 y 2025](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/actions/runs/36737794724), con carpetas que contienen espacios y «ñ». En cada apertura, la prueba cierra el programa con el botón de la ventana, como lo haría la usuaria.

- **Instalador:**
  - Se instaló sobre la versión 1.7.1 publicada, pulsando Siguiente, Instalar y Terminar en el asistente; el programa se abrió solo, al frente de las demás ventanas.
  - Microsoft Defender actualizado no detectó nada en el instalador, en lo instalado ni en el ZIP.
  - Con la versión anterior abierta, avisó y ofreció Reintentar; tras cerrarla, la instalación terminó bien.
  - Con la protección en tiempo real de Microsoft Defender activada.
  - Abrió el programa con el mismo acceso directo del Escritorio.
  - Trajo una base ficticia de la versión anterior respondiendo «Sí» a su aviso.
  - Abrió con variables de otro Python (`PYTHONHOME`, `PYTHONPATH`, `TCL_LIBRARY`).
  - Se desinstaló conservando los datos.
- **ZIP portable:** verificó la firma de Python Software Foundation en `Servitotal.exe` y repitió la apertura, los datos anteriores, el entorno ajeno y el diagnóstico.
- **Python oficial:** la [prueba con Python oficial](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/actions/runs/36737036079) instaló Python 3.14.7 desde python.org y abrió dos veces el paquete de código.

Ninguna de estas pruebas reproduce SmartScreen, el Control inteligente de aplicaciones ni el antivirus del equipo de una usuaria. Los scripts [verificar_windows.py](instaladores/construccion/verificar_windows.py) y [verificar_portable_windows.py](instaladores/construccion/verificar_portable_windows.py) modifican accesos, registro y Escritorio del usuario de prueba; están destinados a un Windows de pruebas efímero.

## Cambios de 1.8.0

- Servitotal usa el mismo programa que Servicio Exclusivo, con sus colores y sus datos (vea [El mismo programa que Servicio Exclusivo](#el-mismo-programa-que-servicio-exclusivo)): el contrato de Servicio Exclusivo a nombre de «S.T Servitotal», la garantía en meses y la comisión que se escribe en cada contrato.
- «Imprimir» pregunta si el contrato se abre en Word (.docx) o en PDF (en el navegador). Ambos se generan solo con la biblioteca estándar, a partir del mismo documento que se firma, con los colores del contrato de Servitotal; si el equipo no tiene Word, esa opción aparece desactivada.
- El contrato ya no se imprime solo. Hasta la 1.7.2 la página guardada lanzaba la impresión al cargarse: cada clic en «Imprimir» y cada pestaña restaurada o recargada por el navegador sacaba otra copia. Al arrancar, el programa quita esa impresión automática de los contratos `.html` que dejaron versiones anteriores, y tras abrir el contrato la pantalla dice dónde se abrió.
- Las firmas con nombre se achican según el largo del nombre y pueden pasar a otro renglón: ya no se salen de la hoja (ni hacen que el navegador achique toda la página), tampoco en contratos firmados antes (también los de Servitotal con tres firmas por renglón).
- «Contratos» está en el menú lateral, debajo de Áreas, con las pestañas Por firmar y Firmados y todas sus acciones (firmar, imprimir, datos del contrato, registrar inicio, deshacer). Ya no hay botón «Ver asignaciones»: al confirmar una asignación se abre Contratos con ella elegida. En pantallas bajas (1366×768) las opciones del menú se acercan para que entren todas.
- Fichas más cortas: la de la trabajadora ya no tiene la sección «Estado» (estado y notas) y la del cliente ya no pide «¿Para cuándo la necesita?» ni «Notas». El estado de la trabajadora lo pone el programa según sus asignaciones y se sigue viendo en la lista. Lo ya escrito en esos campos se conserva en la base y en las copias .csv, y una base nueva mantiene las mismas columnas. Una trabajadora que estuviera «No disponible» (solo se podía poner a mano) pasa al estado de sus asignaciones, para que no quede fuera de las listas sin forma de volver.
- Un sueldo escrito «1.500» se entiende como mil quinientos.
- Si una ficha ya guardada tiene un dato inválido, al salir se dice cuál y se ofrece volver a lo guardado.
- La carpeta adicional de copias solo se usa si es la elegida (lleva la marca `.copias-servitotal`): no se escriben datos en otro USB que tome su letra, y uno desconectado no avisa en cada arranque. Al traer los datos de la versión anterior también se trae esa carpeta.
- La versión se ve en el menú lateral y en `errores.log`.
- Instalador de Windows sin complementos (plugins), como el de Servicio Exclusivo: comprueba si Servitotal está abierto intentando abrir para escritura los archivos que el programa tiene cargados, en vez de Restart Manager, y comprueba Windows de 64 bits sin cargar nada antes de mostrar su ventana.
- Al pulsar «Instalar», Siguiente, Atrás y Cancelar quedan desactivados mientras se comprueba si Servitotal está abierto y mientras se ve el aviso «Reintentar». Antes, un segundo clic durante esa espera se atendía por debajo del aviso y la instalación empezaba dos veces a la vez (en Windows real terminaba con «Error abriendo archivo para escritura»).
- Abierto desde «Terminar» del instalador, Servitotal vuelve a mostrarse al frente de las demás ventanas, como en la 1.7.2 (es lo único que el programa tiene además del de Servicio Exclusivo, y no cambia nada en pantalla).
- Instalador de Windows: un archivo que no se pudo escribir ya no se puede «Omitir», un instalador más viejo advierte antes de reemplazar uno más nuevo y el desinstalador aclara que las copias de Documentos y de la carpeta adicional no se borran.
- Las pruebas nunca usan la carpeta de datos real, aunque se ejecuten desde esta carpeta. Las cuatro que comprueban que los paquetes de `instaladores/` lleven este mismo código fallan hasta que se vuelvan a generar.

## Construir instaladores

Si cambió el programa de Servicio Exclusivo, ejecute primero [igualar_con_tia.py](instaladores/construccion/igualar_con_tia.py); después vuelva a generar los paquetes.

- [crear_instalador_windows.sh](instaladores/construccion/crear_instalador_windows.sh): construye el instalador Windows desde un Mac con las herramientas indicadas en el script. Se detiene si el Python incluido tiene algún binario sin firma.
- [crear_portable_windows.py](instaladores/construccion/crear_portable_windows.py): crea el ZIP portable a partir de ese instalador. Necesita 7-Zip (`7zz` o `7z`).
- [crear_paquete_python.py](instaladores/construccion/crear_paquete_python.py): crea el ZIP de código para Python oficial.
- [crear_instalador_mac.sh](instaladores/construccion/crear_instalador_mac.sh): construye y verifica el DMG desde un Mac con Apple Silicon.
- [crear_iconos.sh](instaladores/construccion/crear_iconos.sh): convierte el logo propio a los formatos de icono desde macOS.
- [Crear_EXE.bat](Crear_EXE.bat): genera un `Servitotal.exe` con PyInstaller desde Windows. El nombre cambió respecto de `Agencia.exe` de la versión anterior.

Los paquetes incluyen el código y los recursos gráficos de Servitotal; los datos operativos se mantienen separados.
