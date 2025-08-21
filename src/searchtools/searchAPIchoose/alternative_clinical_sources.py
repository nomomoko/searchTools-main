"""
替代临床试验数据源 - 避免ClinicalTrials.gov的403错误
"""

import logging
import time
import json
from typing import List, Dict, Any
from ..http_client import SearchHTTPClient

logger = logging.getLogger(__name__)

class ClinicalTrialsGovAlternativeWrapper:
    """
    使用ClinicalTrials.gov的替代接口和镜像站点
    """
    
    def __init__(self):
        from ..search_config import get_api_config
        
        config = get_api_config("clinical_trials")
        self.max_results = config.max_results
        self.rate_limit_delay = getattr(config, 'rate_limit_delay', 2.0)
        
        # 使用更友好的请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Academic Research Tool; +https://example.com/bot)",
            "Accept": "application/json, text/html, application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache"
        }
        
        self.http_client = SearchHTTPClient(
            headers=headers,
            timeout=config.timeout,
            max_retries=1
        )
    
    def search_via_json_api(self, search_query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """
        尝试使用ClinicalTrials.gov的JSON API的不同端点
        """
        try:
            logger.info(f"[ClinicalTrials JSON] Searching for: {search_query}")
            
            # 尝试不同的API端点
            endpoints = [
                "https://clinicaltrials.gov/api/v2/studies",
                "https://classic.clinicaltrials.gov/api/query/study_fields",
                "https://www.clinicaltrials.gov/api/query/study_fields"
            ]
            
            for endpoint in endpoints:
                try:
                    if "v2" in endpoint:
                        # 新版API格式
                        params = {
                            "query.term": search_query,
                            "pageSize": min(max_results, 10),
                            "format": "json"
                        }
                    else:
                        # 旧版API格式
                        params = {
                            "expr": search_query,
                            "min_rnk": 1,
                            "max_rnk": min(max_results, 10),
                            "fmt": "json"
                        }
                    
                    # 添加随机延迟
                    import random
                    time.sleep(random.uniform(2, 5))
                    
                    response = self.http_client.get(endpoint, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        studies = self._extract_studies_from_json(data, search_query)
                        if studies:
                            logger.info(f"[ClinicalTrials JSON] Found {len(studies)} studies from {endpoint}")
                            return studies
                    
                except Exception as e:
                    logger.warning(f"[ClinicalTrials JSON] Endpoint {endpoint} failed: {e}")
                    continue
            
            return []
            
        except Exception as e:
            logger.error(f"[ClinicalTrials JSON] Search error: {e}")
            return []
    
    def _extract_studies_from_json(self, data: Dict[str, Any], search_query: str) -> List[Dict[str, Any]]:
        """
        从JSON响应中提取试验信息
        """
        try:
            studies = []
            
            # 处理新版API响应
            if "studies" in data:
                raw_studies = data["studies"]
            # 处理旧版API响应
            elif "StudyFieldsResponse" in data:
                raw_studies = data["StudyFieldsResponse"].get("StudyFields", [])
            else:
                return []
            
            for study in raw_studies:
                try:
                    if isinstance(study, dict) and "protocolSection" in study:
                        # 新版API格式
                        studies.append(study)
                    elif isinstance(study, list):
                        # 旧版API格式（字段数组）
                        converted_study = self._convert_old_format_to_new(study, search_query)
                        if converted_study:
                            studies.append(converted_study)
                    elif isinstance(study, dict):
                        # 直接字段格式
                        converted_study = self._convert_direct_format_to_new(study, search_query)
                        if converted_study:
                            studies.append(converted_study)
                            
                except Exception as e:
                    logger.warning(f"[ClinicalTrials JSON] Failed to process study: {e}")
                    continue
            
            return studies
            
        except Exception as e:
            logger.error(f"[ClinicalTrials JSON] JSON extraction error: {e}")
            return []
    
    def _convert_old_format_to_new(self, study_array: List[str], search_query: str) -> Dict[str, Any]:
        """
        将旧版API的数组格式转换为新版格式
        """
        try:
            nct_id = study_array[0] if len(study_array) > 0 else "Unknown"
            title = study_array[1] if len(study_array) > 1 else f"Study for {search_query}"
            status = study_array[2] if len(study_array) > 2 else "Unknown"
            
            return {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": nct_id,
                        "briefTitle": title
                    },
                    "statusModule": {
                        "overallStatus": status
                    },
                    "conditionsModule": {
                        "conditions": [search_query]
                    },
                    "armsInterventionsModule": {
                        "interventions": [{"name": "See study details"}]
                    },
                    "descriptionModule": {
                        "briefSummary": f"Clinical trial related to {search_query}."
                    },
                    "sponsorCollaboratorsModule": {
                        "leadSponsor": {"name": "See ClinicalTrials.gov"}
                    }
                }
            }
        except Exception:
            return {}
    
    def _convert_direct_format_to_new(self, study_dict: Dict[str, Any], search_query: str) -> Dict[str, Any]:
        """
        将直接字段格式转换为新版格式
        """
        try:
            return {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": study_dict.get("NCTId", study_dict.get("nct_id", "Unknown")),
                        "briefTitle": study_dict.get("BriefTitle", study_dict.get("title", f"Study for {search_query}"))
                    },
                    "statusModule": {
                        "overallStatus": study_dict.get("OverallStatus", study_dict.get("status", "Unknown"))
                    },
                    "conditionsModule": {
                        "conditions": [study_dict.get("Condition", search_query)]
                    },
                    "armsInterventionsModule": {
                        "interventions": [{"name": study_dict.get("InterventionName", "See study details")}]
                    },
                    "descriptionModule": {
                        "briefSummary": study_dict.get("BriefSummary", f"Clinical trial related to {search_query}.")
                    },
                    "sponsorCollaboratorsModule": {
                        "leadSponsor": {"name": study_dict.get("LeadSponsorName", "See ClinicalTrials.gov")}
                    }
                }
            }
        except Exception:
            return {}


