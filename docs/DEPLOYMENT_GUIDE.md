# 🚀 部署和运行指南

## 概述

本指南详细介绍了SearchTools项目的部署、运行和维护方法，适用于开发、测试和生产环境。

## 📋 系统要求

### 最低要求
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.10+
- **内存**: 4GB RAM
- **存储**: 1GB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **内存**: 8GB+ RAM
- **CPU**: 4核心+
- **网络**: 100Mbps+ 带宽
- **存储**: SSD硬盘

## 🛠️ 安装部署

### 1. 环境准备

#### Python环境
```bash
# 检查Python版本
python --version  # 应该 >= 3.10

# 创建虚拟环境（推荐）
python -m venv searchtools_env

# 激活虚拟环境
# Windows:
searchtools_env\Scripts\activate
# Linux/Mac:
source searchtools_env/bin/activate
```

#### 项目下载
```bash
# 方式1: Git克隆
git clone https://github.com/nomomoko/searchTools-main.git
cd searchTools-main

# 方式2: 下载ZIP
# 从GitHub下载ZIP文件并解压
```

### 2. 依赖安装

#### 基础依赖
```bash
# 安装项目依赖
pip install -e .

# 安装高级算法依赖
pip install numpy

# 验证安装
python -c "import searchtools; print('安装成功')"
```

#### 可选依赖
```bash
# 性能监控
pip install psutil

# 开发工具
pip install pytest black flake8

# 生产部署
pip install gunicorn
```

### 3. 配置设置

#### 环境变量配置
```bash
# 创建 .env 文件
cat > .env << EOF
# API密钥
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here

# 搜索配置
SEARCH_TOOLS_MAX_CONCURRENT_REQUESTS=5
SEARCH_TOOLS_DEFAULT_TIMEOUT=30.0

# 重排序配置
SEARCH_TOOLS_ENABLE_RERANK=true
SEARCH_TOOLS_ALGORITHM_MODE=hybrid
SEARCH_TOOLS_ENABLE_CACHING=true
SEARCH_TOOLS_CACHE_SIZE=1000

# 权重配置
SEARCH_TOOLS_RERANK_RELEVANCE_WEIGHT=0.40
SEARCH_TOOLS_RERANK_AUTHORITY_WEIGHT=0.30
SEARCH_TOOLS_RERANK_RECENCY_WEIGHT=0.20
SEARCH_TOOLS_RERANK_QUALITY_WEIGHT=0.10

# 日志配置
SEARCH_TOOLS_LOG_LEVEL=INFO
SEARCH_TOOLS_LOG_TO_FILE=false
EOF
```

#### 代理配置（可选）
```bash
# 如果需要代理访问
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

## 🎯 运行方式

### 1. 开发模式

#### 直接运行
```bash
# 启动Web服务
python app.py

# 访问地址: http://localhost:8000
```

#### 调试模式
```bash
# 启用详细日志
export SEARCH_TOOLS_LOG_LEVEL=DEBUG
python app.py
```

### 2. 生产模式

#### 使用uvicorn
```bash
# 单进程
uvicorn app:app --host 0.0.0.0 --port 8000

# 多进程（推荐）
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 使用gunicorn
```bash
# 安装gunicorn
pip install gunicorn

# 启动服务
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. 容器化部署

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install -e . && pip install numpy gunicorn

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  searchtools:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SEARCH_TOOLS_ENABLE_RERANK=true
      - SEARCH_TOOLS_CACHE_SIZE=2000
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - searchtools
    restart: unless-stopped
```

## 🔧 配置优化

### 性能调优

#### 内存优化
```bash
# 调整缓存大小
export SEARCH_TOOLS_CACHE_SIZE=2000  # 根据内存调整

# 启用缓存
export SEARCH_TOOLS_ENABLE_CACHING=true
```

#### 并发优化
```bash
# 调整并发请求数
export SEARCH_TOOLS_MAX_CONCURRENT_REQUESTS=8  # 根据网络调整

# 调整超时时间
export SEARCH_TOOLS_DEFAULT_TIMEOUT=45.0
```

#### 算法优化
```bash
# 选择算法模式
export SEARCH_TOOLS_ALGORITHM_MODE=traditional  # 最快
export SEARCH_TOOLS_ALGORITHM_MODE=hybrid       # 平衡（推荐）
export SEARCH_TOOLS_ALGORITHM_MODE=ml_only      # 最准确
```

### 负载均衡配置

#### Nginx配置
```nginx
upstream searchtools {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://searchtools;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 60s;
        proxy_read_timeout 300s;
    }
}
```

## 📊 监控和维护

### 健康检查
```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查API功能
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "test", "max_results": 1}'
```

### 日志管理
```bash
# 启用文件日志
export SEARCH_TOOLS_LOG_TO_FILE=true
export SEARCH_TOOLS_LOG_FILE_PATH=/var/log/searchtools.log

# 日志轮转（logrotate配置）
cat > /etc/logrotate.d/searchtools << EOF
/var/log/searchtools.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
}
EOF
```

### 性能监控
```python
# 监控脚本示例
import requests
import time
import psutil

def monitor_performance():
    # API响应时间
    start = time.time()
    response = requests.post('http://localhost:8000/search', 
                           json={'query': 'test', 'max_results': 5})
    api_time = time.time() - start
    
    # 系统资源
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    
    print(f"API响应时间: {api_time:.2f}s")
    print(f"CPU使用率: {cpu_percent}%")
    print(f"内存使用率: {memory_percent}%")

if __name__ == "__main__":
    monitor_performance()
```

## 🚨 故障排除

### 常见问题

#### 1. 依赖安装失败
```bash
# 升级pip
pip install --upgrade pip

# 清理缓存
pip cache purge

# 重新安装
pip install -e . --force-reinstall
```

#### 2. 内存不足
```bash
# 减少缓存大小
export SEARCH_TOOLS_CACHE_SIZE=500

# 使用traditional模式
export SEARCH_TOOLS_ALGORITHM_MODE=traditional
```

#### 3. 网络超时
```bash
# 增加超时时间
export SEARCH_TOOLS_DEFAULT_TIMEOUT=60.0

# 减少并发数
export SEARCH_TOOLS_MAX_CONCURRENT_REQUESTS=3
```

#### 4. API密钥问题
```bash
# 检查密钥设置
echo $SEMANTIC_SCHOLAR_API_KEY

# 测试API访问
curl "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1"
```

### 调试技巧
```bash
# 启用详细日志
export SEARCH_TOOLS_LOG_LEVEL=DEBUG

# 运行测试
python test_rerank.py

# 检查配置
python -c "from searchtools.search_config import get_config; print(get_config())"
```

## 🔄 更新升级

### 代码更新
```bash
# 拉取最新代码
git pull origin main

# 重新安装依赖
pip install -e . --upgrade

# 重启服务
# 根据部署方式重启
```

### 数据迁移
```bash
# 清理缓存（如果需要）
python -c "
from searchtools.rerank_engine import get_rerank_engine
engine = get_rerank_engine()
engine.clear_cache()
print('缓存已清理')
"
```

---

*SearchTools 部署指南 - 让部署变得简单可靠！*
