# Script kiểm tra trạng thái 4 validator nodes của MiniVoting
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $projectRoot 'config\nodes.json'
$configuration = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json

$pidsFile = Join-Path $projectRoot '.run\nodes.json'
$pidsMap = @{}

if (Test-Path -LiteralPath $pidsFile) {
    try {
        $runtimeInfo = Get-Content -LiteralPath $pidsFile -Raw | ConvertFrom-Json
        foreach ($item in $runtimeInfo.nodes) {
            $pidsMap[$item.id] = $item.pid
        }
    } catch {}
}

Write-Host "=== KIỂM TRA TRẠNG THÁI 4 NODE MINIVOTING ===" -ForegroundColor Cyan

$statusList = foreach ($node in $configuration.nodes) {
    $url = "http://$($node.host):$($node.port)/health"
    $pidVal = if ($pidsMap.ContainsKey($node.id)) { $pidsMap[$node.id] } else { "N/A" }
    
    $procAlive = "KHÔNG CHẠY"
    if ($pidVal -ne "N/A") {
        $numericPid = [int]$pidVal
        $p = Get-Process -Id $numericPid -ErrorAction SilentlyContinue
        if ($null -ne $p) {
            $procAlive = "ĐANG CHẠY"
        } else {
            $procAlive = "ĐÃ THOÁT"
        }
    }

    $healthStatus = "OFFLINE"
    $consensusReady = "N/A"
    try {
        $resp = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 1 -ErrorAction Stop
        $healthStatus = "ONLINE (200)"
        $consensusReady = $resp.consensus_ready
    } catch {
        $healthStatus = "OFFLINE / KHÔNG KẾT NỐI"
    }

    [PSCustomObject]@{
        NodeId = $node.id
        Port = $node.port
        PID = $pidVal
        Process = $procAlive
        Health = $healthStatus
        ConsensusReady = $consensusReady
    }
}

$statusList | Format-Table -AutoSize
