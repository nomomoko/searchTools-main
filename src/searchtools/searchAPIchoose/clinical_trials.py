from ..http_client import SearchHTTPClient
import time
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

API_BASE_URL = "https://clinicaltrials.gov/api/v2/"
logger = logging.getLogger(__name__)


class ClinicalTrialsAPIWrapper:
    """
    ClinicalTrials.gov API 封装类，支持按关键词和状态检索临床试验，并结构化返回常用字段。
    对返回的结果数和字段数可以在本py中修改
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
        self.rate_limit_delay = getattr(config, 'rate_limit_delay', 0.5)

        # ClinicalTrials.gov API 更稳定的 JSON 请求头
        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",  # 避免缓存问题
        }
        self.http_client = SearchHTTPClient(headers=headers,
                                            timeout=config.timeout,
                                            max_retries=config.max_retries)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def search(self,
               search_query: str,
               status: str = None,
               max_studies: int = 15) -> list:
        """
        检索临床试验，返回结构化的试验信息列表。
        增强了错误处理和重试机制。
        """
        # 限制最大结果数量以提高稳定性
        max_studies = min(max_studies, 20)

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

        # 构建查询参数，简化查询以提高成功率
        query_term = search_query.strip()
        if status:
            query_term = f"{query_term} AND {status}"

        params = {
            "query.term": query_term,
            "fields": ",".join(fields_to_get),
            "pageSize": max_studies,
            "format": "json",  # 明确指定格式
        }

        try:
            logger.info(f"[ClinicalTrials] Searching for: {query_term}")
            response = self.http_client.get(f"{self.base_url}studies",
                                            params=params)

            # 添加速率限制延迟
            if self.rate_limit_delay > 0:
                time.sleep(self.rate_limit_delay)

            data = response.json()
            studies = data.get("studies", [])
            logger.info(f"[ClinicalTrials] Found {len(studies)} studies")
            return studies

        except Exception as e:
            logger.error(f"[ClinicalTrialsAPIWrapper] Error: {e}")
            # 不立即返回空列表，让重试机制处理
            raise

    def parse_study(self, study: dict) -> dict:
        """
        从原始study结构中提取常用字段，返回扁平化字典。
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

    def search_and_parse(self,
                         search_query: str,
                         status: str = None,
                         max_studies: int = 15) -> list:
        """
        检索并返回结构化的试验信息列表（每条为dict）。
        增强了错误处理和降级策略。
        """
        try:
            # 首次尝试完整搜索
            studies = self.search(search_query, status, max_studies)
            if studies:
                return [self.parse_study(study) for study in studies if study]

        except Exception as e:
            logger.warning(f"[ClinicalTrials] Primary search failed: {e}")

        # 降级策略1: 简化查询，去掉状态过滤
        if status:
            try:
                logger.info("[ClinicalTrials] Trying fallback without status filter")
                studies = self.search(search_query, None, min(max_studies, 10))
                if studies:
                    return [self.parse_study(study) for study in studies if study]
            except Exception as e:
                logger.warning(f"[ClinicalTrials] Fallback 1 failed: {e}")

        # 降级策略2: 进一步减少结果数量
        try:
            logger.info("[ClinicalTrials] Trying minimal search")
            studies = self.search(search_query, None, 5)
            if studies:
                return [self.parse_study(study) for study in studies if study]
        except Exception as e:
            logger.error(f"[ClinicalTrials] All fallback strategies failed: {e}")

        return []
