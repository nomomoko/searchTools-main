from ..http_client import SearchHTTPClient

API_BASE_URL = "https://clinicaltrials.gov/api/v2/"


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
        # ClinicalTrials.gov API 更稳定的 JSON 请求头
        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        self.http_client = SearchHTTPClient(headers=headers,
                                            timeout=config.timeout,
                                            max_retries=config.max_retries)

    def search(self,
               search_query: str,
               status: str = None,
               max_studies: int = 15) -> list:
        """
        检索临床试验，返回结构化的试验信息列表。
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
            response = self.http_client.get(f"{self.base_url}studies",
                                            params=params)
            data = response.json()
            return data.get("studies", [])
        except Exception as e:
            print(f"[ClinicalTrialsAPIWrapper] Error: {e}")
            return []

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
        """
        studies = self.search(search_query, status, max_studies)
        return [self.parse_study(study) for study in studies]
