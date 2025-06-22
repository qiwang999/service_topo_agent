import redis
import json
import hashlib
from typing import Optional, Dict, List
from datetime import timedelta


class RedisCacheClient:
    """
    Redis-based cache client for query results and embeddings.
    """
    
    def __init__(self, host='localhost', port=6379, db=0, password=None, 
                 default_ttl=3600):  # 1 hour default TTL
        """
        Initialize Redis cache client.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            default_ttl: Default TTL in seconds
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True  # Return strings instead of bytes
        )
        self.default_ttl = default_ttl
        
        # Key prefixes for different types of data
        self.QUERY_CACHE_PREFIX = "query_cache:"
        self.EMBEDDING_PREFIX = "embedding:"
        self.EXAMPLE_PREFIX = "example:"
        self.FEEDBACK_PREFIX = "feedback:"
    
    def _generate_key(self, prefix: str, content: str) -> str:
        """Generate a Redis key from content."""
        # Use SHA256 for consistent hashing
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return f"{prefix}{content_hash}"
    
    def cache_query_result(self, question: str, generated_cypher: str, 
                          final_summary: str, similarity_score: float = None,
                          ttl: int = None) -> bool:
        """
        Cache a query result.
        
        Args:
            question: User's question
            generated_cypher: Generated Cypher query
            final_summary: Final summary
            similarity_score: Similarity score
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            bool: Success status
        """
        try:
            key = self._generate_key(self.QUERY_CACHE_PREFIX, question)
            
            cache_data = {
                'question': question,
                'generated_cypher': generated_cypher,
                'final_summary': final_summary,
                'similarity_score': similarity_score,
                'created_at': self.redis_client.time()[0]  # Unix timestamp
            }
            
            # Store as JSON string
            self.redis_client.setex(
                key,
                ttl or self.default_ttl,
                json.dumps(cache_data)
            )
            
            # Also store in a sorted set for similarity search
            if similarity_score is not None:
                self.redis_client.zadd(
                    f"{self.QUERY_CACHE_PREFIX}similarity",
                    {key: similarity_score}
                )
            
            return True
            
        except Exception as e:
            print(f"Error caching query result: {e}")
            return False
    
    def find_cached_result(self, question: str, min_similarity: float = 0.9) -> Optional[Dict]:
        """
        Find a cached result for a similar question.
        
        Args:
            question: User's question
            min_similarity: Minimum similarity threshold
            
        Returns:
            Optional[Dict]: Cached result if found
        """
        try:
            # For exact match
            key = self._generate_key(self.QUERY_CACHE_PREFIX, question)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                result = json.loads(cached_data)
                result['similarity'] = 1.0  # Exact match
                return result
            
            # For similarity search (would need embedding comparison)
            # This is a simplified version - in practice you'd need to compare embeddings
            return None
            
        except Exception as e:
            print(f"Error finding cached result: {e}")
            return None
    
    def update_cache_summary(self, question: str, final_summary: str) -> bool:
        """
        Update the final summary for a cached query result.
        
        Args:
            question: User's question
            final_summary: Updated summary
            
        Returns:
            bool: Success status
        """
        try:
            key = self._generate_key(self.QUERY_CACHE_PREFIX, question)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                data['final_summary'] = final_summary
                
                # Update with same TTL
                ttl = self.redis_client.ttl(key)
                if ttl > 0:
                    self.redis_client.setex(key, ttl, json.dumps(data))
                else:
                    self.redis_client.setex(key, self.default_ttl, json.dumps(data))
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error updating cache summary: {e}")
            return False
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict: Cache statistics
        """
        try:
            # Count query cache entries
            query_keys = self.redis_client.keys(f"{self.QUERY_CACHE_PREFIX}*")
            query_keys = [k for k in query_keys if not k.endswith(':similarity')]
            
            total_entries = len(query_keys)
            
            # Get memory usage
            info = self.redis_client.info('memory')
            memory_usage = info.get('used_memory_human', 'N/A')
            
            # Get most accessed entries (simplified - would need access tracking)
            stats = {
                'total_entries': total_entries,
                'memory_usage': memory_usage,
                'cache_hit_rate': 'N/A',  # Would need access tracking
                'avg_ttl': self.default_ttl
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {'error': str(e)}
    
    def clear_cache(self, pattern: str = None) -> bool:
        """
        Clear cache entries.
        
        Args:
            pattern: Key pattern to clear (e.g., "query_cache:*")
            
        Returns:
            bool: Success status
        """
        try:
            if pattern:
                keys = self.redis_client.keys(pattern)
            else:
                keys = self.redis_client.keys(f"{self.QUERY_CACHE_PREFIX}*")
            
            if keys:
                self.redis_client.delete(*keys)
            
            return True
            
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    def set_embedding(self, text_type: str, text_content: str, 
                     embedding_data: List[float], ttl: int = None) -> bool:
        """
        Store embedding data.
        
        Args:
            text_type: Type of text ('example', 'feedback', etc.)
            text_content: Text content
            embedding_data: Embedding vector
            ttl: Time to live in seconds
            
        Returns:
            bool: Success status
        """
        try:
            key = self._generate_key(f"{self.EMBEDDING_PREFIX}{text_type}:", text_content)
            
            self.redis_client.setex(
                key,
                ttl or self.default_ttl,
                json.dumps(embedding_data)
            )
            
            return True
            
        except Exception as e:
            print(f"Error storing embedding: {e}")
            return False
    
    def get_embedding(self, text_type: str, text_content: str) -> Optional[List[float]]:
        """
        Retrieve embedding data.
        
        Args:
            text_type: Type of text
            text_content: Text content
            
        Returns:
            Optional[List[float]]: Embedding vector if found
        """
        try:
            key = self._generate_key(f"{self.EMBEDDING_PREFIX}{text_type}:", text_content)
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            
            return None
            
        except Exception as e:
            print(f"Error retrieving embedding: {e}")
            return None
    
    def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            bool: True if healthy
        """
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False 