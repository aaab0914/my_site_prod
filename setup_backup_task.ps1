# 运行此脚本来设置每3天备份一次数据库

$ProjectDir = "C:\Users\K1457\Downloads\Compressed\my_site_prod-master"
$ScriptPath = Join-Path $ProjectDir "backup_db.ps1"
$TaskName = "my_site_db_backup"
$TaskDescription = "Backup my_site database every 3 days"

# 创建任务触发器：从下一个凌晨2点开始，每3天执行一次
$startTime = (Get-Date).Date.AddDays(1).AddHours(2)
$trigger = New-ScheduledTaskTrigger -Once -At $startTime `
    -RepetitionInterval (New-TimeSpan -Days 3) `
    -RepetitionDuration (New-TimeSpan -Days 365)

# 创建任务动作：运行 PowerShell 备份脚本
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

# 创建任务
Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Description $TaskDescription -Force | Out-Null

Write-Host "✓ 定时备份任务已创建"
Write-Host "  任务名: $TaskName"
Write-Host "  执行时间: 每3天凌晨2点"
Write-Host "  执行脚本: $ScriptPath"
Write-Host "  备份位置: $ProjectDir\backups\db\"
