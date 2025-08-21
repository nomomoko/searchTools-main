# ⚡ 性能优化指南

## 概述

SearchTools v1.2.0 通过多种优化技术实现了卓越的性能表现。本指南详细介绍了性能优化策略和最佳实践。

## 📊 性能基准

### 重排序性能
- **100个结果**: < 3ms
- **500个结果**: < 12ms  
- **1000个结果**: < 25ms
- **缓存命中**: < 0.1ms

### 内存使用
- **基础引擎**: ~2MB
- **缓存(1000条)**: ~5MB
- **高级算法**: ~3MB
- **总计**: ~10MB

### API响应时间
- **搜索+重排序**: 增加 < 5ms
- **仅重排序**: < 3ms
- **缓存命中**: < 0.1ms

## 🚀 优化策略

### 1. 缓存优化

#### 启用缓存
```python
from searchtools.rerank_engine import RerankConfig, RerankEngine

config = RerankConfig(
    enable_caching=True,
    cache_size=1000  # 根据内存调整
)
engine = RerankEngine(config)
```

#### 缓存策略
- **LRU淘汰**: 自动淘汰最少使用的缓存项
- **智能键值**: 基于查询和结果数量的缓存键
- **内存控制**: 可配置的缓存大小限制

#### 缓存效果
```python
# 监控缓存性能
metrics = engine.get_performance_metrics()
print(f"缓存命中率: {metrics['cache_hit_rate']:.2%}")
print(f"缓存命中次数: {metrics['cache_hits']}")
```

### 2. 算法模式选择

#### 性能对比
| 模式 | 速度 | 准确性 | 内存使用 | 适用场景 |
|------|------|--------|----------|----------|
| traditional | 最快 | 良好 | 最少 | 快速搜索 |
| ml_only | 中等 | 很好 | 中等 | 精确匹配 |
| hybrid | 较快 | 最好 | 较多 | 综合应用 |

#### 模式配置
```python
# 快速模式
config = RerankConfig(algorithm_mode="traditional")

# 精确模式  
config = RerankConfig(algorithm_mode="ml_only")

# 平衡模式（推荐）
config = RerankConfig(algorithm_mode="hybrid")
```

### 3. 批量处理优化

#### 向量化计算
```python
import numpy as np

# 使用NumPy向量化操作
def vectorized_scoring(queries, documents):
    # 批量计算而非逐个计算
    scores = np.dot(query_vectors, doc_vectors.T)
    return scores
```

#### 预处理优化
```python
# 预构建词汇表和向量
engine = RerankEngine()
documents = [f"{r.title} {r.abstract}" for r in results]
engine.advanced_algorithm.prepare_documents(documents)
```

### 4. 内存优化

#### 对象重用
```python
# 重用RerankEngine实例
engine = RerankEngine()  # 创建一次
for query in queries:
    results = engine.rerank_results(documents, query)  # 重复使用
```

#### 缓存清理
```python
# 定期清理缓存
if engine.get_performance_metrics()['total_queries'] % 1000 == 0:
    engine.clear_cache()
```

### 5. 并发优化

#### 异步处理
```python
import asyncio

async def async_rerank(engine, results, query):
    # 在事件循环中运行重排序
    return await asyncio.get_event_loop().run_in_executor(
        None, engine.rerank_results, results, query
    )
```

#### 线程池
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(engine.rerank_results, results, query)
        for query in queries
    ]
    results = [f.result() for f in futures]
```

## 🔧 配置调优

### 环境变量优化
```bash
# 性能相关配置
SEARCH_TOOLS_ENABLE_CACHING=true
SEARCH_TOOLS_CACHE_SIZE=2000
SEARCH_TOOLS_ALGORITHM_MODE=hybrid

# 高级算法权重调优
SEARCH_TOOLS_BM25_WEIGHT=0.4
SEARCH_TOOLS_TFIDF_WEIGHT=0.3
SEARCH_TOOLS_COSINE_WEIGHT=0.2
SEARCH_TOOLS_SEMANTIC_WEIGHT=0.1
```

### 动态配置
```python
# 根据负载动态调整
def get_optimal_config(result_count, query_complexity):
    if result_count < 50:
        return RerankConfig(algorithm_mode="hybrid")
    elif result_count < 200:
        return RerankConfig(algorithm_mode="traditional")
    else:
        return RerankConfig(
            algorithm_mode="traditional",
            enable_caching=True,
            cache_size=500
        )
