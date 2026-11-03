# Instalador opcional de tarea programada Windows para S4-J4.
# El modo predeterminado es SOLO CONSULTA; nunca cambia el modelo activo.
param(
    [ValidateSet('consulta','aplicar')]
    [string]$Modo = 'consulta',
    [switch]$Registrar,
    [switch]$ConfirmarAplicacion
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $repo 'venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    throw "No se encontro Python del entorno virtual: $python"
}

if ($Modo -eq 'aplicar' -and -not $ConfirmarAplicacion) {
    throw 'Para registrar un job que pueda ejecutar rollback, agregue -ConfirmarAplicacion. Use esto SOLO al desplegar datos reales etiquetados.'
}

$argumentos = '-m src.monitoring.rollback_job --caso-uso churn'
if ($Modo -eq 'aplicar') { $argumentos += ' --aplicar' }
$nombre = 'Sistema-MLOps-S4-J4'

Write-Host "Repositorio: $repo"
Write-Host "Python: $python"
Write-Host "Argumentos: $argumentos"
Write-Host 'Frecuencia: diaria a las 03:00 (hora local de Windows)'
Write-Host "Nombre de tarea: $nombre"
if (-not $Registrar) {
    Write-Host 'Vista previa solamente. Para crear la tarea sin modificar modelos, ejecute este script con -Registrar.'
    exit 0
}

if (-not (Get-Command Register-ScheduledTask -ErrorAction SilentlyContinue)) {
    throw 'Este sistema no tiene el modulo ScheduledTasks de Windows.'
}

$accion = New-ScheduledTaskAction -Execute $python -Argument $argumentos -WorkingDirectory $repo
$disparador = New-ScheduledTaskTrigger -Daily -At '03:00'
Register-ScheduledTask -TaskName $nombre -Action $accion -Trigger $disparador -Description 'Evaluacion MLOps J4 de degradacion y rollback' -Force | Out-Null
Write-Host "Tarea registrada: $nombre (modo $Modo)."
Write-Host "Para eliminarla: Unregister-ScheduledTask -TaskName '$nombre' -Confirm:`$false"
