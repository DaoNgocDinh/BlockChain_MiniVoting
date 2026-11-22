# Script dừng an toàn 4 validator nodes của MiniVoting
# Kiểm tra chặt chẽ PID và đường dẫn repo, không kill tiến trình ngoài repo.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $projectRoot '.run'
$pidsFile = Join-Path $runDir 'nodes.json'
$pythonPath = (Join-Path $projectRoot '.venv\Scripts\python.exe').ToLower()

if (-not (Test-Path -LiteralPath $pidsFile)) {
    Write-Host "Không tìm thấy file .run/nodes.json. Không có thông tin tiến trình nào để dừng." -ForegroundColor Yellow
    exit 0
}

try {
    $runtimeInfo = Get-Content -LiteralPath $pidsFile -Raw | ConvertFrom-Json
} catch {
    Write-Error "Không thể đọc .run/nodes.json: $_"
    exit 1
}

Write-Host "Đang kiểm tra và dừng các tiến trình MiniVoting..." -ForegroundColor Cyan

$stoppedCount = 0

foreach ($node in $runtimeInfo.nodes) {
    $pidToStop = [int]$node.pid
    $proc = Get-Process -Id $pidToStop -ErrorAction SilentlyContinue

    if ($null -eq $proc) {
        Write-Host "  -> $($node.id) (PID: $pidToStop) đã dừng từ trước." -ForegroundColor Gray
        continue
    }

    # BẢO VỆ AN TOÀN: Xác minh tiến trình thuộc về repo này trước khi dừng
    $isSafeToKill = $false
    try {
        $procPath = $proc.MainModule.FileName.ToLower()
        if ($procPath -eq $pythonPath -or $procPath.Contains("blockchain_minivoting")) {
            $isSafeToKill = $true
        }
    } catch {
        # Nếu không truy cập được MainModule, kiểm tra WMI Commandline
        try {
            $wmi = Get-CimInstance Win32_Process -Filter "ProcessId = $pidToStop"
            if ($wmi.CommandLine -like "*src.api.app:app*" -or $wmi.CommandLine -like "*BlockChain_MiniVoting*") {
                $isSafeToKill = $true
            }
        } catch {}
    }

    if ($isSafeToKill) {
        Write-Host "  -> Đang dừng $($node.id) (PID: $pidToStop)..." -ForegroundColor Yellow
        $proc.Kill()
        $null = $proc.WaitForExit(3000)
        $stoppedCount++
    } else {
        Write-Warning "CẢNH BÁO: PID $pidToStop không khớp với môi trường của MiniVoting! Bỏ qua để không kill nhầm tiến trình ngoài repo."
    }
}

# Xóa file runtime sau khi đã dừng
Remove-Item -LiteralPath $pidsFile -Force -ErrorAction SilentlyContinue

Write-Host "`nĐã dừng thành công $stoppedCount tiến trình node MiniVoting." -ForegroundColor Green
