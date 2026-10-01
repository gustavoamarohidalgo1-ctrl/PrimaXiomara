; Instalador de Windows (64 bits) de la Servitotal.  Lo compila crear_instalador_windows.sh (NSIS).
; Se instala solo para el usuario actual (no pide permisos de administrador) e incluye su propio Python.
; Los datos de la agencia viven aparte, en %LOCALAPPDATA%\Servitotal: actualizar o desinstalar
; el programa no los borra (el desinstalador pregunta y, por defecto, los conserva).

Unicode true
SetCompressor /SOLID lzma
AllowSkipFiles off         ; un archivo que no se pudo escribir no se puede «Omitir»: se reintenta o se cancela

!define NOMBRE "Servitotal"
!define CLAVE_DESINSTALAR "Software\Microsoft\Windows\CurrentVersion\Uninstall\Servitotal"
!define DATOS "$LOCALAPPDATA\${NOMBRE}"
; -E -s: el Python incluido no lee PYTHONHOME/PYTHONPATH ni paquetes de otro Python instalado en el equipo.
!define COMANDO_ARGUMENTOS '-E -s "$INSTDIR\app\iniciar.pyw" --datos "${DATOS}"'

Name "${NOMBRE}"
OutFile "${SALIDA}"
RequestExecutionLevel user
InstallDir "$LOCALAPPDATA\Programs\${NOMBRE}"
InstallDirRegKey HKCU "Software\${NOMBRE}" "Carpeta"
BrandingText "${NOMBRE} ${VERSION}"

VIProductVersion "${VERSION}.0"
VIAddVersionKey /LANG=1034 "ProductName" "${NOMBRE}"
VIAddVersionKey /LANG=1034 "FileDescription" "Instalador de ${NOMBRE}"
VIAddVersionKey /LANG=1034 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=1034 "ProductVersion" "${VERSION}"
VIAddVersionKey /LANG=1034 "LegalCopyright" "${NOMBRE}"

!include "MUI2.nsh"
!include "WordFunc.nsh"    ; VersionCompare (instrucciones de NSIS, sin complementos)
!addincludedir "${RAIZ}\instaladores\construccion"   ; makensis de Windows no acepta / en estas rutas
!include "archivos_en_uso.nsh"
!define MUI_ICON "${ICONO}"
!define MUI_UNICON "${ICONO}"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Instalar ${NOMBRE}"
!define MUI_WELCOMEPAGE_TEXT "Este asistente instalará ${NOMBRE} en su computadora.$\r$\n$\r$\nNo necesita instalar nada más: el programa trae todo lo que usa.$\r$\n$\r$\nSus datos (clientes, trabajadoras, contratos) se guardan aparte y no se pierden al actualizar o desinstalar.$\r$\n$\r$\nHaga clic en Siguiente para continuar."
!define MUI_FINISHPAGE_TEXT "${NOMBRE} quedo instalado.$\r$\n$\r$\nAl pulsar Terminar se abrira solo; la primera vez puede tardar unos segundos. Despues abralo con el icono ${NOMBRE} del Escritorio."
!define MUI_FINISHPAGE_RUN ""
!define MUI_FINISHPAGE_RUN_FUNCTION AbrirPrograma
!define MUI_FINISHPAGE_RUN_TEXT "Abrir ${NOMBRE} ahora"

!insertmacro MUI_PAGE_WELCOME
; Al pulsar «Instalar» se comprueba primero si Servitotal está abierto: si la persona cancela, el asistente se queda
; en esta página (Abort en una función «leave») en vez de terminar como instalación anulada.
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE ComprobarAntesDeInstalar
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Spanish"

Function ComprobarAntesDeInstalar
  Call ComprobarArchivosEnUso
  SetErrorLevel 0     ; un «Cancelar» anterior en esta comprobación no debe quedar como código de salida
FunctionEnd

