; Protecciones nativas antes de tocar archivos de una instalación, sin complementos (plugins): sólo instrucciones
; de NSIS, como el instalador de Servicio Exclusivo. Nunca cierra procesos ni programa borrados tras reiniciar.
Var CerrojoInstalador
Var Origen
Var EnUso
Var Actualizacion
Var RuntimeAnterior
Var AppAnterior
Var DesinstaladorAnterior
Var RuntimePublicado
Var AppPublicado
Var DesinstaladorPublicado

; Rename con reintentos durante 2 minutos. Deja el indicador de error activo sólo si al final no se pudo.
; Windows no permite mover una carpeta mientras otro proceso (p. ej. el antivirus) tiene abierto un archivo dentro.
!macro RENOMBRAR ORIGEN DESTINO ID
  StrCpy $R8 0
  reintentar_${ID}:
    ClearErrors
    Rename "${ORIGEN}" "${DESTINO}"
    IfErrors 0 renombrado_${ID}
    IntOp $R8 $R8 + 1
    StrCmp $R8 1 0 +2
      DetailPrint "Esperando a que el antivirus termine de revisar los archivos nuevos..."
    IntCmp $R8 240 agotado_${ID} 0 agotado_${ID}
    Sleep 500
    Goto reintentar_${ID}
  agotado_${ID}:
    SetErrors
  renombrado_${ID}:
!macroend

!include "LogicLib.nsh"
!include "WinVer.nsh"

!macro CERROJO_INSTALADOR PREFIJO
Function ${PREFIJO}.onInit
  ; Sin plugins antes de la primera ventana (como Servicio Exclusivo): nada se extrae a TEMP ni se carga hasta que
  ; se ve el asistente. El Python incluido es de 64 bits y necesita Windows 8.1 o posterior.
  !if "${PREFIJO}" == ""
    ; Un instalador de 32 bits en Windows de 64 bits ve PROCESSOR_ARCHITEW6432 (AMD64 o ARM64).
    ReadEnvStr $0 PROCESSOR_ARCHITEW6432
    ReadEnvStr $1 PROCESSOR_ARCHITECTURE
    ${If} $0 == ""
    ${AndIf} $1 == "x86"
    ${OrIfNot} ${AtLeastWin8.1}
      MessageBox MB_OK|MB_ICONSTOP "${NOMBRE} necesita Windows 10 u 11 de 64 bits. No se modifico nada." /SD IDOK
      SetErrorLevel 5
      Abort
    ${EndIf}
  !endif
  ; Evita que dos actualizadores/desinstaladores de la misma marca publiquen a la vez. Cerrojo sin plugins:
  ; FileOpen comparte el archivo solo para lectura; otro instalador o desinstalador no puede abrirlo para escribir
  ; mientras este siga abierto. Windows lo suelta al cerrarse el proceso.
  ClearErrors
  FileOpen $CerrojoInstalador "$TEMP\Instalador.${NOMBRE}.lock" a
  ${If} ${Errors}
    MessageBox MB_OK|MB_ICONEXCLAMATION "Ya hay un instalador o desinstalador de ${NOMBRE} abierto. Cierrelo antes de continuar." /SD IDOK
    SetErrorLevel 2
    Abort
  ${EndIf}
FunctionEnd
!macroend

!insertmacro CERROJO_INSTALADOR ""
!insertmacro CERROJO_INSTALADOR "un"

!macro ARCHIVOS_EN_USO PREFIJO
; Si el programa esta abierto, Windows no deja abrir para escritura su pythonw.exe, python.exe ni python312.dll
; (estan cargados en memoria). Se prueba abrirlos sin cambiar nada. No se usa Restart Manager: con el aviso repetido
; dejaba al instalador escribiendo en una carpeta equivocada (Windows Server 2025), y los antivirus asocian esa API
; con programas daninos.
Function ${PREFIJO}ProbarArchivo
  IfFileExists "$Origen" 0 fin
  ClearErrors
  FileOpen $R7 "$Origen" a
  IfErrors ocupado
  FileClose $R7
  Goto fin
  ocupado:
    StrCpy $EnUso 1
  fin:
FunctionEnd

Function ${PREFIJO}ComprobarArchivosEnUso
  Push $R6
  Push $R7
  Push $Origen
  volver_a_comprobar:
  StrCpy $R6 0
  intentar:
    StrCpy $EnUso 0
    StrCpy $Origen "$INSTDIR\runtime\pythonw.exe"
    Call ${PREFIJO}ProbarArchivo
    StrCpy $Origen "$INSTDIR\runtime\python.exe"
    Call ${PREFIJO}ProbarArchivo
    StrCpy $Origen "$INSTDIR\runtime\python312.dll"
    Call ${PREFIJO}ProbarArchivo
    StrCmp $EnUso 0 libre
    ; El antivirus tambien puede tenerlos abiertos un instante: se reintenta unos segundos.
    IntOp $R6 $R6 + 1
    IntCmp $R6 8 ocupado_aviso 0 ocupado_aviso
    Sleep 500
    Goto intentar
  ocupado_aviso:
    ; Reintentar sin salir del asistente; si la ventana no se ve (quedo oculta), reiniciar la cierra.
    MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "${NOMBRE} esta abierto. Guarde su trabajo, cierre ${NOMBRE} y pulse Reintentar.$\r$\n$\r$\nSi no ve la ventana de ${NOMBRE}, reinicie la computadora y vuelva a abrir este instalador.$\r$\n$\r$\nNo se modificaron el programa ni sus datos." /SD IDCANCEL IDRETRY volver_a_comprobar
    Pop $Origen
    Pop $R7
    Pop $R6
    SetErrorLevel 2
    Abort
  libre:
  Pop $Origen
  Pop $R7
  Pop $R6
