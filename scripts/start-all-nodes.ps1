# Script khởi động 4 validator nodes của MiniVoting
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Môi trường ảo .venv không tồn tại. Hãy cài đặt theo README.md trước.'
}

$configPath = Join-Path $projectRoot 'config\nodes.json'
$configuration = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json

$runDir = Join-Path $projectRoot '.run'
if (-not (Test-Path -LiteralPath $runDir)) {
    New-Item -ItemType Directory -Path $runDir | Out-Null
}

$pidsFile = Join-Path $runDir 'nodes.json'

# Kiểm tra xem các node đã chạy từ trước chưa
if (Test-Path -LiteralPath $pidsFile) {
    try {
        $existing = Get-Content -LiteralPath $pidsFile -Raw | ConvertFrom-Json
        $stillRunning = @()
        foreach ($item in $existing.nodes) {
            $p = Get-Process -Id $item.pid -ErrorAction SilentlyContinue
            if ($null -ne $p) {
                $stillRunning += $item
            }
        }
        if ($stillRunning.Count -gt 0) {
            Write-Warning "Đã có $($stillRunning.Count) node đang chạy. Dùng scripts/stop-all-nodes.ps1 trước."
            exit 1
        }
    } catch {
        # File cũ bị lỗi, ghi đè
    }
}

Write-Host "Khởi động 4 node MiniVoting..." -ForegroundColor Cyan

$startedNodes = @()

foreach ($node in $configuration.nodes) {
    # Đảm bảo thư mục dữ liệu của từng node tồn tại độc lập
    $nodeDataDir = Join-Path $projectRoot $node.data_dir
    if (-not (Test-Path -LiteralPath $nodeDataDir)) {
        New-Item -ItemType Directory -Path $nodeDataDir -Force | Out-Null
    }

    $arguments = "-m uvicorn src.api.app:app --host $($node.host) --port $($node.port)"
    
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $pythonPath
    $psi.Arguments = $arguments
    $psi.WorkingDirectory = $projectRoot
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.EnvironmentVariables["NODE_ID"] = $node.id

    $process = [System.Diagnostics.Process]::Start($psi)
    
    $startedNodes += [PSCustomObject]@{
        id = $node.id
        pid = $process.Id
        host = $node.host
        port = $node.port
        data_dir = $node.data_dir
    }
    
    Write-Host "  -> Đã khởi tạo $($node.id) tại http://$($node.host):$($node.port) (PID: $($process.Id))"
}

# Lưu danh sách PID vào .run/nodes.json
$runtimeInfo = [PSCustomObject]@{
    started_at = (Get-Date).ToString("o")
    workspace = $projectRoot
    nodes = $startedNodes
}

$runtimeInfo | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $pidsFile -Encoding UTF8

# Chờ và kiểm tra /health trên cả 4 node (timeout 15 giây)
Write-Host "`nĐang kiểm tra phản hồi /health của 4 node..." -ForegroundColor Cyan
$timeoutSeconds = 15
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$healthOk = @{}

while ($sw.Elapsed.TotalSeconds -lt $timeoutSeconds -and $healthOk.Count -lt $startedNodes.Count) {
    foreach ($node in $startedNodes) {
        if (-not $healthOk.ContainsKey($node.id)) {
            try {
                $url = "http://$($node.host):$($node.port)/health"
                $resp = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 1 -ErrorAction SilentlyContinue
                if ($resp.status -eq 'ok' -and $resp.node_id -eq $node.id) {
                    $healthOk[$node.id] = $true
                }
            } catch {
                # Chờ uvicorn khởi động
            }
        }
    }
    Start-Sleep -Milliseconds 300
}

# In bảng tổng kết
Write-Host "`n=== BẢNG TRẠNG THÁI CÁC NODE ===" -ForegroundColor Green
$table = foreach ($node in $startedNodes) {
    $isOk = $healthOk.ContainsKey($node.id)
    [PSCustomObject]@{
        NodeId = $node.id
        Port = $node.port
        PID = $node.pid
        Health = if ($isOk) { "OK (200)" } else { "TIMEOUT / CHƯA PHẢN HỒI" }
    }
}
$table | Format-Table -AutoSize

if ($healthOk.Count -eq $startedNodes.Count) {
    Write-Host "Cả 4 node đã khởi động thành công và phản hồi /health!" -ForegroundColor Green
    Write-Host "Chạy 'powershell -File scripts/stop-all-nodes.ps1' để dừng an toàn." -ForegroundColor Gray
} else {
    Write-Warning "Một số node chưa phản hồi /health. Kiểm tra log hoặc tiến trình."
}