```

## 📈 性能监控

### 实时监控
```python
class PerformanceMonitor:
    def __init__(self, engine):
        self.engine = engine
        
    def get_stats(self):
        metrics = self.engine.get_performance_metrics()
        return {
            'avg_time': metrics['avg_processing_time'],
            'cache_hit_rate': metrics['cache_hit_rate'],
            'total_queries': metrics['total_queries'],
            'algorithm_usage': metrics['algorithm_usage']
        }
    
    def print_report(self):
        stats = self.get_stats()
        print(f"平均处理时间: {stats['avg_time']:.3f}s")
        print(f"缓存命中率: {stats['cache_hit_rate']:.2%}")
        print(f"总查询数: {stats['total_queries']}")
```

### 性能日志
```python
import logging

# 配置性能日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 在重排序后记录性能
logger = logging.getLogger('performance')
logger.info(f"Rerank completed: {len(results)} results in {time:.3f}s")
```

## 🎯 最佳实践

### 1. 生产环境配置
```python
# 生产环境推荐配置
production_config = RerankConfig(
    algorithm_mode="hybrid",
    enable_caching=True,
    cache_size=2000,
    use_advanced_algorithms=True,
    advanced_algorithm_weights={
        'bm25': 0.4,
        'tfidf': 0.3,
        'cosine': 0.2,
        'semantic': 0.1,
        'ml_features': 0.0  # 可选禁用以提升速度
    }
)
```

### 2. 负载测试
```python
import time
import statistics

def load_test(engine, queries, results, iterations=100):
    times = []
    for i in range(iterations):
        query = queries[i % len(queries)]
        start = time.time()
        engine.rerank_results(results, query)
        times.append(time.time() - start)
    
    return {
        'avg_time': statistics.mean(times),
        'median_time': statistics.median(times),
        'p95_time': sorted(times)[int(0.95 * len(times))],
        'max_time': max(times)
    }
```

### 3. 内存监控
```python
import psutil
import os

def monitor_memory():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        'rss': memory_info.rss / 1024 / 1024,  # MB
        'vms': memory_info.vms / 1024 / 1024,  # MB
        'percent': process.memory_percent()
    }
```

## 🔍 故障排除

### 常见性能问题

#### 1. 缓存未命中
**症状**: 相同查询响应时间不稳定
**解决**: 检查缓存配置和键值生成逻辑

#### 2. 内存泄漏
**症状**: 长时间运行后内存持续增长
**解决**: 定期清理缓存，检查对象引用

#### 3. 算法超时
**症状**: 大量结果处理时间过长
**解决**: 切换到traditional模式或减少结果数量

### 性能调试
```python
# 启用详细日志
import logging
logging.getLogger('searchtools.rerank_engine').setLevel(logging.DEBUG)

# 性能分析
import cProfile
cProfile.run('engine.rerank_results(results, query)')
```

## 📊 基准测试

### 运行基准测试
```bash
# 运行性能测试
python test_rerank.py

# 专门的性能测试
python -c "
from test_rerank import test_performance_and_caching
test_performance_and_caching()
"
```

### 自定义基准
```python
def custom_benchmark(result_counts, query_types):
    engine = RerankEngine()
    
    for count in result_counts:
        for query_type in query_types:
            results = generate_test_results(count)
            query = generate_test_query(query_type)
            
            start = time.time()
            engine.rerank_results(results, query)
            duration = time.time() - start
            
            print(f"{count} results, {query_type}: {duration*1000:.2f}ms")
```

## 🎛️ 高级优化

### 1. 预计算优化
```python
# 预计算文档特征
class PrecomputedEngine(RerankEngine):
    def __init__(self, config=None):
        super().__init__(config)
        self.doc_features = {}
    
    def precompute_features(self, results):
        for result in results:
            doc_id = hash(result.title + result.abstract)
            if doc_id not in self.doc_features:
                # 预计算特征
                self.doc_features[doc_id] = self._extract_features(result)
```

### 2. 算法选择优化
```python
def adaptive_algorithm_selection(query, result_count):
    if result_count < 20:
        return "hybrid"  # 小数据集用最好算法
    elif "covid" in query.lower():
        return "semantic"  # 特定领域用语义算法
    else:
        return "traditional"  # 默认用快速算法
```

---

*SearchTools 性能优化 - 速度与精度的完美平衡！*
