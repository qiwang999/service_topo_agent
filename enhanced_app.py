from flask import Flask, request, jsonify
from enhanced_agent import EnhancedText2CypherAgent
from database.vector_db_manager import VectorDBManager
import os
import threading
import uuid
import json

# Initialize Flask app
app = Flask(__name__)

# --- Global Components ---
# We manage a global lock to prevent race conditions when reloading the agent.
agent_lock = threading.Lock()

# Initialize the vector database manager globally
vector_db_manager = VectorDBManager()

# Check for the interaction logging switch from environment variables
ENABLE_LOGGING = os.environ.get(
    "ENABLE_INTERACTION_LOGGING", "false").lower() == "true"

# Check for the default run mode from environment variables
DEFAULT_RUN_MODE = os.environ.get("DEFAULT_RUN_MODE", "standard")

# Check for embedding features
ENABLE_EMBEDDINGS = os.environ.get(
    "ENABLE_EMBEDDINGS", "true").lower() == "true"
ENABLE_CACHE = os.environ.get("ENABLE_CACHE", "true").lower() == "true"

# A function to create a new enhanced agent instance


def create_enhanced_agent(run_mode=None):
    print("--- Loading feedback and creating new enhanced agent instance... ---")
    feedback_examples = vector_db_manager.load_feedback_as_examples()
    summarizer_choice = os.environ.get("SUMMARIZER_TYPE", "llm")

    # Use provided run_mode or default from environment
    agent_run_mode = run_mode or DEFAULT_RUN_MODE

    try:
        new_agent = EnhancedText2CypherAgent(
            summarizer_type=summarizer_choice,
            feedback_examples=feedback_examples,
            run_mode=agent_run_mode,
            enable_cache=ENABLE_CACHE,
            enable_embeddings=ENABLE_EMBEDDINGS
        )
        print(f"--- Enhanced Agent Initialized Successfully ---")
        print(f"   Summarizer: {summarizer_choice}")
        print(f"   Run Mode: {agent_run_mode}")
        print(f"   Cache: {ENABLE_CACHE}")
        print(f"   Embeddings: {ENABLE_EMBEDDINGS}")
        print(f"   Feedback examples: {len(feedback_examples)}")
        return new_agent
    except Exception as e:
        print(f"FATAL: Enhanced agent initialization failed: {e}")
        return None


# Initialize the agent for the first time
agent = create_enhanced_agent()


@app.route('/enhanced/chat', methods=['POST'])
def enhanced_chat():
    """Enhanced chat endpoint with embedding features."""
    global agent
    with agent_lock:
        if not agent:
            return jsonify({"error": "Agent is not available."}), 500

        data = request.get_json()
        user_query = data.get('query')
        conversation_history = data.get('history', [])
        run_mode = data.get('run_mode')  # Allow runtime override of run mode

        # Get or create a conversation ID
        conversation_id = data.get('conversation_id') or str(uuid.uuid4())

        if not user_query:
            return jsonify({"error": "Missing 'query'."}), 400

        # If run_mode is specified and different from current agent's mode, create a new agent
        if run_mode and run_mode != agent.run_mode:
            print(f"--- Switching to run mode: {run_mode} ---")
            agent = create_enhanced_agent(run_mode)

        result = agent.run(conversation_history, user_query)
        result['conversation_id'] = conversation_id
        result['run_mode'] = agent.run_mode

        # Enhanced logging with embedding metadata
        if ENABLE_LOGGING:
            try:
                generated_cypher = result.get('generated_cypher', '')
                final_summary = result.get('summary', '')

                # Include embedding metadata in logs
                log_data = {
                    'conversation_id': conversation_id,
                    'question': user_query,
                    'generated_cypher': generated_cypher,
                    'final_summary': final_summary,
                    'cache_hit': result.get('cache_hit', False),
                    'cache_similarity': result.get('cache_similarity'),
                    'prompt_metadata': result.get('prompt_metadata', {})
                }

                print(
                    f"--- Enhanced interaction logged for conversation: {conversation_id} ---")
                if result.get('cache_hit'):
                    print(
                        f"   Cache hit with similarity: {result.get('cache_similarity', 0):.3f}")
                if result.get('prompt_metadata'):
                    metadata = result.get('prompt_metadata', {})
                    print(
                        f"   Examples used: {metadata.get('examples_used', 0)}")
                    print(
                        f"   Feedback used: {metadata.get('feedback_used', 0)}")
                    print(
                        f"   Avg example similarity: {metadata.get('avg_example_similarity', 0):.3f}")

            except Exception as e:
                print(
                    f"Warning: Failed to log enhanced interaction. Error: {e}")

        return jsonify(result)


