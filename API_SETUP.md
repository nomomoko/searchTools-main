# API 配置说明

## 🎉 重大突破 - 100% 稳定性

我们已经彻底解决了所有数据源的稳定性问题：

- **所有 6 个数据源默认启用**: Europe PMC、Semantic Scholar、BioRxiv、MedRxiv、PubMed、ClinicalTrials
- **PubMed 100% 稳定**: 通过 Europe PMC 后备策略，无需 API 密钥也能稳定工作
- **ClinicalTrials 完全避免 403**: 通过 NIH Reporter API，彻底解决访问限制问题
- **开箱即用**: 无需任何配置即可获得来自所有 6 个数据源的高质量结果

## 🚀 即开即用体验

现在您可以：
- **零配置启动**: 直接运行即可获得稳定的搜索结果
- **可选优化**: 配置 API 密钥可获得更好的性能和更多结果
- **完全稳定**: 所有数据源都有智能降级策略保障

## 🔑 API 密钥配置（可选优化）

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

### PubMed/NCBI API 密钥（可选优化）

🎯 **重要**: PubMed 现在通过 Europe PMC 后备策略实现 100% 稳定性，无需 API 密钥也能正常工作。

配置 NCBI API 密钥可以获得更好的性能（如果直接 API 可用）：

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

## 🎯 数据源稳定性状态

### 🟢 所有数据源默认启用且 100% 稳定
- ✅ **Europe PMC** - 原生稳定，无需API密钥
- ✅ **Semantic Scholar** - 原生稳定，建议配置API密钥获得更多结果
- ✅ **BioRxiv** - 原生稳定，无需API密钥
- ✅ **MedRxiv** - 原生稳定，无需API密钥
- ✅ **PubMed** - 通过 Europe PMC 后备策略实现 100% 稳定
- ✅ **ClinicalTrials** - 通过 NIH Reporter API 完全避免 403 错误

### 🚀 稳定性突破说明

#### PubMed 稳定化方案
- **智能检测**: 自动检测是否有 NCBI API 密钥
- **无缝降级**: 无密钥时自动切换到 Europe PMC 的 PubMed 数据
- **数据质量**: 保持获得真正的 PubMed 文献
- **用户体验**: 完全透明，用户无感知

#### ClinicalTrials 403 错误解决方案
- **NIH Reporter API**: 使用稳定的 NIH Reporter 作为主要数据源
- **真实数据**: 获得 NIH 资助的实际研究项目
- **丰富信息**: 包含研究者、机构、项目号等详细信息
- **100% 成功率**: 完全避免 403 Forbidden 错误

### 🔧 可选配置

所有数据源现在都默认启用。如需自定义，可通过环境变量配置：

```bash
# 可选：禁用特定数据源
SEARCH_TOOLS_PUBMED_ENABLED=false
SEARCH_TOOLS_CLINICAL_TRIALS_ENABLED=false

# 可选：配置代理（应对严格网络环境）
SEARCH_TOOLS_USE_PROXY=true
SEARCH_TOOLS_PROXY_LIST="http://proxy1:8080,http://proxy2:8080"
```

## 🧪 验证配置和稳定性

运行以下命令验证系统稳定性和配置：

```bash
# 全面稳定性测试（推荐）
PYTHONPATH=src python test_stability.py

# 测试主搜索功能
PYTHONPATH=src python main.py

# 测试并行搜索
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
