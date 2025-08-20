"""
异步版本的 ClinicalTrials.gov API 封装类
"""

from typing import List, Optional
from ..async_http_client import AsyncSearchHTTPClient

API_BASE_URL = "https://clinicaltrials.gov/api/v2/"


class AsyncClinicalTrialsAPIWrapper:
    """
    ClinicalTrials.gov API 异步封装类，支持按关键词和状态检索临床试验。

    对于每个临床试验，默认返回以下字段：
    - NCTId
    - BriefTitle
    - OverallStatus
    - Condition
    - InterventionName
    - EligibilityCriteria
    - BriefSummary
    - LeadSponsorName
    """

    def __init__(self):
        self.base_url = API_BASE_URL
        from ..search_config import get_api_config

        config = get_api_config("clinical_trials")
        self.max_results = config.max_results  # 保存配置的最大结果数
        # ClinicalTrials.gov 需要更像浏览器的 User-Agent
        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        self.http_client = AsyncSearchHTTPClient(
            timeout=config.timeout,
            max_retries=config.max_retries,
            headers=headers)

    async def search(self,
                     search_query: str,
                     status: Optional[str] = None,
                     max_studies: int = 15) -> List[dict]:
        """
        异步检索临床试验，返回原始试验信息列表。

        Args:
            search_query: 搜索查询
            status: 试验状态筛选
            max_studies: 返回的最大试验数

        Returns:
            试验信息列表
        """
        fields_to_get = [
            "NCTId",
            "BriefTitle",
            "OverallStatus",
            "Condition",
            "InterventionName",
            "EligibilityCriteria",
            "BriefSummary",  # 摘要
            "LeadSponsorName",
        ]

        params = {
            "query.term":
            f"{search_query} {status}" if status else search_query,
            "fields": ",".join(fields_to_get),
            "pageSize": max_studies,
        }

        try:
            async with self.http_client:
                response = await self.http_client.get(
                    f"{self.base_url}studies", params=params)
                data = response.json()
                return data.get("studies", [])
        except Exception as e:
            print(f"[AsyncClinicalTrialsAPIWrapper] Error: {e}")
            return []

    def parse_study(self, study: dict) -> dict:
        """
        从原始study结构中提取常用字段，返回扁平化字典。

        注：这个方法不需要异步，因为是纯计算操作
        """
        protocol_section = study.get("protocolSection", {})

        id_mod = protocol_section.get("identificationModule", {})
        nctId = id_mod.get("nctId", "N/A")
        briefTitle = id_mod.get("briefTitle", "N/A")

        status_mod = protocol_section.get("statusModule", {})
        overallStatus = status_mod.get("overallStatus", "N/A")

        sponsor_mod = protocol_section.get("sponsorCollaboratorsModule", {})
        leadSponsor = sponsor_mod.get("leadSponsor", {}).get("name", "N/A")

        desc_mod = protocol_section.get("descriptionModule", {})
        briefSummary = desc_mod.get("briefSummary", "N/A")

        cond_mod = protocol_section.get("conditionsModule", {})
        conditions = cond_mod.get("conditions", [])
        if isinstance(conditions, list):
            conditions = ", ".join(conditions)
        else:
            conditions = conditions or "N/A"

        arms_mod = protocol_section.get("armsInterventionsModule", {})
        interventions = arms_mod.get("interventions", [])
        if isinstance(interventions, list):
            interventions = ", ".join(
                [item.get("name", "") for item in interventions])
        else:
            interventions = interventions or "N/A"

        elig_mod = protocol_section.get("eligibilityModule", {})
        eligibilityCriteria = elig_mod.get("eligibilityCriteria", "N/A")

        return {
            "nctId": nctId,
            "briefTitle": briefTitle,
            "overallStatus": overallStatus,
            "conditions": conditions,
            "interventionName": interventions,
            "eligibilityCriteria": eligibilityCriteria,
            "briefSummary": briefSummary,
            "leadSponsorName": leadSponsor,
        }

    async def search_and_parse(self,
                               search_query: str,
                               status: Optional[str] = None,
                               max_studies: int = 15) -> List[dict]:
        """
        异步检索并返回结构化的试验信息列表。

        Args:
            search_query: 搜索查询
            status: 试验状态筛选
            max_studies: 返回的最大试验数

        Returns:
            结构化的试验信息列表
        """
        studies = await self.search(search_query, status, max_studies)
        return [self.parse_study(study) for study in studies]

    async def run(self,
                  query: str,
                  status: Optional[str] = None) -> List[dict]:
        """
        运行 ClinicalTrials 检索，返回统一格式的结构化数据。

        Args:
            query: 搜索关键词
            status: 试验状态筛选

        Returns:
            List of dictionaries containing trial information in unified format
        """
        try:
            # 搜索并解析试验数据
            trials = await self.search_and_parse(query,
                                                 status,
                                                 max_studies=self.max_results)

            # 转换为统一格式
            results = []
            for trial in trials:
                # 构建URL
                nct_id = trial.get("nctId", "")
                url = (f"https://clinicaltrials.gov/study/{nct_id}"
                       if nct_id != "N/A" else "")

                # 构建结构化结果（适配统一格式）
                trial_data = {
                    "title": trial.get("briefTitle", ""),
                    "authors": trial.get("leadSponsorName", ""),  # 使用赞助商作为"作者"
                    "journal": "ClinicalTrials.gov",
                    "year": "",  # 临床试验通常没有发表年份
                    "citations": 0,  # 临床试验不提供引用数
                    "doi": "",  # 临床试验没有DOI
                    "pmid": "",  # 临床试验没有PMID
                    "pmcid": "",  # 临床试验没有PMCID
                    "published_date": "",
                    "url": url,
                    "abstract": trial.get("briefSummary", ""),
                    # 额外的临床试验特定信息
                    "nct_id": nct_id,
                    "status": trial.get("overallStatus", ""),
                    "conditions": trial.get("conditions", ""),
                    "interventions": trial.get("interventionName", ""),
                    "eligibility": trial.get("eligibilityCriteria", ""),
                }
                results.append(trial_data)

            return results

        except Exception as ex:
            print(f"Async ClinicalTrials exception: {ex}")
            return []

    def load(self, query: str) -> List[dict]:
        """
        同步包装器 - 为了兼容性保留
        内部调用异步版本
        """
        import asyncio

        return asyncio.run(self.run(query))
