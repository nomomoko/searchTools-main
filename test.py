import sys
import os
# 添加 src 路径到搜索路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from searchtools.pubmed_search import PubmedQueryRun

# 使用工具
wrapper = PubmedQueryRun()
results = wrapper.run("machine learning")
print(results)
