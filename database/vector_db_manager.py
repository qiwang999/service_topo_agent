import sqlite3
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from database.db_manager import DBManager
from tools.embedding_client import EmbeddingClient


class VectorDBManager(DBManager):
    """
    Extended database manager with vector operations and semantic search capabilities.
    """
        
    def __init__(self, db_path: str = "feedback.db"):
        super().__init__(db_path)
        self.embedding_client = EmbeddingClient()
        self._create_vector_tables()

    def _create_vector_tables(self):
        """Create vector-related tables."""
        cursor = self.conn.cursor()

        # Vector embeddings table for examples and feedback
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vector_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_type TEXT NOT NULL,  -- 'example', 'feedback', 'cache'
                text_content TEXT NOT NULL,
                cypher_query TEXT,
                embedding_data TEXT NOT NULL,  -- JSON array of floats
                similarity_threshold REAL DEFAULT 0.8,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Query cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_hash TEXT UNIQUE NOT NULL,
                question TEXT NOT NULL,
                generated_cypher TEXT NOT NULL,
                final_summary TEXT NOT NULL,
                embedding_data TEXT NOT NULL,
                similarity_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1
            )
        """)

        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vector_embeddings_type 
            ON vector_embeddings(text_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_cache_hash 
            ON query_cache(question_hash)
        """)

        self.conn.commit()

    def store_embedding(self, text_type: str, text_content: str,
                        cypher_query: str = None, similarity_threshold: float = 0.8):
        """Store text and its embedding in the database."""
        embedding = self.embedding_client.get_embedding(text_content)
        if not embedding:
            return False

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO vector_embeddings (text_type, text_content, cypher_query, embedding_data, similarity_threshold)
            VALUES (?, ?, ?, ?, ?)
        """, (text_type, text_content, cypher_query, json.dumps(embedding), similarity_threshold))
        self.conn.commit()
        return True

    def find_similar_examples(self, query: str, top_k: int = 5,
                              min_similarity: float = 0.7) -> List[Dict]:
        """Find similar examples based on semantic similarity."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT text_content, cypher_query, embedding_data, similarity_threshold
            FROM vector_embeddings 
            WHERE text_type = 'example'
        """)
        rows = cursor.fetchall()

        if not rows:
            return []

        # Get query embedding
        query_embedding = self.embedding_client.get_embedding(query)
        if not query_embedding:
            return []

        # Calculate similarities
        similarities = []
        for row in rows:
            text_content, cypher_query, embedding_data, threshold = row
            stored_embedding = json.loads(embedding_data)

            similarity = self.embedding_client.cosine_similarity(
                query_embedding, stored_embedding)

            if similarity >= min_similarity:
                similarities.append({
                    'text_content': text_content,
                    'cypher_query': cypher_query,
                    'similarity': similarity,
                    'threshold': threshold
                })

        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]

    def find_similar_feedback(self, query: str, top_k: int = 3,
                              min_similarity: float = 0.8) -> List[Dict]:
        """Find similar feedback based on semantic similarity."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT text_content, cypher_query, embedding_data
            FROM vector_embeddings 
            WHERE text_type = 'feedback'
        """)
        rows = cursor.fetchall()

        if not rows:
            return []

        # Get query embedding
        query_embedding = self.embedding_client.get_embedding(query)
        if not query_embedding:
            return []

        # Calculate similarities
        similarities = []
        for row in rows:
            text_content, cypher_query, embedding_data = row
            stored_embedding = json.loads(embedding_data)

            similarity = self.embedding_client.cosine_similarity(
                query_embedding, stored_embedding)

            if similarity >= min_similarity:
                similarities.append({
                    'text_content': text_content,
                    'cypher_query': cypher_query,
                    'similarity': similarity
                })

        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]

    def cache_query_result(self, question: str, generated_cypher: str,
                           final_summary: str, similarity_score: float = None):
        """Cache a query result for future use."""
        # Create a simple hash of the question
        question_hash = str(hash(question))

        # Get embedding for the question
        embedding = self.embedding_client.get_embedding(question)
        if not embedding:
            return False

        cursor = self.conn.cursor()

        # Check if already exists
        cursor.execute("""
            SELECT id, access_count FROM query_cache WHERE question_hash = ?
        """, (question_hash,))

        existing = cursor.fetchone()

        if existing:
            # Update existing cache entry
            cache_id, access_count = existing
            cursor.execute("""
                UPDATE query_cache 
                SET access_count = ?, last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (access_count + 1, cache_id))
        else:
            # Insert new cache entry
            cursor.execute("""
                INSERT INTO query_cache 
                (question_hash, question, generated_cypher, final_summary, 
                 embedding_data, similarity_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (question_hash, question, generated_cypher, final_summary,
                  json.dumps(embedding), similarity_score))

        self.conn.commit()
        return True

    def find_cached_result(self, question: str, min_similarity: float = 0.9) -> Optional[Dict]:
        """Find a cached result for a similar question."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT question, generated_cypher, final_summary, embedding_data, similarity_score
            FROM query_cache
        """)
        rows = cursor.fetchall()

        if not rows:
            return None

        # Get query embedding
        query_embedding = self.embedding_client.get_embedding(question)
        if not query_embedding:
            return None

        # Find most similar cached result
        best_match = None
        best_similarity = 0

        for row in rows:
            cached_question, generated_cypher, final_summary, embedding_data, _ = row
            stored_embedding = json.loads(embedding_data)

            similarity = self.embedding_client.cosine_similarity(
                query_embedding, stored_embedding)

            if similarity >= min_similarity and similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    'question': cached_question,
                    'generated_cypher': generated_cypher,
                    'final_summary': final_summary,
                    'similarity': similarity
                }

        return best_match

    def get_cache_stats(self) -> Dict:
        """Get statistics about the query cache."""
        cursor = self.conn.cursor()

        # Total cache entries
        cursor.execute("SELECT COUNT(*) FROM query_cache")
        total_entries = cursor.fetchone()[0]

        # Cache hit rate (entries accessed more than once)
        cursor.execute(
            "SELECT COUNT(*) FROM query_cache WHERE access_count > 1")
        accessed_entries = cursor.fetchone()[0]

        # Most accessed entries
        cursor.execute("""
            SELECT question, access_count 
            FROM query_cache 
            ORDER BY access_count DESC 
            LIMIT 5
        """)
        top_accessed = cursor.fetchall()

        # Average access count
        cursor.execute("SELECT AVG(access_count) FROM query_cache")
        avg_access = cursor.fetchone()[0] or 0

        return {
            'total_entries': total_entries,
            'accessed_entries': accessed_entries,
            'hit_rate': (accessed_entries / total_entries * 100) if total_entries > 0 else 0,
            'avg_access_count': avg_access,
            'top_accessed': [{'question': q[:50] + '...' if len(q) > 50 else q, 'count': c}
                             for q, c in top_accessed]
        }

    def initialize_vector_database(self):
        """Initialize the vector database with existing examples and feedback."""
        print("--- Initializing vector database ---")

        # Load existing examples and create embeddings
        examples = self.load_feedback_as_examples()
        for example in examples:
            text_content = example['natural_language']
            cypher_query = example['cypher']

            # Store as example embedding
            self.store_embedding('example', text_content, cypher_query)

        print(f"--- Stored {len(examples)} example embeddings ---")

        # Load existing feedback and create embeddings
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT question, correct_cypher FROM feedback WHERE rating > 3
        """)
        feedback_rows = cursor.fetchall()

        for row in feedback_rows:
            question, correct_cypher = row
            self.store_embedding('feedback', question, correct_cypher)

        print(f"--- Stored {len(feedback_rows)} feedback embeddings ---")