FunctionEnd
!macroend

!insertmacro ARCHIVOS_EN_USO ""
!insertmacro ARCHIVOS_EN_USO "un."

!macro DATOS_HEREDADOS PREFIJO
Function ${PREFIJO}ComprobarDatosHeredados
  IfFileExists "$INSTDIR\app\agencia.db" datos_dentro
  IfFileExists "$INSTDIR\runtime\agencia.db" datos_dentro
  IfFileExists "$INSTDIR\app\contratos\*.*" datos_dentro
  IfFileExists "$INSTDIR\runtime\contratos\*.*" datos_dentro
  IfFileExists "$INSTDIR\app\respaldos\*.*" datos_dentro
  IfFileExists "$INSTDIR\runtime\respaldos\*.*" datos_dentro
  IfFileExists "$INSTDIR\app\configuracion.json" datos_dentro
  IfFileExists "$INSTDIR\runtime\configuracion.json" datos_dentro
  IfFileExists "$INSTDIR\app\borradores.json" datos_dentro
  IfFileExists "$INSTDIR\runtime\borradores.json" datos_dentro
  IfFileExists "$INSTDIR\app\errores.log" datos_dentro
  IfFileExists "$INSTDIR\runtime\errores.log" datos_dentro
  Return
  datos_dentro:
    MessageBox MB_OK|MB_ICONEXCLAMATION "Esta instalacion contiene datos dentro de app o runtime (base, contratos, respaldos o archivos personales). No se reemplazaron ni borraron.$\r$\n$\r$\nConserve una copia y cambie su ubicacion antes de actualizar o desinstalar ${NOMBRE}." /SD IDOK
    SetErrorLevel 4
    Abort
FunctionEnd
!macroend

!insertmacro DATOS_HEREDADOS "un."

; Al instalar, los datos que alguna vez quedaron dentro de app o runtime (p. ej. si alguien abrió app\agencia.py
; con otro Python) se apartan a la carpeta de datos y la instalación sigue. Servitotal busca ahí la base anterior y
; ofrece traerla. Sólo si Windows no deja moverlos se detiene, sin tocar nada.
!macro APARTAR CARPETA NOMBRE ID
  IfFileExists "$INSTDIR\${CARPETA}\${NOMBRE}" 0 apartado_${ID}
    CreateDirectory "$R6\${CARPETA}"
    ClearErrors
    Rename "$INSTDIR\${CARPETA}\${NOMBRE}" "$R6\${CARPETA}\${NOMBRE}"
    IfErrors datos_no_apartados
  apartado_${ID}:
!macroend

Function ComprobarDatosHeredados
  StrCpy $R6 "${DATOS}\Recuperado de la instalacion anterior"
  StrCpy $R5 1
  destino_libre:
    IfFileExists "$R6\*.*" 0 destino_elegido
    IntOp $R5 $R5 + 1
    StrCpy $R6 "${DATOS}\Recuperado de la instalacion anterior $R5"
    Goto destino_libre
  destino_elegido:
  !insertmacro APARTAR "app" "agencia.db" a1
  !insertmacro APARTAR "app" "agencia.db-wal" a2
  !insertmacro APARTAR "app" "agencia.db-shm" a3
  !insertmacro APARTAR "app" "agencia.db-journal" a4
  !insertmacro APARTAR "app" "contratos" a5
  !insertmacro APARTAR "app" "respaldos" a6
  !insertmacro APARTAR "app" "configuracion.json" a7
  !insertmacro APARTAR "app" "borradores.json" a8
  !insertmacro APARTAR "app" "errores.log" a9
  !insertmacro APARTAR "runtime" "agencia.db" r1
  !insertmacro APARTAR "runtime" "agencia.db-wal" r2
  !insertmacro APARTAR "runtime" "agencia.db-shm" r3
  !insertmacro APARTAR "runtime" "agencia.db-journal" r4
  !insertmacro APARTAR "runtime" "contratos" r5
  !insertmacro APARTAR "runtime" "respaldos" r6
  !insertmacro APARTAR "runtime" "configuracion.json" r7
  !insertmacro APARTAR "runtime" "borradores.json" r8
  !insertmacro APARTAR "runtime" "errores.log" r9
  Return
  datos_no_apartados:
    MessageBox MB_OK|MB_ICONEXCLAMATION "Hay datos guardados dentro de la carpeta del programa ${NOMBRE} y Windows no permitio apartarlos. No se cambio ni se borro nada.$\r$\n$\r$\nReinicie la computadora y vuelva a abrir este instalador. Si se repite, pida ayuda a quien le instalo el programa." /SD IDOK
    SetErrorLevel 4
    Abort
FunctionEnd

Function .onInstFailed
  ; Sólo limpiar nuestro staging si no quedan originales pendientes de recuperar.
  StrCmp $Actualizacion "" conservar_staging
  IfFileExists "$Actualizacion\runtime-anterior\*.*" conservar_staging
  IfFileExists "$Actualizacion\app-anterior\*.*" conservar_staging
  IfFileExists "$Actualizacion\Desinstalar-anterior.exe" conservar_staging
  SetOutPath "$INSTDIR"
  RMDir /r "$Actualizacion"
  conservar_staging:
FunctionEnd
