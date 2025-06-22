from langchain_core.messages import HumanMessage, AIMessage
from typing import Dict, Optional
from prompts.enhanced_prompt_manager import EnhancedPromptManager


class EnhancedCypherGeneratorNode:
    """
    Enhanced Cypher generator node with caching and semantic search capabilities.
    """
    
    def __init__(self, llm, enhanced_prompt_manager: EnhancedPromptManager,
                 vector_db_manager, enable_cache: bool = True,
                 similarity_method: str = 'cosine'):
        self.llm = llm
        self.enhanced_prompt_manager = enhanced_prompt_manager
        self.vector_db_manager = vector_db_manager
        self.enable_cache = enable_cache
        self.similarity_method = similarity_method

    def generate(self, state, db_schema: str) -> Dict:
        """
        Generate Cypher query with enhanced features.

        Args:
            state: Current graph state
            db_schema: Database schema

        Returns:
            Dict: Updated state with generated Cypher
        """
        # Get the latest user message
        messages = state.get("messages", [])
        if not messages:
            return state

        latest_message = messages[-1]
        if not isinstance(latest_message, HumanMessage):
            return state

        question = latest_message.content

        # Check cache first if enabled
        if self.enable_cache:
            cached_result = self.vector_db_manager.find_cached_result(
                question, method=self.similarity_method)
            if cached_result:
                print(
                    f"--- Cache hit! Similarity ({self.similarity_method}): {cached_result['similarity']:.3f} ---")
                state["messages"].append(
                    AIMessage(content=cached_result['generated_cypher']))
                state["generation"] = cached_result['generated_cypher']
                state["summary"] = cached_result['final_summary']
                state["cache_hit"] = True
                state["cache_similarity"] = cached_result['similarity']
                state["similarity_method"] = self.similarity_method
                return state

        # Create enhanced prompt with dynamic examples
        prompt = self.enhanced_prompt_manager.create_enhanced_prompt(
            question=question,
            db_schema=db_schema,
            use_dynamic_examples=True,
            include_feedback=True,
            similarity_method=self.similarity_method
        )

        # Get prompt metadata for logging
        prompt_metadata = self.enhanced_prompt_manager.get_prompt_metadata(
            question, similarity_method=self.similarity_method)

        # Generate Cypher using LLM
        try:
            response = self.llm.invoke(prompt)
            generated_cypher = response.content.strip()

            # Update state
            state["messages"].append(AIMessage(content=generated_cypher))
            state["generation"] = generated_cypher
            state["prompt_metadata"] = prompt_metadata
            state["similarity_method"] = self.similarity_method

            # Cache the result if enabled
            if self.enable_cache:
                self.vector_db_manager.cache_query_result(
                    question=question,
                    generated_cypher=generated_cypher,
                    final_summary="",  # Will be filled by summarizer
                    similarity_score=prompt_metadata.get(
                        'avg_example_similarity', 0)
                )

            print(f"--- Generated Cypher with {prompt_metadata['examples_used']} examples, "
                  f"{prompt_metadata['feedback_used']} feedback items "
                  f"(similarity method: {self.similarity_method}) ---")

        except Exception as e:
            print(f"Error generating Cypher: {e}")
            state["messages"].append(
                AIMessage(content="Error generating Cypher query"))
            state["generation"] = ""

        return state

    def get_similar_queries(self, question: str, top_k: int = 5,
                          method: str = None) -> list:
        """
        Get similar queries from cache.

        Args:
            question (str): The question to find similar queries for
            top_k (int): Number of similar queries to return
            method (str): Similarity method to use (defaults to instance method)

        Returns:
            list: List of similar queries
        """
        if method is None:
            method = self.similarity_method
            
        # This would be implemented to search through cached queries
        # For now, return empty list
        return []

    def set_similarity_method(self, method: str):
        """
        Set the similarity method to use for future operations.
        
        Args:
            method (str): Similarity method ('cosine', 'euclidean', etc.)
        """
        self.similarity_method = method
        print(f"--- Similarity method changed to: {method} ---")
