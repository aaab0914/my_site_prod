# 使用官方 Python 3.12 精简版镜像
FROM python:3.12-slim

# 设置环境变量，优化 Python 和 pip 行为
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=my_site.settings \
    PIP_NO_CACHE_DIR=1

# 设置工作目录
WORKDIR /code

# 创建非 root 用户 'app'，提升安全性
RUN addgroup --system app && adduser --system --ingroup app app

# 复制依赖文件并安装（利用 Docker 缓存层，加快后续构建）
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 复制项目代码到容器内
COPY . .

# 创建静态文件和媒体文件目录，并赋予 app 用户权限
RUN mkdir -p /code/staticfiles /code/media && \
    chown -R app:app /code

# 复制启动脚本并赋予执行权限
COPY entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

# 切换到非 root 用户运行应用
USER app

# 暴露 Gunicorn 端口
EXPOSE 8000

# 使用启动脚本作为容器入口点
ENTRYPOINT ["/code/entrypoint.sh"]