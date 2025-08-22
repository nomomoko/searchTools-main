#!/usr/bin/env python3
"""
学术论文专用Embedding系统

基于最新研究集成多种学术优化的embedding模型：
- SPECTER2: 专为科学文献设计的文档级embedding
- SciBERT: 科学文本预训练的BERT模型
- BGE-M3: 多功能、多语言的高性能embedding模型
- ColBERT: 多向量检索和重排序

支持功能：
- 语义相似度计算
- 文档聚类和分类
- 引用推荐
- 相关论文发现
"""

import os
import json
import hashlib
import logging
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np
from functools import lru_cache
import time

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class EmbeddingConfig:
    """Embedding配置类"""
    model_name: str = "specter2"  # specter2, scibert, bge-m3, colbert
    cache_size: int = 1000
    enable_caching: bool = True
    batch_size: int = 32
    max_length: int = 512
    device: str = "cpu"  # cpu, cuda
    model_path: Optional[str] = None
    
    # SPECTER2特定配置
    specter2_variant: str = "base"  # base, proximity, adhoc
    
    # BGE-M3特定配置
    bge_m3_mode: str = "dense"  # dense, sparse, colbert
    
    # ColBERT特定配置
    colbert_dim: int = 128
    colbert_similarity: str = "cosine"  # cosine, l2

class BaseEmbeddingModel(ABC):
    """Embedding模型基类"""
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.cache = {} if config.enable_caching else None
        self.model = None
        self.tokenizer = None
        
    @abstractmethod
    def load_model(self):
        """加载模型"""
        pass
    
    @abstractmethod
    def encode(self, texts: Union[str, List[str]], **kwargs) -> np.ndarray:
        """编码文本为向量"""
        pass
    
    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _get_from_cache(self, text: str) -> Optional[np.ndarray]:
        """从缓存获取embedding"""
        if not self.cache:
            return None
        key = self._get_cache_key(text)
        return self.cache.get(key)
    
    def _save_to_cache(self, text: str, embedding: np.ndarray):
        """保存embedding到缓存"""
        if not self.cache:
            return
        if len(self.cache) >= self.config.cache_size:
            # LRU清理
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        key = self._get_cache_key(text)
        self.cache[key] = embedding

