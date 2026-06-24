# 运行此脚本来设置每3天备份一次数据库
# 需要以管理员身份运行

$ProjectDir = "C:\Users\K1457\Downloads\Compressed\my_site_prod-master"
$ScriptPath = Join-Path $ProjectDir "backup_db.sh"
$TaskName = "my_site_db_backup"
$TaskDescription = "Backup my_site database every 3 days"

# 创建任务触发器：每3天执行一次
$trigger = New-ScheduledTaskTrigger -At 2:00AM -RepetitionInterval (New-TimeSpan -Days 3) -RepetitionDuration (New-TimeSpan -Days 365)

# 创建任务动作：运行bash脚本
$action = New-ScheduledTaskAction -Execute "bash.exe" -Argument "-c `"cd '$ProjectDir' && bash backup_db.sh`""

# 创建任务
Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Description $TaskDescription -Force

Write-Host "✓ 定时备份任务已创建"
Write-Host "  任务名: $TaskName"
Write-Host "  执行时间: 每3天凌晨2点"
Write-Host "  备份位置: $ProjectDir\backups\db\"
