$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\K1457\Downloads\Compressed\my_site_prod-master"
$BackupDir = Join-Path $ProjectRoot "backups\db"
$DrillDbName = "my_site_restore_drill"
$ComposeFile = Join-Path $ProjectRoot "docker-compose.yml"

function Write-Step {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

if (-not (Test-Path $BackupDir)) {
    throw "备份目录不存在: $BackupDir"
}

$LatestBackup = Get-ChildItem -LiteralPath $BackupDir -Filter *.sql |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $LatestBackup) {
    throw "No .sql backup file was found for the restore drill."
}

Write-Step "Using backup file: $($LatestBackup.FullName)"
Write-Step "Dropping previous restore-drill database if it exists"
docker compose -f $ComposeFile exec -T db sh -lc "export PGPASSWORD=`"$POSTGRES_PASSWORD`"; dropdb -U `"$POSTGRES_USER`" --if-exists $DrillDbName" | Out-Null

Write-Step "Creating restore-drill database"
docker compose -f $ComposeFile exec -T db sh -lc "export PGPASSWORD=`"$POSTGRES_PASSWORD`"; createdb -U `"$POSTGRES_USER`" $DrillDbName" | Out-Null

Write-Step "Restoring backup into restore-drill database"
Get-Content -LiteralPath $LatestBackup.FullName | docker compose -f $ComposeFile exec -T db sh -lc "export PGPASSWORD=`"$POSTGRES_PASSWORD`"; psql -U `"$POSTGRES_USER`" -d $DrillDbName" | Out-Null

Write-Step "Verifying restored tables exist"
$tables = docker compose -f $ComposeFile exec -T db sh -lc "export PGPASSWORD=`"$POSTGRES_PASSWORD`"; psql -U `"$POSTGRES_USER`" -d $DrillDbName -t -c '\dt'" 2>&1

if ([string]::IsNullOrWhiteSpace($tables)) {
    throw "Restore drill failed: no tables were listed."
}

Write-Step "Restore drill succeeded and listed tables from the restored database"
Write-Step "Dropping restore-drill database"
docker compose -f $ComposeFile exec -T db sh -lc "export PGPASSWORD=`"$POSTGRES_PASSWORD`"; dropdb -U `"$POSTGRES_USER`" --if-exists $DrillDbName" | Out-Null

Write-Step "Restore drill completed"
