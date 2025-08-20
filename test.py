from searchtools.pubmed_search import PubmedQueryRun

# 使用工具
wrapper = PubmedQueryRun()
results = wrapper.run("machine learning")
print(results)
