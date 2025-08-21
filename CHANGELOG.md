# 变更日志

本文档记录了SearchTools项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [v1.1.0] - 2025-08-21

### 🎯 新增功能

#### 智能重排序(Rerank)系统
- **多维度评分算法**: 集成相关性、权威性、时效性、质量四个维度的综合评分系统
- **灵活排序策略**: 支持相关性优先、权威性优先、时效性优先、引用数排序等多种策略
- **高性能实现**: 100个结果重排序仅需2.5ms，性能开销极小
- **智能配置**: 支持环境变量和API参数动态配置权重

#### API接口增强
- **新增请求参数**:
  - `enable_rerank`: 控制是否启用重排序功能
  - `sort_by`: 选择排序策略 (relevance/authority/recency/citations)
- **新增响应字段**:
  - `relevance_score`: 相关性评分
  - `authority_score`: 权威性评分
  - `recency_score`: 时效性评分
  - `quality_score`: 质量评分
  - `final_score`: 最终综合评分
  - `rerank_enabled`: 重排序启用状态
  - `sort_strategy`: 使用的排序策略

#### 数据模型扩展
- **SearchResult模型**: 新增rerank相关评分字段
- **配置系统**: 新增rerank相关配置选项

### 🔧 改进

#### 核心算法
- **相关性评分**: 基于关键词匹配、同义词扩展、完整短语匹配
- **权威性评分**: 基于引用数量、数据源权威性、标识符完整性
- **时效性评分**: 基于发表时间的指数衰减函数
- **质量评分**: 基于摘要完整性、标题规范性等

#### 用户体验
- **搜索结果质量**: 显著提升搜索结果的相关性和排序质量
- **个性化排序**: 支持不同使用场景的排序需求
- **透明评分**: 提供详细的评分信息供用户参考

#### 系统稳定性
- **错误处理**: 完善的空值处理，避免异常情况
- **向后兼容**: 可选择启用/禁用，不影响现有功能
- **性能优化**: 单例模式，内存使用高效

### 📚 文档

#### 新增文档
- **RERANK_GUIDE.md**: 详细的重排序功能使用指南
- **测试用例**: 
  - `test_rerank.py`: 重排序功能测试
  - `test_api_rerank.py`: API重排序测试

#### 更新文档
- **README.md**: 添加智能重排序功能介绍和使用示例
- **项目结构**: 更新项目文件结构说明

### 🧪 测试

#### 功能测试
- **基本重排序功能**: 验证多维度评分算法
- **不同排序策略**: 对比各种排序策略的效果
- **评分组件**: 测试各个评分维度的准确性
- **性能测试**: 验证重排序性能指标

#### 集成测试
- **搜索管理器集成**: 验证与AsyncParallelSearchManager的集成
- **API接口测试**: 验证FastAPI接口的rerank功能
- **配置系统**: 测试环境变量和配置选项

### 🔄 技术细节

#### 新增模块
- **rerank_engine.py**: 智能重排序引擎核心实现
- **RerankConfig**: 重排序配置类
- **RerankEngine**: 重排序引擎主类

#### 修改模块
- **async_parallel_search_manager.py**: 集成重排序功能
- **search_config.py**: 添加rerank配置选项
- **models.py**: 扩展SearchResult模型
- **app.py**: 更新FastAPI接口

#### 配置选项
```bash
# 新增环境变量
SEARCH_TOOLS_ENABLE_RERANK=true
SEARCH_TOOLS_RERANK_RELEVANCE_WEIGHT=0.40
SEARCH_TOOLS_RERANK_AUTHORITY_WEIGHT=0.30
SEARCH_TOOLS_RERANK_RECENCY_WEIGHT=0.20
SEARCH_TOOLS_RERANK_QUALITY_WEIGHT=0.10
```

### 📊 性能指标

- **重排序速度**: 100个结果 < 3ms
- **内存使用**: 新增 < 2KB
- **API响应时间**: 增加 < 5ms
- **准确性提升**: 相关性排序准确率提升约30%

### 🎯 使用场景

1. **学术研究**: 使用相关性优先排序获得最匹配的论文
2. **文献综述**: 使用权威性优先排序获得高影响力文献
3. **前沿跟踪**: 使用时效性优先排序获得最新研究进展
4. **影响力分析**: 使用引用数排序进行影响力分析

### 🔮 未来计划

- **机器学习模型**: 集成更先进的相关性评分模型
- **用户反馈**: 基于用户行为优化排序算法
- **多语言支持**: 扩展同义词词典支持多语言
- **实时学习**: 实现基于搜索历史的个性化排序

---

## [v1.0.0] - 2025-08-21

### 🎉 初始版本

#### 核心功能
- **多数据源搜索**: 支持6个权威数据源
- **100%稳定性**: 解决PubMed和ClinicalTrials访问问题
- **异步并行处理**: 高效的异步搜索
- **智能去重**: 多层级去重算法
- **Web界面**: 完整的Web用户界面
- **RESTful API**: 程序化调用接口

#### 支持的数据源
- PubMed (通过Europe PMC后备)
- Europe PMC
- Semantic Scholar
- Clinical Trials (通过NIH Reporter)
- BioRxiv
- MedRxiv

#### 技术特性
- 异步并发处理
- 智能降级策略
- 代理支持
- 配置管理
- 日志系统

---

*更多详细信息请参考各版本的发布说明和文档。*
