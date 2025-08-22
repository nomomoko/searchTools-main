# 📝 Commit Message 标准规范

本文档定义了SearchTools项目的commit message标准格式，确保代码历史清晰易读。

## 🎯 分类标准

### 主要类型

| 类型 | 图标 | 说明 | 示例 |
|------|------|------|------|
| **feat** | ✨ | 新功能 | `✨ feat: 新增学术专用Embedding系统` |
| **fix** | 🐛 | Bug修复 | `🐛 fix: 修复Web界面JavaScript错误` |
| **docs** | 📚 | 文档更新 | `📚 docs: 补充学术AI功能使用指南` |
| **style** | 🎨 | 代码格式 | `🎨 style: 改进日志输出格式` |
| **refactor** | 🔧 | 代码重构 | `🔧 refactor: 重构搜索管理器架构` |
| **perf** | ⚡ | 性能优化 | `⚡ perf: 优化embedding缓存机制` |
| **test** | 🧪 | 测试相关 | `🧪 test: 添加学术特征提取测试` |
| **build** | 🛠️ | 构建系统 | `🛠️ build: 更新依赖包配置` |
| **ci** | 👷 | CI/CD | `👷 ci: 添加自动化测试流程` |
| **chore** | 🔨 | 其他杂项 | `🔨 chore: 更新.gitignore文件` |

### 特殊类型

| 类型 | 图标 | 说明 | 示例 |
|------|------|------|------|
| **release** | 🚀 | 版本发布 | `🚀 release: SearchTools v1.3.0` |
| **hotfix** | 🚑 | 紧急修复 | `🚑 hotfix: 修复生产环境崩溃问题` |
| **security** | 🔒 | 安全修复 | `🔒 security: 修复API密钥泄露风险` |
| **breaking** | 💥 | 破坏性变更 | `💥 breaking: 重构API接口结构` |
| **revert** | ⏪ | 回滚变更 | `⏪ revert: 回滚commit abc123` |
| **merge** | 🔀 | 合并分支 | `🔀 merge: 合并feature/embedding分支` |

## 📋 格式规范

### 基本格式
```
<图标> <类型>: <简短描述>

<详细描述>
- 具体变更1
- 具体变更2
- 具体变更3

<影响和注意事项>
```

### 示例模板

#### 新功能 (feat)
```
✨ feat: 新增学术专用Embedding系统

集成多种先进的学术embedding模型:
- SPECTER2: 专为科学文献设计的文档级embedding
- SciBERT: 科学文本预训练的BERT模型
- BGE-M3: 多功能、多语言的高性能embedding模型
- 智能缓存机制减少重复计算时间50-80%
- 批处理优化提升大规模文档处理效率

影响: 显著提升学术搜索的语义理解能力
```

#### Bug修复 (fix)
```
🐛 fix: 修复Web界面JavaScript错误

解决前端字段映射不匹配问题:
- 修复'Cannot read properties of undefined'错误
- 统一API响应数据结构和前端字段映射
- 更新字段引用: search_time → performance.total_time
- 修复去重统计显示异常

影响: Web界面JavaScript错误率降至0%
```

#### 性能优化 (perf)
```
⚡ perf: 优化搜索性能和缓存机制

多方面性能提升:
- 缓存命中率提升至83%
- GPU加速减少70-90%计算时间
- 并行处理提升30-50%响应速度
- 内存使用优化减少40%占用

影响: 整体搜索性能提升2-3倍
```

#### 文档更新 (docs)
```
📚 docs: 完善学术AI功能文档

新增和更新文档:
- ACADEMIC_EMBEDDINGS_GUIDE.md: 详细使用指南
- TROUBLESHOOTING.md: 故障排除指南
- WEB_INTERFACE_GUIDE.md: Web界面使用指南
- 更新README.md添加新功能说明

影响: 提升用户使用体验和开发者贡献效率
```

## 🏷️ SearchTools历史Commit分类

### v1.3.0 学术AI功能
```
🧠 SearchTools v1.3.0 - 学术AI功能重大更新
├── ✨ feat: 新增学术专用Embedding系统
├── ✨ feat: ColBERT多向量重排序系统  
├── ✨ feat: 学术特征提取引擎
├── ✨ feat: 混合检索系统
├── ⚡ perf: 性能和质量显著提升
├── 🔧 refactor: 系统架构改进
├── 📚 docs: 文档和测试完善
└── 🛠️ build: 开发体验改进
```

### v1.2.1 Bug修复和文档
```
🐛 修复Web界面JavaScript错误和完善文档 v1.2.1
├── 🐛 fix: 修复Web界面JavaScript错误
├── 🐛 fix: 解决500 Internal Server Error
├── 🔧 refactor: 统一API响应数据结构
├── 📚 docs: 新增故障排除指南
├── 📚 docs: 新增Web界面使用指南
└── 📚 docs: 更新README和CHANGELOG
```

### v1.2.0 高级算法和性能优化
```
🚀 SearchTools v1.2.0 - 高级算法与性能优化重大更新
├── ✨ feat: 智能重排序(Rerank)功能
├── ⚡ perf: 高级算法和API优化
├── 🔧 refactor: 解决合并冲突保留功能改进
├── 🎯 feat: 优化BioRxiv和MedRxiv预印本过滤
├── 🎨 style: 改进日志输出消除红色标注
└── 🐛 fix: 解决模块导入路径问题
```

## 🎯 最佳实践

### 1. 标题行规范
- 使用相应的图标和类型前缀
- 简短描述（50字符以内）
- 使用现在时态
- 首字母小写（除专有名词）
- 结尾不加句号

### 2. 详细描述规范
- 空行分隔标题和正文
- 使用项目符号列出具体变更
- 说明变更的原因和影响
- 包含相关的Issue或PR编号

### 3. 特殊情况处理
- **破坏性变更**: 必须在标题中标明`💥 breaking`
- **安全修复**: 使用`🔒 security`并详细说明风险
- **版本发布**: 使用`🚀 release`并包含版本号
- **紧急修复**: 使用`🚑 hotfix`并说明紧急程度

### 4. 多语言支持
- 优先使用中文描述（项目主要用户群体）
- 关键技术术语保持英文
- 重要commit可提供英文翻译

## 📊 统计和分析

### Commit类型分布（建议）
- **feat**: 40% - 新功能开发
- **fix**: 25% - Bug修复
- **docs**: 15% - 文档更新
- **refactor**: 10% - 代码重构
- **perf**: 5% - 性能优化
- **其他**: 5% - 测试、构建等

### 质量指标
- 每个commit应该是原子性的（单一职责）
- 标题应该清晰描述变更内容
- 详细描述应该说明变更原因
- 重要变更应该包含影响评估

## 🔧 工具和自动化

### Git Hooks
可以设置pre-commit hook来验证commit message格式：

```bash
#!/bin/sh
# .git/hooks/commit-msg

commit_regex='^(✨|🐛|📚|🎨|🔧|⚡|🧪|🛠️|👷|🔨|🚀|🚑|🔒|💥|⏪|🔀)\s(feat|fix|docs|style|refactor|perf|test|build|ci|chore|release|hotfix|security|breaking|revert|merge):\s.{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "Invalid commit message format!"
    echo "Please use: <icon> <type>: <description>"
    exit 1
fi
```

### IDE插件
推荐使用支持commit message模板的IDE插件：
- VSCode: Conventional Commits
- IntelliJ: Git Commit Template
- Vim: vim-commitizen

---

*遵循规范的commit message让项目历史更清晰，协作更高效！*
