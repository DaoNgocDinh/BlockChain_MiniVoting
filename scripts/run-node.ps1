param(
    [ValidateSet('node1', 'node2', 'node3', 'node4')]
    [string]$NodeId = 'node1'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create .venv and install requirements-dev.txt first; see README.md.'
}
$configuration = Get-Content -LiteralPath (Join-Path $projectRoot 'config\nodes.json') -Raw | ConvertFrom-Json
$nodeConfig = $configuration.nodes | Where-Object { $_.id -eq $NodeId }
$previousNodeId = $env:NODE_ID
Push-Location $projectRoot
try {
    $env:NODE_ID = $NodeId
    & $pythonPath -m uvicorn src.api.app:app --host $nodeConfig.host --port $nodeConfig.port
    if ($LASTEXITCODE -ne 0) { throw ('Node exited with code ' + $LASTEXITCODE) }
} finally {
    $env:NODE_ID = $previousNodeId
    Pop-Location
}
