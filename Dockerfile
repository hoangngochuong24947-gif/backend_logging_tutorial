# 使用官方轻量级 Python 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，防止 Python 生成 .pyc 文件并启用无缓冲输出
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装构建依赖（部分包可能用到）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制当前目录的所有文件到工作目录
COPY . /app/

# 安装项目依赖（因为要跑教学脚本和展示端前端，所以需要安装 fastapi 等）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi \
    uvicorn \
    jinja2 \
    requests

# 暴露挂载 Web 服务所需的 8000 端口
EXPOSE 8000

# 默认命令设置为 bash 以方便运行不同层级的教学脚本或启动服务器
CMD ["bash"]