@app.route('/enhanced/similar-examples', methods=['POST'])
def find_similar_examples():
    """Find similar examples for a given question."""
    data = request.get_json()
    question = data.get('question')
    top_k = data.get('top_k', 5)

    if not question:
        return jsonify({"error": "Missing 'question'."}), 400

    try:
        similar_examples = agent.find_similar_examples(question, top_k)
        return jsonify({
            "question": question,
            "similar_examples": similar_examples,
            "count": len(similar_examples)
        })
    except Exception as e:
        print(f"Error finding similar examples: {e}")
        return jsonify({"error": "Failed to find similar examples."}), 500


@app.route('/enhanced/similar-feedback', methods=['POST'])
def find_similar_feedback():
    """Find similar feedback for a given question."""
    data = request.get_json()
    question = data.get('question')
    top_k = data.get('top_k', 3)

    if not question:
        return jsonify({"error": "Missing 'question'."}), 400

    try:
        similar_feedback = agent.find_similar_feedback(question, top_k)
        return jsonify({
            "question": question,
            "similar_feedback": similar_feedback,
            "count": len(similar_feedback)
        })
    except Exception as e:
        print(f"Error finding similar feedback: {e}")
        return jsonify({"error": "Failed to find similar feedback."}), 500


@app.route('/enhanced/cache-stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics."""
    try:
        stats = agent.get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"Error getting cache stats: {e}")
        return jsonify({"error": "Failed to get cache statistics."}), 500


@app.route('/enhanced/feedback', methods=['POST'])
def enhanced_feedback():
    """Enhanced feedback endpoint that stores embeddings."""
    global agent
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON."}), 400

    question = data.get('question')
    generated_cypher = data.get('generated_cypher')
    correct_cypher = data.get('correct_cypher')
    rating = data.get('rating')

    if not all([question, generated_cypher, correct_cypher, rating]):
        return jsonify({"error": "Missing required feedback fields."}), 400

    try:
        # Save feedback to the database
        vector_db_manager.save_feedback(
            question, generated_cypher, correct_cypher, rating)

        # Store embedding for the feedback if embeddings are enabled
        if ENABLE_EMBEDDINGS:
            vector_db_manager.store_embedding(
                'feedback', question, correct_cypher)
            print(f"--- Stored feedback embedding for: {question[:50]}... ---")

        # Reload the agent with the new feedback in a thread-safe manner
        with agent_lock:
            agent = create_enhanced_agent()

        return jsonify({"message": "Feedback received, embedding stored, and agent reloaded."})
    except Exception as e:
        print(f"Error saving enhanced feedback: {e}")
        return jsonify({"error": "Failed to save feedback."}), 500


@app.route('/enhanced/initialize-embeddings', methods=['POST'])
def initialize_embeddings():
    """Initialize embeddings for existing data."""
    try:
        vector_db_manager.initialize_vector_database()
        return jsonify({"message": "Embeddings initialized successfully."})
    except Exception as e:
        print(f"Error initializing embeddings: {e}")
        return jsonify({"error": "Failed to initialize embeddings."}), 500


if __name__ == '__main__':
    # Running in debug mode is not recommended for production
    app.run(host='0.0.0.0', port=5001, debug=True)
