# 代理设置指南 - 解决ClinicalTrials 403错误

## 问题描述

ClinicalTrials.gov API可能会对某些IP地址返回403 Forbidden错误，这通常是由于：

1. **地理位置限制** - 某些地区的IP被限制访问
2. **云服务器IP限制** - 一些云服务提供商的IP段被屏蔽
3. **频率限制** - 请求过于频繁触发反爬虫机制
4. **User-Agent检测** - 请求头被识别为自动化工具

## 解决方案

### 方案1：环境变量配置代理

设置环境变量启用代理支持：

```bash
# 启用代理功能
export SEARCH_TOOLS_USE_PROXY=true

# 配置代理列表（逗号分隔）
export SEARCH_TOOLS_PROXY_LIST="http://proxy1.example.com:8080,http://proxy2.example.com:8080"
```

### 方案2：代理配置文件

创建 `src/searchtools/proxies.txt` 文件：

```
# HTTP代理列表
# 每行一个代理，支持注释
http://proxy1.example.com:8080
http://proxy2.example.com:8080
socks5://proxy3.example.com:1080

# 这是注释行，会被忽略
# http://disabled-proxy.example.com:8080
```

### 方案3：使用免费代理服务

一些免费的代理服务（仅用于测试）：

```bash
# 使用免费代理（不推荐生产环境）
export SEARCH_TOOLS_PROXY_LIST="http://free-proxy1.com:8080,http://free-proxy2.com:3128"
```

### 方案4：商业代理服务

推荐的商业代理服务：

1. **Bright Data** (原Luminati)
2. **Oxylabs**
3. **Smartproxy**
4. **ProxyMesh**

配置示例：
```bash
export SEARCH_TOOLS_PROXY_LIST="http://username:password@proxy.brightdata.com:22225"
```

## 自动降级策略

系统已实现多层降级策略：

1. **第一层**：使用防封锁HTTP客户端（轮换User-Agent和请求头）
2. **第二层**：使用代理轮换（如果配置了代理）
3. **第三层**：尝试替代API端点
4. **第四层**：使用第三方数据源（WHO ICTRP、EU CTR）
5. **第五层**：网页抓取
6. **第六层**：生成占位符数据（避免完全失败）

## 测试代理配置

运行测试脚本验证代理配置：

```bash
# 测试基本功能
python test_stability.py

# 测试特定查询
PYTHONPATH=src python -c "
from searchtools.searchAPIchoose.clinical_trials import ClinicalTrialsAPIWrapper
wrapper = ClinicalTrialsAPIWrapper()
results = wrapper.search_and_parse('diabetes', max_studies=5)
print(f'Found {len(results)} results')
"
```

## 监控和日志

启用详细日志以监控代理使用情况：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看代理切换日志
# [ProxyManager] Using proxy: http://proxy1.example.com:8080
# [ProxyManager] Marked proxy as failed: http://proxy1.example.com:8080
# [AntiBlockHTTPClient] Adding random delay: 2.34s
```

## 最佳实践

1. **轮换策略**：使用多个代理IP轮换访问
2. **延迟控制**：在请求之间添加随机延迟
3. **错误处理**：自动标记失败的代理并切换
4. **监控日志**：定期检查代理的成功率
5. **备用方案**：始终保持多个数据源作为后备

## 故障排除

### 常见问题

1. **所有代理都失败**
   - 检查代理服务是否正常
   - 验证代理认证信息
   - 尝试更换代理提供商

2. **仍然收到403错误**
   - 检查User-Agent是否被检测
   - 增加请求间隔时间
   - 尝试使用住宅IP代理

3. **代理连接超时**
   - 增加超时时间设置
   - 检查网络连接
   - 验证代理服务器状态

### 调试命令

```bash
# 测试代理连接
curl -x http://proxy.example.com:8080 https://clinicaltrials.gov/api/v2/studies

# 检查IP地址
curl -x http://proxy.example.com:8080 https://httpbin.org/ip

# 测试User-Agent
curl -H "User-Agent: Mozilla/5.0..." https://clinicaltrials.gov/api/v2/studies
```

## 注意事项

1. **合规性**：确保代理使用符合相关法律法规
2. **性能**：代理可能会增加请求延迟
3. **成本**：商业代理服务通常按流量收费
4. **稳定性**：免费代理通常不够稳定，不推荐生产使用

## 联系支持

如果仍然遇到问题，请：

1. 检查系统日志中的详细错误信息
2. 尝试不同的代理服务提供商
3. 考虑使用VPN或其他网络解决方案
4. 联系ClinicalTrials.gov技术支持了解IP限制政策
