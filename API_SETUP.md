# API 配置说明

## Semantic Scholar API 密钥配置

为了使用 Semantic Scholar 搜索功能，您需要配置 API 密钥。

### 方法1：使用 .env 文件（推荐）

1. 在项目根目录创建 `.env` 文件：
```bash
SEMANTIC_SCHOLAR_API_KEY=您的API密钥
```

2. 确保安装了 python-dotenv：
```bash
pip install python-dotenv
```

### 方法2：设置环境变量

```bash
export SEMANTIC_SCHOLAR_API_KEY=您的API密钥
```

### 方法3：在代码中直接设置

在 `src/searchtools/searchAPIchoose/semantic.py` 文件的第103行，您可以直接设置：
```python
MY_API_KEY = "您的API密钥"
```

## 获取 Semantic Scholar API 密钥

1. 访问 [Semantic Scholar API](https://www.semanticscholar.org/product/api)
2. 注册账户并申请 API 密钥
3. 将密钥配置到项目中

## 验证配置

运行以下命令验证配置是否成功：

```bash
# 测试 Semantic Scholar 搜索
PYTHONPATH=src python test_semantic_search.py

# 测试并行搜索（包含 Semantic Scholar）
PYTHONPATH=src python test_parallel_search.py

# 测试异步搜索管理器
PYTHONPATH=src python test_async_search_manager.py
```

如果配置成功，您应该能看到来自 Semantic Scholar 的搜索结果。

## 注意事项

- API 密钥是敏感信息，请不要将其提交到版本控制系统
- `.env` 文件已添加到 `.gitignore` 中
- 如果没有配置 API 密钥，系统仍然可以使用其他数据源（EPMC、BioRxiv、MedRxiv）
