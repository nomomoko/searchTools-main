# SearchTools - 学术搜索工具包

一个强大的多源学术文献搜索工具，支持异步并行搜索和智能去重。

## 🌟 特性

- **多数据源搜索**: 支持 Europe PMC、BioRxiv、MedRxiv、Semantic Scholar
- **异步并行处理**: 高效的异步搜索，大幅提升性能
- **智能去重**: 基于 DOI、PMID、NCTID、标题+作者的多层级去重
- **Web 界面**: 完整的 Web 用户界面，支持实时搜索
- **RESTful API**: 提供 API 接口，支持程序化调用
- **高质量结果**: 整合多个权威学术数据库的结果

## 🚀 快速开始

### 安装依赖

```bash
pip install -e .
```

或者使用 requirements.txt：

```bash
pip install -r requirements.txt
```

### API 配置

为了使用 Semantic Scholar 搜索功能，需要配置 API 密钥。详细说明请参考 [API_SETUP.md](API_SETUP.md)。

### 运行示例

#### 1. 命令行搜索

```bash
PYTHONPATH=src python main.py
```

#### 2. 启动 Web 服务

```bash
PYTHONPATH=src python app.py
```

然后访问 http://localhost:8000

#### 3. 运行测试

```bash
# 测试基本搜索功能
PYTHONPATH=src python test.py

# 测试 Semantic Scholar
PYTHONPATH=src python test_semantic_search.py

# 测试并行搜索
PYTHONPATH=src python test_parallel_search.py

# 测试异步搜索管理器
PYTHONPATH=src python test_async_search_manager.py
```

## 📖 使用方法

### Python API

```python
import asyncio
from searchtools.async_parallel_search_manager import AsyncParallelSearchManager

async def search_papers():
    search_manager = AsyncParallelSearchManager()

    # 执行搜索
    results = await search_manager.search_all_sources("cancer immunotherapy")

    # 去重
    deduplicated_results, stats = search_manager.deduplicate_results(results)

    print(f"找到 {len(deduplicated_results)} 篇论文")
    for paper in deduplicated_results[:5]:
        print(f"- {paper.title}")

# 运行搜索
asyncio.run(search_papers())
```

### Web API

```bash
# 搜索请求
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "machine learning", "max_results": 10}'
```

## 🏗️ 项目结构

```
searchTools-main/
├── src/searchtools/           # 核心搜索工具包
│   ├── searchAPIchoose/       # 各数据源 API 封装
│   ├── async_parallel_search_manager.py  # 异步搜索管理器
│   ├── search_config.py       # 配置管理
│   └── ...
├── app.py                     # FastAPI Web 应用
├── main.py                    # 命令行示例
├── test_*.py                  # 测试文件
├── API_SETUP.md              # API 配置说明
└── README.md                 # 项目说明
```

## 🔧 配置选项

系统支持通过环境变量进行配置：

```bash
# Semantic Scholar API 密钥
SEMANTIC_SCHOLAR_API_KEY=your_api_key

# 搜索配置
SEARCH_TOOLS_MAX_CONCURRENT_REQUESTS=5
SEARCH_TOOLS_SEMANTIC_SCHOLAR_MAX_RESULTS=10
```

## 📊 支持的数据源

| 数据源 | 描述 | 状态 |
|--------|------|------|
| Europe PMC | 欧洲生物医学文献数据库 | ✅ 启用 |
| Semantic Scholar | AI 驱动的学术搜索引擎 | ✅ 启用 |
| BioRxiv | 生物学预印本服务器 | ✅ 启用 |
| MedRxiv | 医学预印本服务器 | ✅ 启用 |
| PubMed | 美国国立医学图书馆数据库 | ⚠️ 可选 |
| Clinical Trials | 临床试验数据库 | ⚠️ 可选 |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。