Function AbrirPrograma
  SetOutPath "$INSTDIR\app"
  ; El instalador está al frente y se cierra enseguida: sin este permiso Windows puede abrir el programa detrás de
  ; las demás ventanas y parecería que no se abrió nada.
  System::Call 'user32::AllowSetForegroundWindow(i -1)'
  ClearErrors
  Exec '"$INSTDIR\runtime\pythonw.exe" ${COMANDO_ARGUMENTOS}'
  IfErrors 0 +2
    MessageBox MB_OK|MB_ICONEXCLAMATION "${NOMBRE} quedo instalado, pero Windows no permitio abrirlo desde aqui.$\r$\n$\r$\nAbralo con el icono ${NOMBRE} del Escritorio o del menu Inicio." /SD IDOK
FunctionEnd

Section "Instalar"
  Call ComprobarArchivosEnUso
  Call ComprobarDatosHeredados

  ; Un instalador viejo (por ejemplo, uno anterior que siga en el chat) no reemplaza sin avisar a uno más nuevo.
  ReadRegStr $R0 HKCU "${CLAVE_DESINSTALAR}" "DisplayVersion"
  ${If} $R0 != ""
    ${VersionCompare} "$R0" "${VERSION}" $R1
    ${If} $R1 == 1
    ${AndIf} ${Cmd} `MessageBox MB_YESNO|MB_ICONEXCLAMATION|MB_DEFBUTTON2 "Ya esta instalada la version $R0 de ${NOMBRE}, mas nueva que esta (${VERSION}).$\r$\n$\r$\nInstalar de todos modos esta version anterior? Sus datos se conservan." /SD IDNO IDNO`
      SetErrorLevel 6
      Abort
    ${EndIf}
  ${EndIf}

  StrCpy $RuntimeAnterior 0
  StrCpy $AppAnterior 0
  StrCpy $DesinstaladorAnterior 0
  StrCpy $RuntimePublicado 0
  StrCpy $AppPublicado 0
  StrCpy $DesinstaladorPublicado 0
  ClearErrors
  CreateDirectory "$INSTDIR"
  GetTempFileName $Actualizacion "$INSTDIR"
  IfErrors fallo_preparacion
  Delete "$Actualizacion"
  CreateDirectory "$Actualizacion"
  SetOutPath "$Actualizacion\runtime"
  File /r "${RUNTIME}\*"
  IfErrors fallo_preparacion
  SetOutPath "$Actualizacion\app"
  File /r "${APLICACION}\*"
  IfErrors fallo_preparacion
  WriteUninstaller "$Actualizacion\Desinstalar.exe"
  IfErrors fallo_preparacion
  SetOutPath "$INSTDIR"
  Call ComprobarArchivosEnUso
  Call ComprobarDatosHeredados

  ; Mantener la instalación anterior hasta publicar las tres piezas completas. Cada cambio de nombre se reintenta:
  ; el antivirus suele revisar durante unos segundos los archivos recién extraídos y bloquea mover su carpeta.
  IfFileExists "$INSTDIR\runtime\*.*" 0 mover_app
    !insertmacro RENOMBRAR "$INSTDIR\runtime" "$Actualizacion\runtime-anterior" apartar_runtime
    IfErrors recuperar_anterior
    StrCpy $RuntimeAnterior 1
  mover_app:
  IfFileExists "$INSTDIR\app\*.*" 0 mover_desinstalador
    !insertmacro RENOMBRAR "$INSTDIR\app" "$Actualizacion\app-anterior" apartar_app
    IfErrors recuperar_anterior
    StrCpy $AppAnterior 1
  mover_desinstalador:
  IfFileExists "$INSTDIR\Desinstalar.exe" 0 publicar_runtime
    !insertmacro RENOMBRAR "$INSTDIR\Desinstalar.exe" "$Actualizacion\Desinstalar-anterior.exe" apartar_desinstalador
    IfErrors recuperar_anterior
    StrCpy $DesinstaladorAnterior 1
  publicar_runtime:
  !insertmacro RENOMBRAR "$Actualizacion\runtime" "$INSTDIR\runtime" publicar_runtime
  IfErrors recuperar_anterior
  StrCpy $RuntimePublicado 1
  !insertmacro RENOMBRAR "$Actualizacion\app" "$INSTDIR\app" publicar_app
  IfErrors recuperar_anterior
  StrCpy $AppPublicado 1
  !insertmacro RENOMBRAR "$Actualizacion\Desinstalar.exe" "$INSTDIR\Desinstalar.exe" publicar_desinstalador
  IfErrors recuperar_anterior
  StrCpy $DesinstaladorPublicado 1

  CreateDirectory "${DATOS}"
  SetOutPath "$INSTDIR\app"
  CreateDirectory "$SMPROGRAMS\${NOMBRE}"
  CreateShortcut "$SMPROGRAMS\${NOMBRE}\${NOMBRE}.lnk" "$INSTDIR\runtime\pythonw.exe" '${COMANDO_ARGUMENTOS}' "$INSTDIR\app\icono.ico" 0
  CreateShortcut "$SMPROGRAMS\${NOMBRE}\Datos de la agencia.lnk" "${DATOS}"
  CreateShortcut "$SMPROGRAMS\${NOMBRE}\Desinstalar.lnk" "$INSTDIR\Desinstalar.exe"
  CreateShortcut "$DESKTOP\${NOMBRE}.lnk" "$INSTDIR\runtime\pythonw.exe" '${COMANDO_ARGUMENTOS}' "$INSTDIR\app\icono.ico" 0

  WriteRegStr HKCU "Software\${NOMBRE}" "Carpeta" "$INSTDIR"
  WriteRegStr HKCU "${CLAVE_DESINSTALAR}" "DisplayName" "${NOMBRE}"
  WriteRegStr HKCU "${CLAVE_DESINSTALAR}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${CLAVE_DESINSTALAR}" "Publisher" "${NOMBRE}"
  WriteRegStr HKCU "${CLAVE_DESINSTALAR}" "DisplayIcon" "$INSTDIR\app\icono.ico"
  WriteRegStr HKCU "${CLAVE_DESINSTALAR}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${CLAVE_DESINSTALAR}" "UninstallString" '"$INSTDIR\Desinstalar.exe"'
  WriteRegDWORD HKCU "${CLAVE_DESINSTALAR}" "NoModify" 1
  WriteRegDWORD HKCU "${CLAVE_DESINSTALAR}" "NoRepair" 1
  Goto instalacion_terminada

  recuperar_anterior:
    SetOutPath "$INSTDIR"
    StrCpy $R7 0      ; 1 si alguna pieza no se pudo devolver a su sitio
    StrCmp $RuntimePublicado 1 0 recuperar_app
      !insertmacro RENOMBRAR "$INSTDIR\runtime" "$Actualizacion\runtime" retirar_runtime
      IfErrors 0 +2
        StrCpy $R7 1
    recuperar_app:
    StrCmp $AppPublicado 1 0 recuperar_desinstalador
      !insertmacro RENOMBRAR "$INSTDIR\app" "$Actualizacion\app" retirar_app
      IfErrors 0 +2
        StrCpy $R7 1
    recuperar_desinstalador:
    StrCmp $DesinstaladorPublicado 1 0 devolver_runtime
      !insertmacro RENOMBRAR "$INSTDIR\Desinstalar.exe" "$Actualizacion\Desinstalar.exe" retirar_desinstalador
      IfErrors 0 +2
        StrCpy $R7 1
    devolver_runtime:
    StrCmp $RuntimeAnterior 1 0 devolver_app
      !insertmacro RENOMBRAR "$Actualizacion\runtime-anterior" "$INSTDIR\runtime" devolver_runtime
      IfErrors 0 +2
        StrCpy $R7 1
    devolver_app:
    StrCmp $AppAnterior 1 0 devolver_desinstalador
      !insertmacro RENOMBRAR "$Actualizacion\app-anterior" "$INSTDIR\app" devolver_app
      IfErrors 0 +2
        StrCpy $R7 1
    devolver_desinstalador:
    StrCmp $DesinstaladorAnterior 1 0 recuperacion_revisada
      !insertmacro RENOMBRAR "$Actualizacion\Desinstalar-anterior.exe" "$INSTDIR\Desinstalar.exe" devolver_desinstalador
      IfErrors 0 +2
        StrCpy $R7 1
    recuperacion_revisada:
    StrCmp $R7 1 recuperacion_incompleta
    MessageBox MB_OK|MB_ICONSTOP "No se pudo completar la instalacion de ${NOMBRE} porque Windows o el antivirus tenian ocupados sus archivos. No se cambio nada y sus datos estan a salvo.$\r$\n$\r$\nReinicie la computadora y vuelva a abrir este instalador." /SD IDOK
    RMDir /r "$Actualizacion"
    SetErrorLevel 3
    Abort
  recuperacion_incompleta:
    MessageBox MB_OK|MB_ICONSTOP "No se pudo completar la instalacion de ${NOMBRE}. Sus datos estan a salvo.$\r$\n$\r$\nReinicie la computadora y vuelva a abrir este instalador para terminarla.$\r$\n$\r$\n(Copia de los archivos anteriores: $Actualizacion)" /SD IDOK
    SetErrorLevel 3
    Abort
  fallo_preparacion:
    SetOutPath "$INSTDIR"
    StrCmp $Actualizacion "" +2
      RMDir /r "$Actualizacion"
    MessageBox MB_OK|MB_ICONSTOP "No se pudieron preparar los archivos de ${NOMBRE}: puede faltar espacio en el disco o el antivirus los bloqueo. No se cambio nada y sus datos estan a salvo.$\r$\n$\r$\nReinicie la computadora y vuelva a abrir este instalador." /SD IDOK
    SetErrorLevel 3
    Abort
  instalacion_terminada:
    SetOutPath "$INSTDIR"
    RMDir /r "$Actualizacion"
