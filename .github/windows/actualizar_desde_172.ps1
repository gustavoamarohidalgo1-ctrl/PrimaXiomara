# Actualización de Servitotal tal como la tiene la agencia: se instala la versión 1.7.2 publicada, se cargan datos
# ficticios con su propio código (garantías en días, un contrato firmado), se instala encima la versión nueva y se
# abre. Debe guardar una copia antes de actualizar, pasar las garantías a meses (30 días = 1 mes) sin perder nada y
# abrir sin avisos de error.
param(
  [Parameter(Mandatory)][string]$Instalador,
  [string]$Salida = "$env:RUNNER_TEMP\resultados"
)
$ErrorActionPreference = 'Continue'
New-Item -ItemType Directory -Force $Salida | Out-Null
$fallos = 0
function Fallo($t) { Write-Host "::error::desde-1.7.2 - $t"; $script:fallos++ }
$Instalador = (Resolve-Path $Instalador).Path
$Instdir = Join-Path $env:LOCALAPPDATA 'Programs\Servitotal'
$Datos = Join-Path $env:LOCALAPPDATA 'Servitotal'
$Clave = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Servitotal'
if (Test-Path "$Instdir\Desinstalar.exe") { Start-Process "$Instdir\Desinstalar.exe" -ArgumentList '/S', "_?=$Instdir" -Wait }
Remove-Item -Recurse -Force $Instdir, $Datos -ErrorAction SilentlyContinue

# 1) La versión 1.7.2 publicada (la de la rama main), comprobada por su huella
$anterior = Join-Path $env:RUNNER_TEMP 'Servitotal-1.7.2.exe'
Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/gustavoamarohidalgo1-ctrl/PrimaXiomara/raw/ae4d693d2b156190757f490dcc4cfd9186d80108/instaladores/Servitotal-Windows-x64.exe' -OutFile $anterior
$huella = (Get-FileHash $anterior -Algorithm SHA256).Hash.ToLower()
if ($huella -ne '899cd563e7b6e207119e1ad477d0ecdeba78478207a589adfa154225625dc49f') { Fallo "La 1.7.2 descargada no es la publicada ($huella)"; exit 1 }
$p = Start-Process -FilePath $anterior -ArgumentList '/S' -Wait -PassThru
$version = (Get-ItemProperty $Clave -ErrorAction SilentlyContinue).DisplayVersion
Write-Host "Instalada la versión anterior: código $($p.ExitCode), versión $version"
if ($p.ExitCode -ne 0 -or $version -ne '1.7.2') { Fallo "No quedó instalada la 1.7.2 (código $($p.ExitCode), versión $version)"; exit 1 }

# 2) Datos ficticios escritos por el propio Servitotal 1.7.2
$env:AGENCIA_DATOS = $Datos
& "$Instdir\runtime\python.exe" -E -s "$PSScriptRoot\datos_172.py" "$Instdir\app" 2>&1 | Tee-Object -FilePath (Join-Path $Salida 'datos-172.txt') | Write-Host
$codigo = $LASTEXITCODE
Remove-Item Env:\AGENCIA_DATOS
if ($codigo -ne 0) { Fallo 'No se pudieron crear los datos con la 1.7.2'; exit 1 }

# 3) Instalar la versión nueva encima
$p = Start-Process -FilePath $Instalador -ArgumentList '/S' -Wait -PassThru
$version = (Get-ItemProperty $Clave -ErrorAction SilentlyContinue).DisplayVersion
Write-Host "Actualización sobre 1.7.2 -> código $($p.ExitCode), versión $version"
if ($p.ExitCode -ne 0) { Fallo "La actualización terminó con código $($p.ExitCode)" }
if (Test-Path "$Instdir\app\contratos_servitotal.py") { Fallo 'Quedaron archivos del programa anterior en app' }
Get-ChildItem $Instdir -Directory -Force | Where-Object Name -notin 'runtime', 'app' |
  ForEach-Object { Fallo "Quedó una carpeta temporal tras actualizar: $($_.Name)" }

# 4) Primer arranque de la versión nueva con esos datos, con los argumentos del acceso directo
$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Servitotal\Servitotal.lnk'))
$partes = [regex]::Matches($s.Arguments, '"([^"]*)"|(\S+)') | ForEach-Object { if ($_.Groups[1].Success) { $_.Groups[1].Value } else { $_.Groups[2].Value } }
$partes = @($partes | Select-Object -Skip ([array]::FindIndex([string[]]$partes, [Predicate[string]]{ param($x) $x -like '*.pyw' })))
$json = Join-Path $Salida 'desde-172.json'
& "$Instdir\runtime\python.exe" -E -s "$PSScriptRoot\arranque.py" $json @partes 2>&1 | Out-File (Join-Path $Salida 'desde-172.txt') -Encoding utf8
if ($LASTEXITCODE -ne 0) { Fallo "El primer arranque sobre datos 1.7.2 falló: $(Get-Content $json -Raw -Encoding utf8)" }
$r = Get-Content $json -Raw -Encoding utf8 | ConvertFrom-Json
foreach ($a in @($r.avisos)) { Write-Host "aviso $($a.tipo): $($a.titulo) - $($a.mensaje)" }

# 5) Comprobar la base actualizada y la copia previa
& "$Instdir\runtime\python.exe" -E -s "$PSScriptRoot\comprobar_180.py" (Join-Path $Datos 'agencia.db') $Datos 2>&1 | Write-Host
if ($LASTEXITCODE -ne 0) { Fallo 'La base de la 1.7.2 no quedó bien actualizada' }

# 6) Abrir desde el acceso directo, como ella, y cerrar con la X
& "$PSScriptRoot\abrir_programa.ps1" -Archivo (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Servitotal\Servitotal.lnk') -Proceso pythonw -Datos $Datos -Nombre 'desde-172-acceso' -Salida $Salida
if ($LASTEXITCODE -ne 0) { Fallo 'El programa no abrió bien desde el acceso directo tras actualizar' }

if ($fallos) { exit 1 }
Write-Host 'OK: actualización desde Servitotal 1.7.2 con datos.'
exit 0
