import openai
import numpy as np
from typing import List, Dict, Tuple, Optional, Union, Literal
import json
import os
from dotenv import load_dotenv
from scipy.spatial.distance import cosine, euclidean, cityblock
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
import faiss
import warnings

# Load environment variables
load_dotenv()


class EmbeddingClient:
    """
    Client for OpenAI embedding API with advanced vector operations and similarity metrics.
    """

    def __init__(self, model_name: str = "text-embedding-3-small"):
        """
        Initialize the embedding client.

        Args:
            model_name (str): OpenAI embedding model name
        """
        self.model_name = model_name
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 缓存已计算的embedding以避免重复计算
        self._embedding_cache = {}

    def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Get embedding for a single text.

        Args:
            text (str): Text to embed
            use_cache (bool): Whether to use caching

        Returns:
            List[float]: Embedding vector
        """
        if use_cache and text in self._embedding_cache:
            return self._embedding_cache[text]
            
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            embedding = response.data[0].embedding
            
            if use_cache:
                self._embedding_cache[text] = embedding
                
            return embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return []

    def get_embeddings_batch(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        Get embeddings for multiple texts in batch.

        Args:
            texts (List[str]): List of texts to embed
            use_cache (bool): Whether to use caching

        Returns:
            List[List[float]]: List of embedding vectors
        """
        # 分离已缓存和未缓存的文本
        cached_embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            if use_cache and text in self._embedding_cache:
                cached_embeddings.append(self._embedding_cache[text])
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 获取未缓存文本的embedding
        if uncached_texts:
            try:
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=uncached_texts
                )
                new_embeddings = [data.embedding for data in response.data]
                
                # 缓存新的embedding
                if use_cache:
                    for text, embedding in zip(uncached_texts, new_embeddings):
                        self._embedding_cache[text] = embedding
            except Exception as e:
                print(f"Error getting batch embeddings: {e}")
                new_embeddings = [[] for _ in uncached_texts]
        
        # 合并结果
        result = [None] * len(texts)
        for i, embedding in enumerate(cached_embeddings):
            result[i] = embedding
        for i, embedding in zip(uncached_indices, new_embeddings):
            result[i] = embedding
            
        return result

    def calculate_similarity(self, vec1: Union[List[float], np.ndarray], 
                           vec2: Union[List[float], np.ndarray],
                           method: Literal['cosine', 'euclidean', 'manhattan', 'dot_product', 
                                         'pearson', 'spearman', 'jaccard', 'hamming'] = 'cosine') -> float:
        """
        Calculate similarity between two vectors using various methods.

        Args:
            vec1: First vector
            vec2: Second vector
            method: Similarity calculation method

        Returns:
            float: Similarity score
        """
        # 转换为numpy数组
        vec1 = np.array(vec1, dtype=np.float32)
        vec2 = np.array(vec2, dtype=np.float32)
        
        if len(vec1) != len(vec2):
            return 0.0
        
        if method == 'cosine':
            # 余弦相似度 - 最常用的文本相似度度量
            return 1 - cosine(vec1, vec2)
            
        elif method == 'euclidean':
            # 欧几里得距离 - 转换为相似度 (1 / (1 + distance))
            distance = euclidean(vec1, vec2)
            return 1 / (1 + distance)
            
        elif method == 'manhattan':
            # 曼哈顿距离 - 转换为相似度
            distance = cityblock(vec1, vec2)
            return 1 / (1 + distance)
            
        elif method == 'dot_product':
            # 点积 - 需要归一化
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot_product / (norm1 * norm2)
            
        elif method == 'pearson':
            # 皮尔逊相关系数
            if np.std(vec1) == 0 or np.std(vec2) == 0:
                return 0.0
            return np.corrcoef(vec1, vec2)[0, 1]
            
        elif method == 'spearman':
            # 斯皮尔曼相关系数
            from scipy.stats import spearmanr
            try:
                return spearmanr(vec1, vec2)[0]
            except:
                return 0.0
                
        elif method == 'jaccard':
            # Jaccard相似度 (适用于稀疏向量)
            vec1_binary = (vec1 > 0).astype(int)
            vec2_binary = (vec2 > 0).astype(int)
            intersection = np.sum(vec1_binary & vec2_binary)
            union = np.sum(vec1_binary | vec2_binary)
            return intersection / union if union > 0 else 0.0
            
        elif method == 'hamming':
            # 汉明距离 (适用于二进制向量)
            vec1_binary = (vec1 > 0).astype(int)
            vec2_binary = (vec2 > 0).astype(int)
            return 1 - np.mean(vec1_binary != vec2_binary)
            
        else:
            raise ValueError(f"Unknown similarity method: {method}")

    def find_most_similar_faiss(self, query_embedding: List[float],
                               candidate_embeddings: List[List[float]],
                               top_k: int = 5,
                               method: str = 'cosine') -> List[Tuple[int, float]]:
        """
        Find the most similar embeddings using FAISS for high-performance similarity search.

        Args:
            query_embedding: Query embedding
            candidate_embeddings: Candidate embeddings
            top_k: Number of top results to return
            method: Similarity method ('cosine', 'euclidean')

        Returns:
            List[Tuple[int, float]]: List of (index, similarity_score) tuples
        """
        if not candidate_embeddings:
            return []
            
        # 过滤空embedding
        valid_embeddings = []
        valid_indices = []
        for i, emb in enumerate(candidate_embeddings):
            if emb:
                valid_embeddings.append(emb)
                valid_indices.append(i)
        
        if not valid_embeddings:
            return []
            
        # 转换为numpy数组
        embeddings_array = np.array(valid_embeddings, dtype=np.float32)
        query_array = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        
        # 选择FAISS索引类型
        if method == 'cosine':
            # 对于余弦相似度，需要归一化向量
            faiss.normalize_L2(embeddings_array)
            faiss.normalize_L2(query_array)
            index = faiss.IndexFlatIP(embeddings_array.shape[1])  # Inner Product
        else:
            index = faiss.IndexFlatL2(embeddings_array.shape[1])  # L2 distance
        
        # 添加向量到索引
        index.add(embeddings_array)
        
        # 搜索
        distances, indices = index.search(query_array, min(top_k, len(valid_embeddings)))
        
        # 转换结果
        results = []
        for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
            if idx != -1:  # FAISS返回-1表示无效结果
                original_idx = valid_indices[idx]
                if method == 'cosine':
                    similarity = dist  # 内积就是余弦相似度
                else:
                    similarity = 1 / (1 + dist)  # 转换为相似度
                results.append((original_idx, similarity))
        
        return results

    def find_most_similar_sklearn(self, query_embedding: List[float],
                                 candidate_embeddings: List[List[float]],
                                 top_k: int = 5,
                                 method: str = 'cosine') -> List[Tuple[int, float]]:
        """
        Find the most similar embeddings using scikit-learn for batch processing.

        Args:
            query_embedding: Query embedding
            candidate_embeddings: Candidate embeddings
            top_k: Number of top results to return
            method: Similarity method

        Returns:
            List[Tuple[int, float]]: List of (index, similarity_score) tuples
        """
        if not candidate_embeddings:
            return []
            
        # 过滤空embedding
        valid_embeddings = []
        valid_indices = []
        for i, emb in enumerate(candidate_embeddings):
            if emb:
                valid_embeddings.append(emb)
                valid_indices.append(i)
        
        if not valid_embeddings:
            return []
            
        # 转换为numpy数组
        embeddings_array = np.array(valid_embeddings, dtype=np.float32)
        query_array = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        
        # 计算相似度矩阵
        if method == 'cosine':
            similarities = cosine_similarity(query_array, embeddings_array)[0]
        elif method == 'euclidean':
            distances = euclidean_distances(query_array, embeddings_array)[0]
            similarities = 1 / (1 + distances)
        else:
            # 使用自定义方法
            similarities = []
            for emb in valid_embeddings:
                sim = self.calculate_similarity(query_embedding, emb, method)
                similarities.append(sim)
            similarities = np.array(similarities)
        
        # 获取top_k结果
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            original_idx = valid_indices[idx]
            similarity = similarities[idx]
            results.append((original_idx, similarity))
        
        return results

    def find_most_similar(self, query_embedding: List[float],
                         candidate_embeddings: List[List[float]],
                         top_k: int = 5,
                         method: str = 'cosine',
                         use_faiss: bool = True) -> List[Tuple[int, float]]:
        """
        Find the most similar embeddings with optimized performance.

        Args:
            query_embedding: Query embedding
            candidate_embeddings: Candidate embeddings
            top_k: Number of top results to return
            method: Similarity method
            use_faiss: Whether to use FAISS for acceleration

        Returns:
            List[Tuple[int, float]]: List of (index, similarity_score) tuples
        """
        if not query_embedding:
            return []
            
        # 根据数据规模选择算法
        if use_faiss and len(candidate_embeddings) > 100:
            # 大数据集使用FAISS
            return self.find_most_similar_faiss(
                query_embedding, candidate_embeddings, top_k, method
            )
        else:
            # 小数据集使用sklearn或自定义方法
            return self.find_most_similar_sklearn(
                query_embedding, candidate_embeddings, top_k, method
            )

    def semantic_search(self, query: str, candidates: List[str],
                       top_k: int = 5,
                       method: str = 'cosine',
                       use_cache: bool = True,
                       use_faiss: bool = True) -> List[Tuple[int, float, str]]:
        """
        Perform semantic search on a list of candidate texts.

        Args:
            query: Search query
            candidates: Candidate texts
            top_k: Number of top results to return
            method: Similarity method
            use_cache: Whether to use embedding cache
            use_faiss: Whether to use FAISS for acceleration

        Returns:
            List[Tuple[int, float, str]]: List of (index, similarity_score, text) tuples
        """
        # Get embeddings
        query_embedding = self.get_embedding(query, use_cache)
        candidate_embeddings = self.get_embeddings_batch(candidates, use_cache)

        if not query_embedding:
            return []

        # Find most similar
        similar_indices = self.find_most_similar(
            query_embedding, candidate_embeddings, top_k, method, use_faiss)

        # Return results with text
        results = []
        for idx, similarity in similar_indices:
            if idx < len(candidates):
                results.append((idx, similarity, candidates[idx]))

        return results

    def batch_semantic_search(self, queries: List[str], candidates: List[str],
                            top_k: int = 5,
                            method: str = 'cosine',
                            use_cache: bool = True) -> List[List[Tuple[int, float, str]]]:
        """
        Perform batch semantic search for multiple queries.

        Args:
            queries: List of search queries
            candidates: Candidate texts
            top_k: Number of top results to return
            method: Similarity method
            use_cache: Whether to use embedding cache

        Returns:
            List[List[Tuple[int, float, str]]]: Results for each query
        """
        # Get embeddings for all queries and candidates
        query_embeddings = self.get_embeddings_batch(queries, use_cache)
        candidate_embeddings = self.get_embeddings_batch(candidates, use_cache)
        
        if not candidate_embeddings:
            return [[] for _ in queries]
        
        # 转换为numpy数组
        query_array = np.array(query_embeddings, dtype=np.float32)
        candidate_array = np.array(candidate_embeddings, dtype=np.float32)
        
        # 计算相似度矩阵
        if method == 'cosine':
            similarity_matrix = cosine_similarity(query_array, candidate_array)
        elif method == 'euclidean':
            distance_matrix = euclidean_distances(query_array, candidate_array)
            similarity_matrix = 1 / (1 + distance_matrix)
        else:
            # 使用自定义方法
            similarity_matrix = np.zeros((len(queries), len(candidates)))
            for i, query_emb in enumerate(query_embeddings):
                for j, candidate_emb in enumerate(candidate_embeddings):
                    if query_emb and candidate_emb:
                        similarity_matrix[i, j] = self.calculate_similarity(
                            query_emb, candidate_emb, method
                        )
        
        # 获取每个查询的top_k结果
        results = []
        for i, similarities in enumerate(similarity_matrix):
            top_indices = np.argsort(similarities)[::-1][:top_k]
            query_results = []
            for idx in top_indices:
                if idx < len(candidates):
                    query_results.append((idx, similarities[idx], candidates[idx]))
            results.append(query_results)
        
        return results

    def clear_cache(self):
        """Clear the embedding cache."""
        self._embedding_cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'cache_size': len(self._embedding_cache),
            'cache_memory_estimate': len(self._embedding_cache) * 1536 * 4  # 假设每个embedding是1536维float32
        }
