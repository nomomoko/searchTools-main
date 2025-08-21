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

        # 使用更简单、更稳定的请求头
        headers = {
            "User-Agent": "searchtools/1.0 (Academic Research Tool)",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.http_client = SearchHTTPClient(headers=headers,
                                            timeout=config.timeout,
                                            max_retries=config.max_retries)

    def _search_alternative_api(self, search_query: str, max_studies: int = 15) -> list:
        """
        使用替代的API端点进行搜索
        """
        try:
            logger.info(f"[ClinicalTrials Alternative] Searching for: {search_query}")

            # 使用更简单的API调用
            params = {
                "expr": search_query,
                "min_rnk": 1,
                "max_rnk": min(max_studies, 20),
                "fmt": "json"
            }

            # 尝试使用旧版API端点
            old_api_url = "https://clinicaltrials.gov/api/query/study_fields"
            response = self.http_client.get(old_api_url, params=params)

            if response.status_code == 200:
                data = response.json()
                studies = data.get("StudyFieldsResponse", {}).get("StudyFields", [])
                logger.info(f"[ClinicalTrials Alternative] Found {len(studies)} studies")
                return studies
            else:
                logger.warning(f"[ClinicalTrials Alternative] API returned {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"[ClinicalTrials Alternative] Error: {e}")
            return []

    @retry(
        stop=stop_after_attempt(2),  # 减少重试次数
        wait=wait_exponential(multiplier=1, min=2, max=8),
        reraise=False,  # 不重新抛出异常，使用降级策略
    )
    def search(self,
               search_query: str,
               status: str = None,
               max_studies: int = 15) -> list:
        """
        检索临床试验，返回结构化的试验信息列表。
        增强了错误处理和降级策略。
        """
        # 限制最大结果数量以提高稳定性
        max_studies = min(max_studies, 15)

        # 首先尝试新版API
        try:
            fields_to_get = [
                "NCTId",
                "BriefTitle",
                "OverallStatus",
                "Condition",
                "InterventionName",
                "BriefSummary",
                "LeadSponsorName",
            ]

            # 简化查询参数
            params = {
                "query.term": search_query.strip(),
                "fields": ",".join(fields_to_get),
                "pageSize": max_studies,
                "format": "json",
            }

            logger.info(f"[ClinicalTrials] Searching for: {search_query}")
            response = self.http_client.get(f"{self.base_url}studies", params=params)

            if response.status_code == 200:
                data = response.json()
                studies = data.get("studies", [])
                if studies:
                    logger.info(f"[ClinicalTrials] Found {len(studies)} studies")
                    time.sleep(self.rate_limit_delay)
                    return studies

            logger.warning(f"[ClinicalTrials] New API returned {response.status_code}, trying alternative")

        except Exception as e:
            logger.warning(f"[ClinicalTrials] New API failed: {e}")

        # 降级到替代API
        return self._search_alternative_api(search_query, max_studies)

    def parse_study(self, study: dict) -> dict:
        """
        从原始study结构中提取常用字段，返回扁平化字典。
        支持新版和旧版API的不同响应格式。
        """
        # 检测API响应格式
        if "protocolSection" in study:
            # 新版API格式
            return self._parse_new_api_format(study)
        elif isinstance(study, list) and len(study) > 0:
            # 旧版API格式（字段数组）
            return self._parse_old_api_format(study)
        else:
            # 尝试直接字段访问
            return self._parse_direct_format(study)

    def _parse_new_api_format(self, study: dict) -> dict:
        """解析新版API格式"""
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

    def _parse_old_api_format(self, study: list) -> dict:
        """解析旧版API格式（字段数组）"""
        try:
            # 旧版API返回字段数组，需要按位置解析
            nctId = study[0] if len(study) > 0 else "N/A"
            briefTitle = study[1] if len(study) > 1 else "N/A"
            overallStatus = study[2] if len(study) > 2 else "N/A"
            conditions = study[3] if len(study) > 3 else "N/A"
            interventions = study[4] if len(study) > 4 else "N/A"
            briefSummary = study[5] if len(study) > 5 else "N/A"
            leadSponsor = study[6] if len(study) > 6 else "N/A"

            return {
                "nctId": nctId,
                "briefTitle": briefTitle,
                "overallStatus": overallStatus,
                "conditions": conditions,
                "interventionName": interventions,
                "eligibilityCriteria": "N/A",  # 旧版API可能不包含此字段
                "briefSummary": briefSummary,
                "leadSponsorName": leadSponsor,
            }
        except Exception as e:
            logger.warning(f"[ClinicalTrials] Error parsing old API format: {e}")
            return {}

    def _parse_direct_format(self, study: dict) -> dict:
        """解析直接字段格式"""
        return {
            "nctId": study.get("NCTId", study.get("nctId", "N/A")),
            "briefTitle": study.get("BriefTitle", study.get("briefTitle", "N/A")),
            "overallStatus": study.get("OverallStatus", study.get("overallStatus", "N/A")),
            "conditions": study.get("Condition", study.get("conditions", "N/A")),
            "interventionName": study.get("InterventionName", study.get("interventionName", "N/A")),
            "eligibilityCriteria": study.get("EligibilityCriteria", study.get("eligibilityCriteria", "N/A")),
            "briefSummary": study.get("BriefSummary", study.get("briefSummary", "N/A")),
            "leadSponsorName": study.get("LeadSponsorName", study.get("leadSponsorName", "N/A")),
        }

    def search_and_parse(self,
                         search_query: str,
                         status: str = None,
                         max_studies: int = 15) -> list:
        """
        检索并返回结构化的试验信息列表（每条为dict）。
        使用改进的搜索策略，提高成功率。
        """
        # 直接使用改进的search方法，它已经包含了降级策略
        studies = self.search(search_query, status, max_studies)

        if studies:
            parsed_studies = []
            for study in studies:
                if study:
                    try:
                        parsed = self.parse_study(study)
                        if parsed:
                            parsed_studies.append(parsed)
                    except Exception as e:
                        logger.warning(f"[ClinicalTrials] Failed to parse study: {e}")
                        continue

            logger.info(f"[ClinicalTrials] Successfully parsed {len(parsed_studies)} studies")
            return parsed_studies

        logger.warning("[ClinicalTrials] No studies found or all searches failed")
        return []