class ClinicalTrialsRegistryWrapper:
    """
    使用其他国家和地区的临床试验注册中心
    """
    
    def __init__(self):
        from ..search_config import get_api_config
        
        config = get_api_config("clinical_trials")
        self.max_results = config.max_results
        self.rate_limit_delay = getattr(config, 'rate_limit_delay', 1.0)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Academic Research Tool)",
            "Accept": "application/json, text/html",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        self.http_client = SearchHTTPClient(
            headers=headers,
            timeout=config.timeout,
            max_retries=1
        )
    
    def search_multiple_registries(self, search_query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """
        搜索多个临床试验注册中心
        """
        all_studies = []
        
        # 搜索各个注册中心
        registries = [
            ("ANZCTR", self._search_anzctr),
            ("ISRCTN", self._search_isrctn),
            ("ChiCTR", self._search_chictr)
        ]
        
        for registry_name, search_func in registries:
            try:
                logger.info(f"[{registry_name}] Searching for: {search_query}")
                studies = search_func(search_query, max_results // len(registries))
                if studies:
                    logger.info(f"[{registry_name}] Found {len(studies)} studies")
                    all_studies.extend(studies)
                time.sleep(self.rate_limit_delay)
            except Exception as e:
                logger.warning(f"[{registry_name}] Search failed: {e}")
                continue
        
        return all_studies[:max_results]
    
    def _search_anzctr(self, search_query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索澳新临床试验注册中心 (ANZCTR)
        """
        try:
            # ANZCTR搜索URL
            search_url = f"https://www.anzctr.org.au/TrialSearch.aspx"
            params = {
                "searchTxt": search_query,
                "isBasic": "True"
            }
            
            response = self.http_client.get(search_url, params=params)
            
            if response.status_code == 200:
                # 简单的HTML解析提取试验ID
                import re
                trial_ids = re.findall(r'ACTRN\d{14}', response.text)
                
                studies = []
                for trial_id in trial_ids[:max_results]:
                    study = {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": trial_id,
                                "briefTitle": f"ANZCTR Trial for {search_query}"
                            },
                            "statusModule": {
                                "overallStatus": "See ANZCTR"
                            },
                            "conditionsModule": {
                                "conditions": [search_query]
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"name": "See ANZCTR details"}]
                            },
                            "descriptionModule": {
                                "briefSummary": f"Clinical trial from ANZCTR related to {search_query}."
                            },
                            "sponsorCollaboratorsModule": {
                                "leadSponsor": {"name": "See ANZCTR"}
                            }
                        }
                    }
                    studies.append(study)
                
                return studies
            
            return []
            
        except Exception as e:
            logger.error(f"[ANZCTR] Search error: {e}")
            return []
    
    def _search_isrctn(self, search_query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索ISRCTN注册中心
        """
        try:
            # ISRCTN搜索API
            search_url = "https://www.isrctn.com/search"
            params = {
                "q": search_query,
                "filters": "condition:" + search_query
            }
            
            response = self.http_client.get(search_url, params=params)
            
            if response.status_code == 200:
                # 简单的HTML解析
                import re
                trial_ids = re.findall(r'ISRCTN\d{8}', response.text)
                
                studies = []
                for trial_id in trial_ids[:max_results]:
                    study = {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": trial_id,
                                "briefTitle": f"ISRCTN Trial for {search_query}"
                            },
                            "statusModule": {
                                "overallStatus": "See ISRCTN"
                            },
                            "conditionsModule": {
                                "conditions": [search_query]
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"name": "See ISRCTN details"}]
                            },
                            "descriptionModule": {
                                "briefSummary": f"Clinical trial from ISRCTN related to {search_query}."
                            },
                            "sponsorCollaboratorsModule": {
                                "leadSponsor": {"name": "See ISRCTN"}
                            }
                        }
                    }
                    studies.append(study)
                
                return studies
            
            return []
            
        except Exception as e:
            logger.error(f"[ISRCTN] Search error: {e}")
            return []
    
    def _search_chictr(self, search_query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索中国临床试验注册中心 (ChiCTR)
        """
        try:
            # ChiCTR搜索URL
            search_url = "http://www.chictr.org.cn/searchprojen.aspx"
            params = {
                "title": search_query,
                "officialname": "",
                "subjectid": "",
                "secondaryid": "",
                "applier": "",
                "studyleader": "",
                "ethicalcommitteesanction": "",
                "sponsor": "",
                "studyailment": "",
                "studyailmentcode": "",
                "studytype": "",
                "studystage": "",
                "studydesign": "",
                "minstudyexecutetime": "",
                "maxstudyexecutetime": "",
                "recruitmentstatus": "",
                "gender": "",
                "agreetosign": "",
                "secsponsor": "",
                "regno": "",
                "regstatus": "",
                "country": "",
                "province": "",
                "city": "",
                "institution": "",
                "institutionlevel": "",
                "measure": "",
                "intercode": "",
                "sourceofspends": "",
                "createyear": "",
                "isuploadrf": "",
                "whetherpublic": "",
                "btngo": "btn&Go"
            }
            
            response = self.http_client.get(search_url, params=params)
            
            if response.status_code == 200:
                # 简单的HTML解析
                import re
                trial_ids = re.findall(r'ChiCTR\d{10}', response.text)
                
                studies = []
                for trial_id in trial_ids[:max_results]:
                    study = {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": trial_id,
                                "briefTitle": f"ChiCTR Trial for {search_query}"
                            },
                            "statusModule": {
                                "overallStatus": "See ChiCTR"
                            },
                            "conditionsModule": {
                                "conditions": [search_query]
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"name": "See ChiCTR details"}]
                            },
                            "descriptionModule": {
                                "briefSummary": f"Clinical trial from ChiCTR related to {search_query}."
                            },
                            "sponsorCollaboratorsModule": {
                                "leadSponsor": {"name": "See ChiCTR"}
                            }
                        }
                    }
                    studies.append(study)
                
                return studies
            
            return []
            
        except Exception as e:
            logger.error(f"[ChiCTR] Search error: {e}")
            return []
