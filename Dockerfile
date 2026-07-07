# 使用官方 Python 3.12 精简版镜像
FROM python:3.12-slim

# 设置环境变量，优化 Python 和 pip 行为
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=my_site.settings.prod \
    PIP_NO_CACHE_DIR=1

# 设置工作目录
WORKDIR /code

# 创建非 root 用户 'app'，提升安全性
RUN addgroup --system app && adduser --system --ingroup app app

# 复制依赖清单
COPY requirements.txt /tmp/requirements.txt

# ✅ 纯在线安装：直接从 PyPI 下载并安装所有依赖
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# 复制项目代码到容器内
COPY . .

# 创建静态文件、媒体文件和日志目录，并赋予 app 用户权限
RUN mkdir -p /code/staticfiles /code/media /code/logs && \
    chown -R app:app /code && \
    chmod -R 755 /code/media /code/logs

# 将入口脚本复制到不受 /code 绑定挂载影响的位置
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 暴露 Gunicorn 端口
EXPOSE 8000

# 使用 shell 显式执行入口脚本，避免宿主机执行位差异导致权限错误
ENTRYPOINT ["sh", "/usr/local/bin/entrypoint.sh"]