# Actualización desde Servitotal 1.8.0 (la que se entregó antes de los avisos): se instala ese mismo instalador, se
# cargan datos ficticios con su propio código, se instala encima la versión nueva y se abre. Debe guardar una copia
# antes de actualizar, agregar la tabla de avisos sin cambiar nada de lo anterior y abrir sin avisos de error.
param(
  [Parameter(Mandatory)][string]$Instalador,
  [string]$Salida = "$env:RUNNER_TEMP\resultados"
)
$ErrorActionPreference = 'Continue'
New-Item -ItemType Directory -Force $Salida | Out-Null
$fallos = 0
function Fallo($t) { Write-Host "::error::desde-1.8.0 - $t"; $script:fallos++ }
$Instalador = (Resolve-Path $Instalador).Path
$Instdir = Join-Path $env:LOCALAPPDATA 'Programs\Servitotal'
$Datos = Join-Path $env:LOCALAPPDATA 'Servitotal'
$Clave = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Servitotal'
if (Test-Path "$Instdir\Desinstalar.exe") { Start-Process "$Instdir\Desinstalar.exe" -ArgumentList '/S', "_?=$Instdir" -Wait }
Remove-Item -Recurse -Force $Instdir, $Datos -ErrorAction SilentlyContinue

# 1) El instalador 1.8.0 que se entregó (rama prueba-1.8.0), comprobado por su huella
$anterior = Join-Path $env:RUNNER_TEMP 'Servitotal-1.8.0.exe'
Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/raw/517d7cb1772c0c495435b3d26261831077e6267b/instaladores/Servitotal-Windows-x64.exe' -OutFile $anterior
$huella = (Get-FileHash $anterior -Algorithm SHA256).Hash.ToLower()
if ($huella -ne '17435037c577e3c0012109197eba81b13ac344ecbf6f46154c959922a0d6c7fc') { Fallo "La 1.8.0 descargada no es la entregada ($huella)"; exit 1 }
$p = Start-Process -FilePath $anterior -ArgumentList '/S' -Wait -PassThru
$version = (Get-ItemProperty $Clave -ErrorAction SilentlyContinue).DisplayVersion
Write-Host "Instalada la versión anterior: código $($p.ExitCode), versión $version"
if ($p.ExitCode -ne 0 -or $version -ne '1.8.0') { Fallo "No quedó instalada la 1.8.0 (código $($p.ExitCode), versión $version)"; exit 1 }

# 2) Datos ficticios escritos por el propio Servitotal 1.8.0 (y cómo quedaron, para compararlos después)
$env:AGENCIA_DATOS = $Datos
$antes = Join-Path $Salida 'datos-180.json'
& "$Instdir\runtime\python.exe" -E -s "$PSScriptRoot\datos_180.py" "$Instdir\app" $antes 2>&1 | Tee-Object -FilePath (Join-Path $Salida 'datos-180.txt') | Write-Host
$codigo = $LASTEXITCODE
Remove-Item Env:\AGENCIA_DATOS
if ($codigo -ne 0) { Fallo 'No se pudieron crear los datos con la 1.8.0'; exit 1 }

# 3) Instalar la versión nueva encima
$p = Start-Process -FilePath $Instalador -ArgumentList '/S' -Wait -PassThru
$version = (Get-ItemProperty $Clave -ErrorAction SilentlyContinue).DisplayVersion
Write-Host "Actualización sobre 1.8.0 -> código $($p.ExitCode), versión $version"
if ($p.ExitCode -ne 0) { Fallo "La actualización terminó con código $($p.ExitCode)" }
$nueva = (Select-String -Path (Join-Path (Split-Path $PSScriptRoot -Parent | Split-Path -Parent) 'agencia.py') -Pattern '^VERSION = "([0-9.]+)"').Matches[0].Groups[1].Value
if ($version -ne $nueva) { Fallo "El registro dice $version y la versión nueva es $nueva" }
Get-ChildItem $Instdir -Directory -Force | Where-Object Name -notin 'runtime', 'app' |
  ForEach-Object { Fallo "Quedó una carpeta temporal tras actualizar: $($_.Name)" }

# 4) Primer arranque de la versión nueva con esos datos, con los argumentos del acceso directo
$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Servitotal\Servitotal.lnk'))
$partes = [regex]::Matches($s.Arguments, '"([^"]*)"|(\S+)') | ForEach-Object { if ($_.Groups[1].Success) { $_.Groups[1].Value } else { $_.Groups[2].Value } }
$partes = @($partes | Select-Object -Skip ([array]::FindIndex([string[]]$partes, [Predicate[string]]{ param($x) $x -like '*.pyw' })))
$json = Join-Path $Salida 'desde-180.json'
& "$Instdir\runtime\python.exe" -E -s "$PSScriptRoot\arranque.py" $json @partes 2>&1 | Out-File (Join-Path $Salida 'desde-180.txt') -Encoding utf8
if ($LASTEXITCODE -ne 0) { Fallo "El primer arranque sobre datos 1.8.0 falló: $(Get-Content $json -Raw -Encoding utf8)" }
$r = Get-Content $json -Raw -Encoding utf8 | ConvertFrom-Json
foreach ($a in @($r.avisos)) { Write-Host "aviso $($a.tipo): $($a.titulo) - $($a.mensaje)" }

# 5) Comprobar la base actualizada y la copia previa
& "$Instdir\runtime\python.exe" -E -s "$PSScriptRoot\comprobar_desde_180.py" (Join-Path $Datos 'agencia.db') $Datos $antes 2>&1 | Write-Host
if ($LASTEXITCODE -ne 0) { Fallo 'La base de la 1.8.0 no quedó bien actualizada' }

# 6) Abrir desde el acceso directo, como ella, y cerrar con la X
& "$PSScriptRoot\abrir_programa.ps1" -Archivo (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Servitotal\Servitotal.lnk') -Proceso pythonw -Datos $Datos -Nombre 'desde-180-acceso' -Salida $Salida
if ($LASTEXITCODE -ne 0) { Fallo 'El programa no abrió bien desde el acceso directo tras actualizar' }

if ($fallos) { exit 1 }
Write-Host 'OK: actualización desde Servitotal 1.8.0 con datos.'
exit 0
