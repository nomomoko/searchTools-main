from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import Field

from .searchAPIchoose.EuropePMC import EuropePMCAPIWrapper
from .searchAPIchoose.pubmed import PubMedAPIWrapper

# 这是魔改了langchain的pubmed搜索，增加了近五年检索和按照时间范围检索的逻辑。（时间范围检索暂时注释掉了）


class PubmedQueryRun(BaseTool):
    """Tool that searches the PubMed API."""

    name: str = "pub_med"
    description: str = (
        "A wrapper around PubMed. "
        "Useful for when you need to answer questions about medicine, health, "
        "and biomedical topics "
        "from biomedical literature, MEDLINE, life science journals, and online books. "
        "Input should be a search query.")
    api_wrapper: PubMedAPIWrapper = Field(default_factory=EuropePMCAPIWrapper)

    # Europe是pubmed镜像，可以实现按照引用量排序，就写在这里了，

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the PubMed tool."""
        return self.api_wrapper.run(query)


if __name__ == "__main__":
    tool = PubmedQueryRun()
    query = "diabetes treatment"
    result = tool._run(query)
    print(f"Query: {query}\nResult: {result}")
