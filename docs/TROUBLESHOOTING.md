# 🚨 故障排除指南

本指南提供了SearchTools项目常见问题的详细解决方案，帮助您快速诊断和解决各种技术问题。

## 📋 问题分类

### 🌐 Web界面问题
### 🔧 服务器问题  
### 📦 依赖和安装问题
### 🌍 网络和API问题
### 💾 性能和内存问题

---

## 🌐 Web界面问题

### 问题1: JavaScript错误 "Cannot read properties of undefined"

#### 症状
- 浏览器控制台显示JavaScript错误
- 搜索结果无法正常显示
- 统计信息显示异常

#### 原因分析
- 前端代码期望的API响应字段与实际返回字段不匹配
- API响应数据结构发生变化

#### 解决方案
```bash
# 1. 确保使用最新版本
git pull origin main

# 2. 重新启动服务
python app.py

# 3. 清除浏览器缓存
# Chrome: Ctrl+Shift+R (强制刷新)
# Firefox: Ctrl+F5
```

#### 验证修复
1. 打开浏览器开发者工具 (F12)
2. 访问 http://localhost:8000
3. 进行搜索测试
4. 检查控制台是否还有错误

### 问题2: 搜索按钮无响应

#### 症状
- 点击搜索按钮没有反应
- 没有显示"正在搜索中"状态

#### 解决方案
```bash
# 检查服务器是否运行
curl http://localhost:8000/

# 如果无响应，重新启动服务
python app.py
```

### 问题3: 搜索结果显示不完整

#### 症状
- 部分字段显示为"undefined"或"N/A"
- 缺少作者、期刊等信息

#### 解决方案
这通常是正常现象，因为不同数据源提供的字段完整性不同。可以：
1. 尝试不同的搜索关键词
2. 检查原始数据源是否提供完整信息

---

## 🔧 服务器问题

### 问题1: 500 Internal Server Error

#### 症状
- API请求返回500错误
- Web界面显示"搜索失败，请重试"

#### 原因分析
- Python模块导入失败
- 依赖包缺失或版本不兼容
- 代码逻辑错误

#### 解决方案
```bash
# 1. 检查Python路径设置
export PYTHONPATH=src  # Linux/Mac
$env:PYTHONPATH = "src"  # Windows PowerShell

# 2. 重新安装依赖
pip install -e .
pip install numpy

# 3. 测试模块导入
python -c "
import sys
sys.path.insert(0, 'src')
from searchtools.async_parallel_search_manager import AsyncParallelSearchManager
print('导入成功')
"

# 4. 重新启动服务
python app.py
```

#### 调试技巧
```bash
# 启用详细日志
export SEARCH_TOOLS_LOG_LEVEL=DEBUG
python app.py

# 查看详细错误信息
python -c "
import sys
sys.path.insert(0, 'src')
try:
    from app import app
    print('App导入成功')
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()
"
```

### 问题2: 端口占用错误

#### 症状
- 启动时提示"Address already in use"
- 无法绑定到8000端口

#### 解决方案
```bash
# 查找占用端口的进程
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# 终止占用进程
taskkill /PID <PID> /F  # Windows
kill -9 <PID>  # Linux/Mac

# 或使用不同端口
python -c "
import uvicorn
from app import app
uvicorn.run(app, host='0.0.0.0', port=8001)
"
```

### 问题3: 服务启动后无响应

#### 症状
- 服务启动成功但无法访问
- 浏览器显示"无法连接"

#### 解决方案
```bash
# 1. 检查防火墙设置
# Windows: 允许Python通过防火墙
# Linux: sudo ufw allow 8000

# 2. 检查绑定地址
# 确保使用 0.0.0.0 而不是 127.0.0.1
python -c "
import uvicorn
from app import app
uvicorn.run(app, host='0.0.0.0', port=8000)
"

# 3. 测试本地连接
curl http://localhost:8000/
curl http://127.0.0.1:8000/
```

---

## 📦 依赖和安装问题

### 问题1: ModuleNotFoundError

#### 症状
```
ModuleNotFoundError: No module named 'searchtools'
```

#### 解决方案
```bash
# 方法1: 设置Python路径
export PYTHONPATH=src
python app.py

# 方法2: 重新安装项目
pip install -e .

# 方法3: 直接指定路径
python -c "
import sys
sys.path.insert(0, 'src')
from app import app
"
```

### 问题2: NumPy导入错误

#### 症状
```
ModuleNotFoundError: No module named 'numpy'
```

#### 解决方案
```bash
# 安装NumPy
pip install numpy

# 如果安装失败，尝试升级pip
pip install --upgrade pip
pip install numpy

# 验证安装
python -c "import numpy; print('NumPy版本:', numpy.__version__)"
```

### 问题3: 依赖版本冲突

#### 症状
- 安装时出现版本冲突警告
- 运行时出现兼容性错误

