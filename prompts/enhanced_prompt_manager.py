import json
from typing import List, Dict, Optional
from database.vector_db_manager import VectorDBManager


class EnhancedPromptManager:
    """
    Enhanced prompt manager with semantic search and dynamic example selection.
    """

    def __init__(self, vector_db_manager: VectorDBManager,
                 base_prompt_template: str = None,
                 examples_file_path: str = "examples.json",
                 default_similarity_method: str = 'cosine'):
        self.vector_db_manager = vector_db_manager
        self.base_prompt_template = base_prompt_template or self._get_default_prompt()
        self.examples_file_path = examples_file_path
        self.default_similarity_method = default_similarity_method

    def _get_default_prompt(self) -> str:
        """Get the default prompt template."""
        return """你是一个专业的Neo4j Cypher查询生成器，专门用于服务拓扑分析。

你的任务是将自然语言问题转换为准确的Cypher查询语句。

数据库模式：
{db_schema}

请根据以下示例来理解查询模式：

{examples}

用户问题：{question}

请生成一个Cypher查询语句，只返回查询语句，不要包含任何解释或额外文本。"""

    def get_dynamic_examples(self, question: str, max_examples: int = 5,
                           similarity_method: str = None) -> List[Dict]:
        """
        Get dynamically selected examples based on semantic similarity.

        Args:
            question (str): The user's question
            max_examples (int): Maximum number of examples to return
            similarity_method (str): Similarity method to use

        Returns:
            List[Dict]: List of similar examples
        """
        if similarity_method is None:
            similarity_method = self.default_similarity_method
            
        # Find similar examples using semantic search
        similar_examples = self.vector_db_manager.find_similar_examples(
            question, top_k=max_examples, min_similarity=0.7,
            method=similarity_method
        )

        # Convert to the expected format
        examples = []
        for example in similar_examples:
            examples.append({
                'natural_language': example['text_content'],
                'cypher': example['cypher_query'],
                'similarity': example['similarity']
            })

        # If we don't have enough similar examples, add some from static examples
        if len(examples) < max_examples:
            static_examples = self._load_static_examples()
            remaining_count = max_examples - len(examples)

            for i, static_example in enumerate(static_examples[:remaining_count]):
                examples.append({
                    'natural_language': static_example['natural_language'],
                    'cypher': static_example['cypher'],
                    'similarity': 0.0  # Static examples have no similarity score
                })

        return examples

    def get_similar_feedback(self, question: str, max_feedback: int = 3,
                           similarity_method: str = None) -> List[Dict]:
        """
        Get similar feedback based on semantic similarity.

        Args:
            question (str): The user's question
            max_feedback (int): Maximum number of feedback items to return
            similarity_method (str): Similarity method to use

        Returns:
            List[Dict]: List of similar feedback
        """
        if similarity_method is None:
            similarity_method = self.default_similarity_method
            
        similar_feedback = self.vector_db_manager.find_similar_feedback(
            question, top_k=max_feedback, min_similarity=0.8,
            method=similarity_method
        )

        return similar_feedback

    def _load_static_examples(self) -> List[Dict]:
        """Load static examples from the examples file."""
        try:
            with open(self.examples_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(
                f"Warning: Examples file {self.examples_file_path} not found")
            return []
        except json.JSONDecodeError:
            print(
                f"Warning: Invalid JSON in examples file {self.examples_file_path}")
            return []

    def format_examples_for_prompt(self, examples: List[Dict]) -> str:
        """
        Format examples for inclusion in the prompt.

        Args:
            examples (List[Dict]): List of examples with similarity scores

        Returns:
            str: Formatted examples string
        """
        if not examples:
            return "无示例"

        formatted_examples = []
        for i, example in enumerate(examples, 1):
            similarity_info = f" (相似度: {example.get('similarity', 0):.2f})" if example.get(
                'similarity') else ""
            formatted_examples.append(
                f"示例{i}{similarity_info}:\n"
                f"问题: {example['natural_language']}\n"
                f"Cypher: {example['cypher']}\n"
            )

        return "\n".join(formatted_examples)

    def create_enhanced_prompt(self, question: str, db_schema: str,
                             use_dynamic_examples: bool = True,
                             include_feedback: bool = True,
                             similarity_method: str = None) -> str:
        """
        Create an enhanced prompt with dynamic example selection.

        Args:
            question (str): The user's question
            db_schema (str): Database schema
            use_dynamic_examples (bool): Whether to use dynamic example selection
            include_feedback (bool): Whether to include similar feedback
            similarity_method (str): Similarity method to use

        Returns:
            str: Enhanced prompt
        """
        if similarity_method is None:
            similarity_method = self.default_similarity_method
            
        # Get examples
        if use_dynamic_examples:
            examples = self.get_dynamic_examples(question, similarity_method=similarity_method)
        else:
            static_examples = self._load_static_examples()
            examples = [{'natural_language': ex['natural_language'],
                        'cypher': ex['cypher'], 'similarity': 0.0}
                        for ex in static_examples[:5]]

        # Get similar feedback if requested
        feedback_examples = []
        if include_feedback:
            feedback_examples = self.get_similar_feedback(question, similarity_method=similarity_method)

        # Format examples
        examples_text = self.format_examples_for_prompt(examples)

        # Add feedback examples if available
        if feedback_examples:
            feedback_text = "\n\n用户反馈示例:\n"
            for i, feedback in enumerate(feedback_examples, 1):
                feedback_text += (
                    f"反馈{i} (相似度: {feedback['similarity']:.2f}):\n"
                    f"问题: {feedback['text_content']}\n"
                    f"正确Cypher: {feedback['cypher_query']}\n\n"
                )
            examples_text += feedback_text

        # Create the prompt
        prompt = self.base_prompt_template.format(
            db_schema=db_schema,
            examples=examples_text,
            question=question
        )

        return prompt

    def get_prompt_metadata(self, question: str, similarity_method: str = None) -> Dict:
        """
        Get metadata about the prompt generation process.

        Args:
            question (str): The user's question
            similarity_method (str): Similarity method used

        Returns:
            Dict: Metadata about examples and feedback used
        """
        if similarity_method is None:
            similarity_method = self.default_similarity_method
            
        examples = self.get_dynamic_examples(question, similarity_method=similarity_method)
        feedback = self.get_similar_feedback(question, similarity_method=similarity_method)

        return {
            'examples_used': len(examples),
            'feedback_used': len(feedback),
            'similarity_method': similarity_method,
            'example_similarities': [ex.get('similarity', 0) for ex in examples],
            'feedback_similarities': [fb.get('similarity', 0) for fb in feedback],
            'avg_example_similarity': sum(ex.get('similarity', 0) for ex in examples) / len(examples) if examples else 0,
            'avg_feedback_similarity': sum(fb.get('similarity', 0) for fb in feedback) / len(feedback) if feedback else 0
        }

    def set_similarity_method(self, method: str):
        """
        Set the default similarity method to use.
        
        Args:
            method (str): Similarity method ('cosine', 'euclidean', etc.)
        """
        self.default_similarity_method = method
        print(f"--- Default similarity method changed to: {method} ---")