SectionEnd

Section "Uninstall"
  Call un.ComprobarArchivosEnUso
  Call un.ComprobarDatosHeredados
  MessageBox MB_YESNO|MB_ICONQUESTION|MB_DEFBUTTON2 "¿Desea borrar también los DATOS de la agencia en esta computadora (clientes, trabajadoras, contratos y sus copias)?$\r$\n$\r$\nEsta acción NO se puede deshacer. Las copias en Documentos\Respaldos ${NOMBRE} y en la carpeta adicional no se borran: si la computadora cambia de dueño, bórrelas a mano.$\r$\n$\r$\nSi solo quiere reinstalar o actualizar el programa, elija No." /SD IDNO IDNO conservar_datos
    Call un.ComprobarArchivosEnUso
    RMDir /r "${DATOS}"
  conservar_datos:
  Call un.ComprobarArchivosEnUso

  ; solo lo que instaló este programa; nunca se borra una carpeta entera que el usuario haya elegido
  RMDir /r "$INSTDIR\runtime"
  RMDir /r "$INSTDIR\app"
  Delete "$INSTDIR\Desinstalar.exe"
  RMDir "$INSTDIR"

  Delete "$SMPROGRAMS\${NOMBRE}\${NOMBRE}.lnk"
  Delete "$SMPROGRAMS\${NOMBRE}\Datos de la agencia.lnk"
  Delete "$SMPROGRAMS\${NOMBRE}\Desinstalar.lnk"
  RMDir "$SMPROGRAMS\${NOMBRE}"
  Delete "$DESKTOP\${NOMBRE}.lnk"
  DeleteRegKey HKCU "${CLAVE_DESINSTALAR}"
  DeleteRegKey HKCU "Software\${NOMBRE}"
SectionEnd