#### 解决方案
```bash
# 创建虚拟环境
python -m venv searchtools_env

# 激活虚拟环境
# Windows:
searchtools_env\Scripts\activate
# Linux/Mac:
source searchtools_env/bin/activate

# 重新安装依赖
pip install -e .
pip install numpy
```

---

## 🌍 网络和API问题

### 问题1: 搜索超时

#### 症状
- 搜索长时间无响应
- 最终返回超时错误

#### 解决方案
```bash
# 增加超时时间
export SEARCH_TOOLS_DEFAULT_TIMEOUT=60

# 减少并发请求数
export SEARCH_TOOLS_MAX_CONCURRENT_REQUESTS=3

# 测试网络连接
curl -I https://api.semanticscholar.org
curl -I https://www.ebi.ac.uk
```

### 问题2: API密钥问题

#### 症状
- Semantic Scholar搜索失败
- 返回认证错误

#### 解决方案
```bash
# 设置API密钥
export SEMANTIC_SCHOLAR_API_KEY=your_api_key

# 验证密钥
curl -H "x-api-key: your_api_key" \
     "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1"
```

### 问题3: 代理配置

#### 症状
- 在企业网络环境下无法访问外部API
- 连接被防火墙阻止

#### 解决方案
```bash
# 配置HTTP代理
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# 配置认证代理
export HTTP_PROXY=http://username:password@proxy.company.com:8080

# 验证代理设置
curl --proxy $HTTP_PROXY -I https://api.semanticscholar.org
```

---

## 💾 性能和内存问题

### 问题1: 内存不足

#### 症状
- 搜索过程中程序崩溃
- 系统内存使用率过高

#### 解决方案
```bash
# 减少并发请求数
export SEARCH_TOOLS_MAX_CONCURRENT_REQUESTS=2

# 减少缓存大小
export SEARCH_TOOLS_CACHE_SIZE=500

# 限制搜索结果数量
# 在API请求中设置较小的max_results值
```

### 问题2: 搜索速度慢

#### 症状
- 搜索耗时过长
- 响应时间超过预期

#### 解决方案
```bash
# 启用缓存
export SEARCH_TOOLS_ENABLE_CACHING=true

# 使用更快的算法模式
export SEARCH_TOOLS_ALGORITHM_MODE=traditional

# 减少搜索的数据源
# 在配置中禁用某些数据源
```

### 问题3: 高并发问题

#### 症状
- 多用户同时使用时性能下降
- 出现连接错误

#### 解决方案
```bash
# 使用生产级服务器
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker

# 配置负载均衡
# 使用nginx等反向代理
```

---

## 🔍 诊断工具

### 系统诊断脚本

创建 `diagnose.py` 文件：
```python
#!/usr/bin/env python3
import sys
import os
import subprocess
import importlib

def check_python_version():
    print(f"Python版本: {sys.version}")
    if sys.version_info < (3, 10):
        print("⚠️ 警告: 推荐使用Python 3.10+")

def check_dependencies():
    deps = ['fastapi', 'uvicorn', 'httpx', 'numpy']
    for dep in deps:
        try:
            mod = importlib.import_module(dep)
            print(f"✅ {dep}: {getattr(mod, '__version__', '已安装')}")
        except ImportError:
            print(f"❌ {dep}: 未安装")

def check_network():
    urls = [
        'https://api.semanticscholar.org',
        'https://www.ebi.ac.uk',
        'https://api.biorxiv.org'
    ]
    for url in urls:
        try:
            result = subprocess.run(['curl', '-I', url], 
                                  capture_output=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {url}: 可访问")
            else:
                print(f"❌ {url}: 无法访问")
        except:
            print(f"❌ {url}: 测试失败")

if __name__ == "__main__":
    print("🔍 SearchTools 系统诊断")
    print("=" * 50)
    check_python_version()
    print()
    check_dependencies()
    print()
    check_network()
```

运行诊断：
```bash
python diagnose.py
```

### 日志分析

启用详细日志并分析：
```bash
# 启用调试日志
export SEARCH_TOOLS_LOG_LEVEL=DEBUG

# 将日志输出到文件
python app.py 2>&1 | tee searchtools.log

# 分析错误
grep -i error searchtools.log
grep -i exception searchtools.log
```

---

## 📞 获取帮助

如果以上解决方案都无法解决您的问题，请：

1. **查看GitHub Issues**: https://github.com/nomomoko/searchTools-main/issues
2. **提交新Issue**: 包含详细的错误信息和环境描述
3. **提供诊断信息**: 运行诊断脚本并提供输出结果

### Issue模板

提交Issue时请包含：
```
**问题描述**
简要描述遇到的问题

**环境信息**
- 操作系统: 
- Python版本: 
- 项目版本: 

**重现步骤**
1. 
2. 
3. 

**错误信息**
```
完整的错误堆栈信息
```

**期望行为**
描述期望的正确行为

**额外信息**
其他可能有用的信息
```

---

*SearchTools 故障排除指南 - 让问题解决变得简单！*
