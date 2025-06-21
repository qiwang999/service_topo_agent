import sqlite3
import json
from typing import List, Dict

class DBManager:
    """
    Manages all interactions with the SQLite database for feedback storage.
    """
    def __init__(self, db_path: str = "feedback.db"):
        """
        Initializes the DBManager and connects to the SQLite database.
        
        Args:
            db_path (str): The path to the SQLite database file.
        """
        self.db_path = db_path
        # `check_same_thread=False` is required for multi-threaded access, e.g., in a web server.
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        """Creates the feedback table if it doesn't already exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                generated_cypher TEXT NOT NULL,
                correct_cypher TEXT NOT NULL,
                rating INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                question TEXT NOT NULL,
                generated_cypher TEXT,
                final_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def save_feedback(self, question: str, generated_cypher: str, correct_cypher: str, rating: int):
        """Saves a new piece of feedback to the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO feedback (question, generated_cypher, correct_cypher, rating)
            VALUES (?, ?, ?, ?)
        """, (question, generated_cypher, correct_cypher, rating))
        self.conn.commit()

    def log_interaction(self, conversation_id: str, question: str, generated_cypher: str, final_summary: str):
        """Logs a full agent interaction to the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO interaction_logs (conversation_id, question, generated_cypher, final_summary)
            VALUES (?, ?, ?, ?)
        """, (conversation_id, question, generated_cypher, final_summary))
        self.conn.commit()

    def load_feedback_as_examples(self) -> List[Dict]:
        """
        Loads high-quality feedback from the database to be used as few-shot examples.
        - Only feedback with a rating > 3 is considered high-quality.
        - Fetches the most recent 20 examples to keep the prompt concise.
        """
        cursor = self.conn.cursor()
        # We only want to learn from good examples provided by the user.
        cursor.execute("""
            SELECT question, correct_cypher FROM feedback 
            WHERE rating > 3 
            ORDER BY created_at DESC 
            LIMIT 20
        """)
        rows = cursor.fetchall()
        
        examples = []
        for row in rows:
            examples.append({
                "natural_language": row[0],
                "cypher": row[1]
            })
        return examples

    def __del__(self):
        """Ensure the database connection is closed when the object is destroyed."""
        if self.conn:
            self.conn.close() 