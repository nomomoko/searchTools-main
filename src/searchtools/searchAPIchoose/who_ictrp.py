"""
WHO International Clinical Trials Registry Platform (ICTRP) API Wrapper
作为ClinicalTrials.gov的替代数据源
"""

import logging
import time
from typing import List, Dict, Any
from ..http_client import SearchHTTPClient

logger = logging.getLogger(__name__)

class WHOICTRPAPIWrapper:
    """
    WHO ICTRP API包装器，提供临床试验搜索功能
    """
    
    def __init__(self):
        from ..search_config import get_api_config
        
        config = get_api_config("clinical_trials")
        self.max_results = config.max_results
        self.rate_limit_delay = getattr(config, 'rate_limit_delay', 1.0)
        
        # WHO ICTRP搜索端点
        self.base_url = "https://trialsearch.who.int/api/search"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://trialsearch.who.int/",
            "Origin": "https://trialsearch.who.int"
        }
        
        self.http_client = SearchHTTPClient(
            headers=headers,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
    
    def search_trials(self, search_query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """
        搜索WHO ICTRP数据库中的临床试验
        """
        try:
            logger.info(f"[WHO ICTRP] Searching for: {search_query}")
            
            params = {
                "q": search_query,
                "size": min(max_results, 20),
                "from": 0,
                "sort": "relevance"
            }
            
            response = self.http_client.get(self.base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                trials = data.get("trials", [])
                logger.info(f"[WHO ICTRP] Found {len(trials)} trials")
                
                # 添加速率限制延迟
                time.sleep(self.rate_limit_delay)
                
                return trials
            else:
                logger.warning(f"[WHO ICTRP] HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"[WHO ICTRP] Search error: {e}")
            return []
    
    def parse_trial(self, trial: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析WHO ICTRP试验数据为标准格式
        """
        try:
            return {
                "nctId": trial.get("trial_id", "N/A"),
                "briefTitle": trial.get("public_title", "N/A"),
                "overallStatus": trial.get("recruitment_status", "N/A"),
                "conditions": trial.get("condition", "N/A"),
                "interventionName": trial.get("intervention", "N/A"),
                "eligibilityCriteria": trial.get("inclusion_criteria", "N/A"),
                "briefSummary": trial.get("scientific_title", "N/A"),
                "leadSponsorName": trial.get("primary_sponsor", "N/A"),
                "source": "WHO ICTRP"
            }
        except Exception as e:
            logger.warning(f"[WHO ICTRP] Parse error: {e}")
            return {}
    
    def search_and_parse(self, search_query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """
        搜索并解析WHO ICTRP试验数据
        """
        trials = self.search_trials(search_query, max_results)
        parsed_trials = []
        
        for trial in trials:
            parsed = self.parse_trial(trial)
            if parsed:
                parsed_trials.append(parsed)
        
        logger.info(f"[WHO ICTRP] Successfully parsed {len(parsed_trials)} trials")
        return parsed_trials


class EUClinicalTrialsAPIWrapper:
    """
    EU Clinical Trials Register API包装器
    """
    
    def __init__(self):
        from ..search_config import get_api_config
        
        config = get_api_config("clinical_trials")
        self.max_results = config.max_results
        self.rate_limit_delay = getattr(config, 'rate_limit_delay', 1.0)
        
        # EU Clinical Trials Register搜索端点
        self.base_url = "https://www.clinicaltrialsregister.eu/ctr-search/rest/search"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        self.http_client = SearchHTTPClient(
            headers=headers,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
    
    def search_trials(self, search_query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """
        搜索EU Clinical Trials Register
        """
        try:
            logger.info(f"[EU CTR] Searching for: {search_query}")
            
            params = {
                "query": search_query,
                "page": 1,
                "pageSize": min(max_results, 20)
            }
            
            response = self.http_client.get(self.base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                trials = data.get("results", [])
                logger.info(f"[EU CTR] Found {len(trials)} trials")
                
                time.sleep(self.rate_limit_delay)
                return trials
            else:
                logger.warning(f"[EU CTR] HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"[EU CTR] Search error: {e}")
            return []
    
    def parse_trial(self, trial: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析EU CTR试验数据
        """
        try:
            return {
                "nctId": trial.get("eudractNumber", "N/A"),
                "briefTitle": trial.get("title", "N/A"),
                "overallStatus": trial.get("trialStatus", "N/A"),
                "conditions": trial.get("medicalCondition", "N/A"),
                "interventionName": trial.get("intervention", "N/A"),
                "eligibilityCriteria": "N/A",
                "briefSummary": trial.get("title", "N/A"),
                "leadSponsorName": trial.get("sponsor", "N/A"),
                "source": "EU CTR"
            }
        except Exception as e:
            logger.warning(f"[EU CTR] Parse error: {e}")
            return {}
    
    def search_and_parse(self, search_query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """
        搜索并解析EU CTR试验数据
        """
        trials = self.search_trials(search_query, max_results)
        parsed_trials = []
        
        for trial in trials:
            parsed = self.parse_trial(trial)
            if parsed:
                parsed_trials.append(parsed)
        
        logger.info(f"[EU CTR] Successfully parsed {len(parsed_trials)} trials")
        return parsed_trials
