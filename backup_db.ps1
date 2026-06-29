$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\K1457\Downloads\Compressed\my_site_prod-master"
$BackupDir = Join-Path $ProjectRoot "backups\db"
$LogDir = Join-Path $ProjectRoot "logs"
$TaskLog = Join-Path $LogDir "backup_task.log"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

function Write-TaskLog {
    param([string]$Message)
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Add-Content -LiteralPath $TaskLog -Value $line
    Write-Host $line
}

try {
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $BackupFile = Join-Path $BackupDir "my_site_db_$Timestamp.sql"

    Write-TaskLog "开始备份数据库到 $BackupFile ..."

    $dump = docker compose -f (Join-Path $ProjectRoot "docker-compose.yml") exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' 2>&1

    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($dump)) {
        if (Test-Path $BackupFile) {
            Remove-Item -LiteralPath $BackupFile -Force
        }
        throw "数据库备份失败。docker 输出: $dump"
    }

    [System.IO.File]::WriteAllText($BackupFile, $dump, [System.Text.Encoding]::UTF8)
    $fileInfo = Get-Item -LiteralPath $BackupFile

    if ($fileInfo.Length -le 0) {
        Remove-Item -LiteralPath $BackupFile -Force
        throw "数据库备份失败，输出为空。"
    }

    Get-ChildItem -LiteralPath $BackupDir -Filter *.sql |
        Sort-Object LastWriteTime -Descending |
        Select-Object -Skip 7 |
        Remove-Item -Force

    Write-TaskLog "备份成功: $BackupFile ($($fileInfo.Length) bytes)"
}
catch {
    Write-TaskLog "备份失败: $($_.Exception.Message)"
    exit 1
}
