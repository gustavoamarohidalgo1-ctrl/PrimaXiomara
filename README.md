# Agencia de Empleos S.T Servitotal

Aplicación de escritorio para registrar clientes y trabajadoras, gestionar áreas y asignaciones, preparar y firmar contratos, cobrar comisiones y administrar garantías. **Versión de distribución: 1.7.1.**

Conserva el logo propio de Servitotal y su tema oscuro con detalles rosa y fucsia. La comisión admite un importe o un porcentaje del sueldo: el 50 % es una propuesta inicial editable para cada contrato. La garantía inicial es de 30 días y permite acordar otros plazos en días o meses, o sin garantía.

## Descargar e instalar

Los instaladores incluyen Python; no hace falta instalarlo por separado.

| Equipo | Instalador |
| --- | --- |
| Windows 10 u 11 de 64 bits | [Servitotal-Windows-x64.exe](instaladores/Servitotal-Windows-x64.exe) |
| Mac con chip Apple Silicon, macOS 11.0 o posterior | [Servitotal-Mac-arm64.dmg](instaladores/Servitotal-Mac-arm64.dmg) |

En GitHub, abra el archivo correspondiente y use **Download raw file** para descargarlo. En Mac, abra el DMG y arrastre Servitotal a Aplicaciones. Consulte [LEEME.txt](LEEME.txt) para instalación y uso.

Las huellas de los dos paquetes están en [SHA256SUMS.txt](instaladores/SHA256SUMS.txt).

### Aviso «Windows protegió su PC»

El instalador actual no tiene firma Authenticode de editor. SmartScreen puede advertir que la aplicación es desconocida al evaluar su firma y reputación. Este aviso por sí solo no demuestra un fallo de la aplicación ni certifica la seguridad del archivo. [Explicación de Microsoft](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

Si descargó `Servitotal-Windows-x64.exe` de [este repositorio oficial](https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara) y confía en su procedencia:

1. En el aviso, pulse **Más información**.
2. Compruebe el nombre del archivo y pulse **Ejecutar de todas formas** para iniciar la instalación.

Son los pasos que documenta [Microsoft para aplicaciones nuevas](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/publish-first-app#step-6-handle-smartscreen-for-new-apps). No hace falta desactivar Microsoft Defender ni añadir una exclusión. Si falta ese botón o aparece una detección concreta de virus, conserve el texto del aviso para revisar ese caso antes de continuar.

## Ejecutar desde el código

Requiere Python con Tk 8.6 o posterior y SQLite. Se comprobó con Python 3.12 y 3.14. La aplicación utiliza la biblioteca estándar de Python.

```sh
python agencia.py --datos ./datos-locales
```

Mantenga [contratos_servitotal.py](contratos_servitotal.py) y los recursos gráficos junto a `agencia.py`. En Windows también puede usar [Iniciar.bat](Iniciar.bat). En Mac, [Crear_App_Mac.command](Crear_App_Mac.command) crea un lanzador junto al código; su requisito de macOS depende del Python instalado en ese equipo.

## Datos y actualizaciones

Cada cambio confirmado se guarda en SQLite. El programa mantiene copias locales y externas, permite elegir una carpeta adicional y conserva borradores de registros nuevos incompletos.

Los instaladores guardan la información en una carpeta separada:

- Windows: `%LOCALAPPDATA%\Servitotal`.
- Mac: `~/Library/Application Support/Servitotal`.

Guarde su trabajo y cierre la aplicación antes de actualizarla. La instalación normal conserva la carpeta de datos. Si utilizaba una versión con `agencia.db` junto al programa, conserve esa carpeta, cree un respaldo desde la aplicación original y restáurelo desde el panel de respaldos de la nueva instalación.

Este repositorio contiene únicamente el programa Servitotal y sus instaladores. Los registros reales de clientes y trabajadoras, contratos generados, respaldos, configuración y borradores permanecen fuera de Git. `.gitignore` utiliza una lista explícita de archivos permitidos.

## Pruebas

Las **307 pruebas de Servitotal** pasaron en copias independientes con Python 3.12, sin fallos ni pruebas omitidas. Las pruebas de la aplicación tampoco registraron errores de callbacks Python o Tcl. Usan registros ficticios y bases temporales; son independientes de otros proyectos. Con Python que incluya Tk y una sesión gráfica disponible:

```sh
python -m unittest discover -v
```

Las pruebas del constructor de Windows requieren `makensis`. Las pruebas de recreación del lanzador utilizan las herramientas de macOS.

Las mejoras de 1.7.1 incluyen comprobación de cambios simultáneos, conservación del ejemplar firmado, protección del importe ya cobrado, redondeo decimal y preparación verificada de copias y restauraciones. Los instaladores de Mac se probaron con arranques nuevos y actualización desde datos ficticios de 1.7.0. Los instaladores Windows se compilaron e inspeccionaron; su ejecución en un equipo Windows sigue pendiente.

## Construir instaladores

- [Crear_EXE.bat](Crear_EXE.bat): genera el portable `Servitotal.exe` desde Windows en un entorno temporal.
- [crear_instalador_windows.sh](instaladores/construccion/crear_instalador_windows.sh): construye el instalador Windows desde un Mac con las herramientas indicadas en el script.
- [crear_instalador_mac.sh](instaladores/construccion/crear_instalador_mac.sh): construye y verifica el DMG desde un Mac con Apple Silicon.
- [crear_iconos.sh](instaladores/construccion/crear_iconos.sh): convierte el logo propio a los formatos de icono desde macOS.

Los paquetes incluyen el código y los recursos gráficos de Servitotal; los datos operativos se mantienen separados.
