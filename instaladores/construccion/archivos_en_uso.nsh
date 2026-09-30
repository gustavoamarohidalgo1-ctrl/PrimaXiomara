; Protecciones nativas antes de tocar archivos de una instalación.
; Restart Manager: https://learn.microsoft.com/windows/win32/api/restartmanager/nf-restartmanager-rmgetlist
; Sólo consulta procesos; nunca los cierra ni programa borrados tras reiniciar.
Var CerrojoInstalador
Var Actualizacion
Var RuntimeAnterior
Var AppAnterior
Var DesinstaladorAnterior
Var RuntimePublicado
Var AppPublicado
Var DesinstaladorPublicado

; Rename con reintentos durante 30 s. Deja el indicador de error activo sólo si al final no se pudo.
; Windows no permite mover una carpeta mientras otro proceso (p. ej. el antivirus) tiene abierto un archivo dentro.
!macro RENOMBRAR ORIGEN DESTINO ID
  StrCpy $R8 0
  reintentar_${ID}:
    ClearErrors
    Rename "${ORIGEN}" "${DESTINO}"
    IfErrors 0 renombrado_${ID}
    IntOp $R8 $R8 + 1
    IntCmp $R8 60 agotado_${ID} 0 agotado_${ID}
    Sleep 500
    Goto reintentar_${ID}
  agotado_${ID}:
    SetErrors
  renombrado_${ID}:
!macroend

!include "LogicLib.nsh"
!include "x64.nsh"
!include "WinVer.nsh"

!macro CERROJO_INSTALADOR PREFIJO
Function ${PREFIJO}.onInit
  !if "${PREFIJO}" == ""
    ; El Python incluido es de 64 bits y necesita Windows 8.1 o posterior: avisar en vez de un error de DLL.
    ${IfNot} ${RunningX64}
    ${OrIfNot} ${AtLeastWin8.1}
      MessageBox MB_OK|MB_ICONSTOP "${NOMBRE} necesita Windows 10 u 11 de 64 bits. No se modifico nada." /SD IDOK
      SetErrorLevel 5
      Abort
    ${EndIf}
  !endif
  ; Evita que dos actualizadores/desinstaladores de la misma marca publiquen a la vez.
  System::Call 'kernel32::CreateMutexW(p 0, i 0, w "Local\Instalador.${NOMBRE}") p .r0 ?e'
  Pop $1
  StrCpy $CerrojoInstalador $0
  StrCmp $0 0 bloqueo_error
  StrCmp $1 183 bloqueo_ocupado
  Return
  bloqueo_ocupado:
    MessageBox MB_OK|MB_ICONEXCLAMATION "Ya hay un instalador o desinstalador de ${NOMBRE} abierto. Cierrelo antes de continuar." /SD IDOK
    SetErrorLevel 2
    Abort
  bloqueo_error:
    MessageBox MB_OK|MB_ICONSTOP "No se pudo comprobar otra instalacion en curso. No se modificaron los archivos." /SD IDOK
    SetErrorLevel 2
    Abort
FunctionEnd
!macroend

!insertmacro CERROJO_INSTALADOR ""
!insertmacro CERROJO_INSTALADOR "un"

!macro ARCHIVOS_EN_USO PREFIJO
Function ${PREFIJO}ComprobarArchivosEnUso
  volver_a_comprobar:
  System::Store "s"
  StrCpy $R9 0
  IfFileExists "$INSTDIR\runtime\pythonw.exe" comprobar
  IfFileExists "$INSTDIR\runtime\python.exe" comprobar
  IfFileExists "$INSTDIR\runtime\python312.dll" comprobar finalizar
  comprobar:
    StrCpy $R9 2
    System::Call 'rstrtmgr::RmStartSession(*i .r0, i 0, w .r1) i .r5'
    StrCmp $5 0 0 finalizar
    System::Call '*(&w${NSIS_MAX_STRLEN} "$INSTDIR\runtime\pythonw.exe") p .r1'
    System::Call '*(&w${NSIS_MAX_STRLEN} "$INSTDIR\runtime\python.exe") p .r2'
    System::Call '*(&w${NSIS_MAX_STRLEN} "$INSTDIR\runtime\python312.dll") p .r3'
    System::Call '*(p r1, p r2, p r3) p .r4'
    StrCmp $1 0 liberar
    StrCmp $2 0 liberar
    StrCmp $3 0 liberar
    StrCmp $4 0 liberar
    System::Call 'rstrtmgr::RmRegisterResources(i r0, i 3, p r4, i 0, p 0, i 0, p 0) i .r5'
    StrCmp $5 0 0 liberar
    ; Array nulo y capacidad cero: 234 indica procesos; 0 y cantidad cero indica libre.
    System::Call 'rstrtmgr::RmGetList(i r0, *i .r6, *i 0 .r7, p 0, *i .r8) i .r5'
    StrCmp $5 234 ocupado
    StrCmp $5 0 0 liberar
    StrCmp $6 0 0 ocupado
    StrCpy $R9 0
    Goto liberar
  ocupado:
    StrCpy $R9 1
  liberar:
    System::Free $4
    System::Free $3
    System::Free $2
    System::Free $1
    System::Call 'rstrtmgr::RmEndSession(i r0)'
  finalizar:
    Push $R9
    System::Store "l"
    Pop $0
    StrCmp $0 0 libre
    StrCmp $0 1 0 no_comprobado
    ; Reintentar sin salir del asistente; si la ventana no se ve (quedó oculta), reiniciar la cierra.
    MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "${NOMBRE} esta abierto. Guarde su trabajo, cierre ${NOMBRE} y pulse Reintentar.$\r$\n$\r$\nSi no ve la ventana de ${NOMBRE}, reinicie la computadora y vuelva a abrir este instalador.$\r$\n$\r$\nNo se modificaron el programa ni sus datos." /SD IDCANCEL IDRETRY volver_a_comprobar
    SetErrorLevel 2
    Abort
  no_comprobado:
    MessageBox MB_RETRYCANCEL|MB_ICONSTOP "Windows no pudo comprobar si ${NOMBRE} esta abierto. Cierre ${NOMBRE} y pulse Reintentar, o reinicie la computadora y vuelva a abrir este instalador.$\r$\n$\r$\nNo se modificaron el programa ni sus datos." /SD IDCANCEL IDRETRY volver_a_comprobar
    SetErrorLevel 2
    Abort
  libre:
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

!insertmacro DATOS_HEREDADOS ""
!insertmacro DATOS_HEREDADOS "un."

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