class SPECTER2Model(BaseEmbeddingModel):
    """SPECTER2学术论文embedding模型
    
    SPECTER2是专门为科学文献设计的文档级embedding模型，
    在学术论文相似度、分类、聚类等任务上表现优异。
    """
    
    def load_model(self):
        """加载SPECTER2模型"""
        try:
            from transformers import AutoTokenizer, AutoModel
            
            model_name = f"allenai/specter2_{self.config.specter2_variant}"
            logger.info(f"Loading SPECTER2 model: {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            
            if self.config.device == "cuda":
                import torch
                if torch.cuda.is_available():
                    self.model = self.model.cuda()
                    logger.info("SPECTER2 model loaded on GPU")
                else:
                    logger.warning("CUDA not available, using CPU")
            
            logger.info("SPECTER2 model loaded successfully")
            
        except ImportError:
            logger.error("transformers library not found. Install with: pip install transformers torch")
            raise
        except Exception as e:
            logger.error(f"Failed to load SPECTER2 model: {e}")
            raise
    
    def encode(self, texts: Union[str, List[str]], **kwargs) -> np.ndarray:
        """编码学术论文文本
        
        Args:
            texts: 论文文本（标题+摘要）或文本列表
            
        Returns:
            embedding向量数组
        """
        if isinstance(texts, str):
            texts = [texts]
        
        # 检查缓存
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cached_emb = self._get_from_cache(text)
            if cached_emb is not None:
                embeddings.append(cached_emb)
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 处理未缓存的文本
        if uncached_texts:
            if self.model is None:
                self.load_model()
            
            try:
                import torch
                
                # 分批处理
                batch_embeddings = []
                for i in range(0, len(uncached_texts), self.config.batch_size):
                    batch_texts = uncached_texts[i:i + self.config.batch_size]
                    
                    # Tokenize
                    inputs = self.tokenizer(
                        batch_texts,
                        padding=True,
                        truncation=True,
                        max_length=self.config.max_length,
                        return_tensors="pt"
                    )
                    
                    if self.config.device == "cuda":
                        inputs = {k: v.cuda() for k, v in inputs.items()}
                    
                    # 获取embedding
                    with torch.no_grad():
                        outputs = self.model(**inputs)
                        # 使用[CLS] token的embedding
                        batch_emb = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                        batch_embeddings.append(batch_emb)
                
                # 合并批次结果
                if batch_embeddings:
                    uncached_embeddings = np.vstack(batch_embeddings)
                    
                    # 保存到缓存并更新结果
                    for i, (text, emb) in enumerate(zip(uncached_texts, uncached_embeddings)):
                        self._save_to_cache(text, emb)
                        embeddings[uncached_indices[i]] = emb
                
            except Exception as e:
                logger.error(f"Error encoding texts with SPECTER2: {e}")
                raise
        
        return np.array([emb for emb in embeddings if emb is not None])

class SciBERTModel(BaseEmbeddingModel):
    """SciBERT学术文本embedding模型
    
    SciBERT是在科学文本上预训练的BERT模型，
    对科学术语和概念有更好的理解。
    """
    
    def load_model(self):
        """加载SciBERT模型"""
        try:
            from transformers import AutoTokenizer, AutoModel
            
            model_name = "allenai/scibert_scivocab_uncased"
            logger.info(f"Loading SciBERT model: {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            
            if self.config.device == "cuda":
                import torch
                if torch.cuda.is_available():
                    self.model = self.model.cuda()
                    logger.info("SciBERT model loaded on GPU")
                else:
                    logger.warning("CUDA not available, using CPU")
            
            logger.info("SciBERT model loaded successfully")
            
        except ImportError:
            logger.error("transformers library not found. Install with: pip install transformers torch")
            raise
        except Exception as e:
            logger.error(f"Failed to load SciBERT model: {e}")
            raise
    
    def encode(self, texts: Union[str, List[str]], **kwargs) -> np.ndarray:
        """编码科学文本"""
        if isinstance(texts, str):
            texts = [texts]
        
        # 检查缓存
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cached_emb = self._get_from_cache(text)
            if cached_emb is not None:
                embeddings.append(cached_emb)
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 处理未缓存的文本
        if uncached_texts:
            if self.model is None:
                self.load_model()
            
            try:
                import torch
                
                # 分批处理
                batch_embeddings = []
                for i in range(0, len(uncached_texts), self.config.batch_size):
                    batch_texts = uncached_texts[i:i + self.config.batch_size]
                    
                    # Tokenize
                    inputs = self.tokenizer(
                        batch_texts,
                        padding=True,
                        truncation=True,
                        max_length=self.config.max_length,
                        return_tensors="pt"
                    )
                    
                    if self.config.device == "cuda":
                        inputs = {k: v.cuda() for k, v in inputs.items()}
                    
                    # 获取embedding (mean pooling)
                    with torch.no_grad():
                        outputs = self.model(**inputs)
                        # 使用mean pooling
                        attention_mask = inputs['attention_mask']
                        token_embeddings = outputs.last_hidden_state
                        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                        batch_emb = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
                        batch_emb = batch_emb.cpu().numpy()
                        batch_embeddings.append(batch_emb)
                
                # 合并批次结果
                if batch_embeddings:
                    uncached_embeddings = np.vstack(batch_embeddings)
                    
                    # 保存到缓存并更新结果
                    for i, (text, emb) in enumerate(zip(uncached_texts, uncached_embeddings)):
                        self._save_to_cache(text, emb)
                        embeddings[uncached_indices[i]] = emb
                
            except Exception as e:
                logger.error(f"Error encoding texts with SciBERT: {e}")
                raise
        
        return np.array([emb for emb in embeddings if emb is not None])

class BGE_M3Model(BaseEmbeddingModel):
    """BGE-M3多功能embedding模型
    
    BGE-M3支持dense、sparse、colbert三种检索模式，
    在多种检索任务上都有优异表现。
    """
    
    def load_model(self):
        """加载BGE-M3模型"""
        try:
            from FlagEmbedding import BGEM3FlagModel
            
            model_name = "BAAI/bge-m3"
            logger.info(f"Loading BGE-M3 model: {model_name}")
            
            self.model = BGEM3FlagModel(
                model_name,
                use_fp16=True if self.config.device == "cuda" else False
            )
            
            logger.info("BGE-M3 model loaded successfully")
            
        except ImportError:
            logger.error("FlagEmbedding library not found. Install with: pip install FlagEmbedding")
            raise
        except Exception as e:
            logger.error(f"Failed to load BGE-M3 model: {e}")
            raise
    
    def encode(self, texts: Union[str, List[str]], **kwargs) -> np.ndarray:
        """编码文本为多功能向量"""
        if isinstance(texts, str):
            texts = [texts]
        
        if self.model is None:
            self.load_model()
        
        try:
            if self.config.bge_m3_mode == "dense":
                embeddings = self.model.encode(texts, batch_size=self.config.batch_size)['dense_vecs']
            elif self.config.bge_m3_mode == "sparse":
                embeddings = self.model.encode(texts, batch_size=self.config.batch_size)['lexical_weights']
            elif self.config.bge_m3_mode == "colbert":
                embeddings = self.model.encode(texts, batch_size=self.config.batch_size)['colbert_vecs']
            else:
                raise ValueError(f"Unsupported BGE-M3 mode: {self.config.bge_m3_mode}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error encoding texts with BGE-M3: {e}")
            raise

class AcademicEmbeddingManager:
    """学术embedding管理器
    
    统一管理多种学术embedding模型，提供高级功能：
    - 模型选择和切换
    - 批量处理
    - 缓存管理
    - 性能监控
    """
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.models = {}
        self.current_model = None
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'total_time': 0.0
        }
    
    def get_model(self, model_name: str = None) -> BaseEmbeddingModel:
        """获取或创建embedding模型"""
        if model_name is None:
            model_name = self.config.model_name
        
        if model_name not in self.models:
            if model_name == "specter2":
                self.models[model_name] = SPECTER2Model(self.config)
            elif model_name == "scibert":
                self.models[model_name] = SciBERTModel(self.config)
            elif model_name == "bge-m3":
                self.models[model_name] = BGE_M3Model(self.config)
            else:
                raise ValueError(f"Unsupported model: {model_name}")
        
        return self.models[model_name]
    
    def encode_papers(self, papers: List[Dict], model_name: str = None) -> np.ndarray:
        """编码学术论文
        
        Args:
            papers: 论文列表，每个论文包含title和abstract字段
            model_name: 使用的模型名称
            
        Returns:
            论文embedding向量数组
        """
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            model = self.get_model(model_name)
            
            # 构建论文文本（标题+摘要）
            texts = []
            for paper in papers:
                title = paper.get('title', '')
                abstract = paper.get('abstract', '')
                # SPECTER2推荐的格式：标题 + [SEP] + 摘要
                text = f"{title} [SEP] {abstract}" if abstract else title
                texts.append(text)
            
            # 编码
            embeddings = model.encode(texts)
            
            # 更新统计
            self.stats['total_time'] += time.time() - start_time
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error encoding papers: {e}")
            raise
    
    def compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray, 
                          method: str = "cosine") -> float:
        """计算embedding相似度"""
        if method == "cosine":
            return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        elif method == "euclidean":
            return 1.0 / (1.0 + np.linalg.norm(emb1 - emb2))
        elif method == "dot":
            return np.dot(emb1, emb2)
        else:
            raise ValueError(f"Unsupported similarity method: {method}")
    
    def find_similar_papers(self, query_embedding: np.ndarray, 
                           paper_embeddings: np.ndarray,
                           top_k: int = 10) -> List[Tuple[int, float]]:
        """找到最相似的论文"""
        similarities = []
        for i, paper_emb in enumerate(paper_embeddings):
            sim = self.compute_similarity(query_embedding, paper_emb)
            similarities.append((i, sim))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_stats(self) -> Dict:
        """获取性能统计"""
        stats = self.stats.copy()
        if stats['total_requests'] > 0:
            stats['avg_time'] = stats['total_time'] / stats['total_requests']
            stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_requests']
        return stats
    
    def clear_cache(self):
        """清理所有模型缓存"""
        for model in self.models.values():
            if model.cache:
                model.cache.clear()
        logger.info("All model caches cleared")

# 便捷函数
def create_academic_embedder(model_name: str = "specter2", **kwargs) -> AcademicEmbeddingManager:
    """创建学术embedding管理器"""
    config = EmbeddingConfig(model_name=model_name, **kwargs)
    return AcademicEmbeddingManager(config)

def encode_paper_text(title: str, abstract: str = "", 
                     model_name: str = "specter2") -> np.ndarray:
    """快速编码单篇论文"""
    embedder = create_academic_embedder(model_name)
    papers = [{"title": title, "abstract": abstract}]
    return embedder.encode_papers(papers)[0]
