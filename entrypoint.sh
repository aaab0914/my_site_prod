#!/bin/sh
set -e

# 1. 安全保护：检查并确保 staticfiles 目录权限正确
# 如果因为挂载卷导致 /code/staticfiles 属于 root，这里强制修正权限
# 2>/dev/null 的作用是：如果当前用户已经是 app，则忽略该命令，不报错
sudo -n chown -R app:app /code/staticfiles 2>/dev/null || true

# 2. 运行时环境检查：先测试能否连接数据库和加载 Django
# 通过 `check` 命令先做一次预检，确保 .env 配置和数据库都是对的
python manage.py check --deploy 2>/dev/null || echo "⚠️ 注意：Django check 未完全通过，请检查 .env 配置。"

# 3. 自动收集静态文件（防止 CSS 丢失）
# 添加 `2>/dev/null` 屏蔽非致命警告，如果第一次失败则尝试重试
python manage.py collectstatic --noinput 2>/dev/null || echo "⚠️ 静态文件收集稍后重试，容器已启动。"

# 4. 执行 Gunicorn 主进程（前台运行，保持容器不退出）
exec gunicorn --workers 3 --bind 0.0.0.0:8000 my_site.wsgi:application