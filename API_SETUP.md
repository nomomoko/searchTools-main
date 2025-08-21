# API 配置说明

## 🔑 API 密钥配置

### Semantic Scholar API 密钥（推荐配置）

为了使用 Semantic Scholar 搜索功能，您需要配置 API 密钥。

#### 方法1：使用 .env 文件（推荐）

1. 在项目根目录创建 `.env` 文件：
```bash
SEMANTIC_SCHOLAR_API_KEY=您的API密钥
```

2. 确保安装了 python-dotenv：
```bash
pip install python-dotenv
```

#### 方法2：设置环境变量

```bash
export SEMANTIC_SCHOLAR_API_KEY=您的API密钥
```

### PubMed/NCBI API 密钥（可选）

NCBI现在推荐使用API密钥以获得更高的请求限制。

```bash
# 在 .env 文件中添加
NCBI_API_KEY=您的NCBI_API密钥
# 或者
PUBMED_API_KEY=您的NCBI_API密钥
```

## 🌐 获取 API 密钥

### Semantic Scholar
1. 访问 [Semantic Scholar API](https://www.semanticscholar.org/product/api)
2. 注册账户并申请 API 密钥
3. 将密钥配置到项目中

### NCBI/PubMed
1. 访问 [NCBI API Keys](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/)
2. 创建NCBI账户并生成API密钥
3. 配置到环境变量中

## 🔧 数据源配置策略

### 默认启用的稳定数据源
- ✅ **Europe PMC** - 高稳定性，无需API密钥
- ✅ **Semantic Scholar** - 需要API密钥，但非常稳定
- ✅ **BioRxiv** - 高稳定性，无需API密钥
- ✅ **MedRxiv** - 高稳定性，无需API密钥

### 默认禁用的数据源（可手动启用）
- ⚠️ **PubMed** - 需要API密钥，否则会降级到Europe PMC
- ⚠️ **ClinicalTrials** - 可能有IP限制，不够稳定

### 启用额外数据源

如果您想启用PubMed和ClinicalTrials，可以通过环境变量配置：

```bash
# 在 .env 文件中添加
SEARCH_TOOLS_PUBMED_ENABLED=true
SEARCH_TOOLS_CLINICAL_TRIALS_ENABLED=true
```

## 🧪 验证配置

运行以下命令验证配置是否成功：

```bash
# 测试 Semantic Scholar 搜索
PYTHONPATH=src python test_semantic_search.py

# 测试并行搜索（包含 Semantic Scholar）
PYTHONPATH=src python test_parallel_search.py

# 测试异步搜索管理器
PYTHONPATH=src python test_async_search_manager.py

# 测试稳定性（包括PubMed和ClinicalTrials）
PYTHONPATH=src python test_stability.py
```

## 📋 配置示例

完整的 `.env` 文件示例：

```bash
# 必需的API密钥
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_api_key

# 可选的API密钥
NCBI_API_KEY=your_ncbi_api_key

# 可选的数据源启用
SEARCH_TOOLS_PUBMED_ENABLED=true
SEARCH_TOOLS_CLINICAL_TRIALS_ENABLED=false

# 可选的性能调优
SEARCH_TOOLS_MAX_CONCURRENT_REQUESTS=5
SEARCH_TOOLS_SEMANTIC_SCHOLAR_MAX_RESULTS=10
```

## ⚠️ 注意事项

- **安全性**: API 密钥是敏感信息，请不要将其提交到版本控制系统
- **降级策略**: 如果某个数据源不可用，系统会自动使用其他可用的数据源
- **性能**: 默认配置优先考虑稳定性，如需更多数据源可手动启用
- **监控**: 建议在生产环境中监控各数据源的成功率
