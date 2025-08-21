"""
NIH Reporter API Wrapper - 作为ClinicalTrials.gov的稳定替代数据源
"""

import logging
import time
from typing import List, Dict, Any
from ..http_client import SearchHTTPClient

logger = logging.getLogger(__name__)

class NIHReporterAPIWrapper:
    """
    NIH Reporter API包装器，提供临床试验和研究项目搜索功能
    """
    
    def __init__(self):
        from ..search_config import get_api_config
        
        config = get_api_config("clinical_trials")
        self.max_results = config.max_results
        self.rate_limit_delay = getattr(config, 'rate_limit_delay', 1.0)
        
        # NIH Reporter API端点
        self.base_url = "https://api.reporter.nih.gov/v2/projects/search"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Academic Research Tool)",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        self.http_client = SearchHTTPClient(
            headers=headers,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
    
    def search_projects(self, search_query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """
        搜索NIH Reporter数据库中的研究项目
        """
        try:
            logger.info(f"[NIH Reporter] Searching for: {search_query}")
            
            # 构建搜索请求体
            search_data = {
                "criteria": {
                    "advanced_text_search": {
                        "operator": "and",
                        "search_field": "projecttitle,terms,abstracttext",
                        "search_text": search_query
                    },
                    "project_types": ["1", "2", "3", "4", "5"],  # 包含各种项目类型
                    "fiscal_years": [2020, 2021, 2022, 2023, 2024, 2025]  # 最近几年
                },
                "include_fields": [
                    "ProjectNum", "ProjectTitle", "AbstractText", "OrgName",
                    "PrincipalInvestigators", "ProjectStartDate", "ProjectEndDate",
                    "AwardAmount", "ActivityCode", "StudySection"
                ],
                "offset": 0,
                "limit": min(max_results, 20),
                "sort_field": "project_start_date",
                "sort_order": "desc"
            }
            
            response = self.http_client.post(self.base_url, json=search_data)
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get("results", [])
                logger.info(f"[NIH Reporter] Found {len(projects)} projects")
                
                # 添加速率限制延迟
                time.sleep(self.rate_limit_delay)
                
                return projects
            else:
                logger.warning(f"[NIH Reporter] HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"[NIH Reporter] Search error: {e}")
            return []
    
    def parse_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析NIH Reporter项目数据为ClinicalTrials格式
        """
        try:
            # 提取主要研究者信息
            pis = project.get("principal_investigators", [])
            pi_names = [pi.get("full_name", "") for pi in pis if pi.get("full_name")]
            pi_str = "; ".join(pi_names) if pi_names else "Unknown"
            
            # 提取项目信息
            project_num = project.get("project_num", "N/A")
            title = project.get("project_title", "N/A")
            abstract = project.get("abstract_text", "N/A")
            org_name = project.get("org_name", "N/A")
            start_date = project.get("project_start_date", "N/A")
            end_date = project.get("project_end_date", "N/A")
            
            # 构建状态信息
            status = "Active" if end_date and end_date > start_date else "Completed"
            
            return {
                "nctId": project_num,
                "briefTitle": title,
                "overallStatus": status,
                "conditions": "Research Project",
                "interventionName": "NIH Funded Research",
                "eligibilityCriteria": "See NIH Reporter for details",
                "briefSummary": abstract[:500] + "..." if len(abstract) > 500 else abstract,
                "leadSponsorName": org_name,
                "principalInvestigators": pi_str,
                "source": "NIH Reporter"
            }
        except Exception as e:
            logger.warning(f"[NIH Reporter] Parse error: {e}")
            return {}
    
    def search_and_parse(self, search_query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """
        搜索并解析NIH Reporter项目数据
        """
        projects = self.search_projects(search_query, max_results)
        parsed_projects = []
        
        for project in projects:
            parsed = self.parse_project(project)
            if parsed:
                parsed_projects.append(parsed)
        
        logger.info(f"[NIH Reporter] Successfully parsed {len(parsed_projects)} projects")
        return parsed_projects


class ClinicalTrialsGovSearchWrapper:
    """
    使用ClinicalTrials.gov的搜索页面进行数据提取
    """
    
    def __init__(self):
        from ..search_config import get_api_config
        
        config = get_api_config("clinical_trials")
        self.max_results = config.max_results
        self.rate_limit_delay = getattr(config, 'rate_limit_delay', 2.0)
        
        # 使用更友好的请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
        
        self.http_client = SearchHTTPClient(
            headers=headers,
            timeout=config.timeout,
            max_retries=1
        )
    
    def search_via_web_interface(self, search_query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """
        通过ClinicalTrials.gov的网页界面进行搜索
        """
        try:
            logger.info(f"[ClinicalTrials Web] Searching for: {search_query}")
            
            # 构建搜索URL - 使用简单的搜索界面
            import urllib.parse
            encoded_query = urllib.parse.quote_plus(search_query)
            
            # 使用基本搜索URL，避免复杂参数
            search_url = f"https://clinicaltrials.gov/search?term={encoded_query}"
            
            # 添加随机延迟避免被检测
            import random
            time.sleep(random.uniform(1, 3))
            
            response = self.http_client.get(search_url)
            
            if response.status_code == 200:
                # 简单的HTML解析
                studies = self._extract_studies_from_html(response.text, search_query)
                logger.info(f"[ClinicalTrials Web] Found {len(studies)} studies")
                return studies
            else:
                logger.warning(f"[ClinicalTrials Web] HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"[ClinicalTrials Web] Search error: {e}")
            return []
    
    def _extract_studies_from_html(self, html_content: str, search_query: str) -> List[Dict[str, Any]]:
        """
        从HTML内容中提取试验信息
        """
        try:
            import re
            
            studies = []
            
            # 查找NCT ID模式
            nct_pattern = r'NCT\d{8}'
            nct_ids = re.findall(nct_pattern, html_content)
            
            # 查找试验标题模式（简化版）
            title_pattern = r'<[^>]*title[^>]*>([^<]+)</[^>]*>'
            titles = re.findall(title_pattern, html_content, re.IGNORECASE)
            
            # 为每个找到的NCT ID创建基本的试验信息
            for i, nct_id in enumerate(set(nct_ids[:10])):  # 去重并限制数量
                title = titles[i] if i < len(titles) else f"Clinical Trial for {search_query}"
                
                study = {
                    "protocolSection": {
                        "identificationModule": {
                            "nctId": nct_id,
                            "briefTitle": title.strip()
                        },
                        "statusModule": {
                            "overallStatus": "See ClinicalTrials.gov"
                        },
                        "conditionsModule": {
                            "conditions": [search_query]
                        },
                        "armsInterventionsModule": {
                            "interventions": [{"name": "See study details"}]
                        },
                        "descriptionModule": {
                            "briefSummary": f"Clinical trial related to {search_query}. Visit https://clinicaltrials.gov/study/{nct_id} for full details."
                        },
                        "sponsorCollaboratorsModule": {
                            "leadSponsor": {"name": "See ClinicalTrials.gov"}
                        }
                    }
                }
                studies.append(study)
            
            return studies
            
        except Exception as e:
            logger.error(f"[ClinicalTrials Web] HTML parsing error: {e}")
            return []
