from flask import Flask, request, jsonify
from agent import Text2CypherAgent
from database.db_manager import DBManager
import os
import threading
import uuid

# Initialize Flask app
app = Flask(__name__)

# --- Global Components ---
# We manage a global lock to prevent race conditions when reloading the agent.
agent_lock = threading.Lock()

# Initialize the database manager globally
db_manager = DBManager()

# Check for the interaction logging switch from environment variables
ENABLE_LOGGING = os.environ.get("ENABLE_INTERACTION_LOGGING", "false").lower() == "true"

# Check for the default run mode from environment variables
DEFAULT_RUN_MODE = os.environ.get("DEFAULT_RUN_MODE", "standard")

# A function to create a new agent instance. This will be called on startup
# and every time feedback is submitted.
def create_agent(run_mode=None):
    print("--- Loading feedback and creating new agent instance... ---")
    feedback_examples = db_manager.load_feedback_as_examples()
    summarizer_choice = os.environ.get("SUMMARIZER_TYPE", "llm")
    
    # Use provided run_mode or default from environment
    agent_run_mode = run_mode or DEFAULT_RUN_MODE
    
    try:
        new_agent = Text2CypherAgent(
            summarizer_type=summarizer_choice,
            feedback_examples=feedback_examples,
            run_mode=agent_run_mode
        )
        print(f"--- Agent Initialized Successfully (Summarizer: {summarizer_choice}, Run Mode: {agent_run_mode}, Feedback examples: {len(feedback_examples)}) ---")
        return new_agent
    except Exception as e:
        print(f"FATAL: Agent initialization failed: {e}")
        return None

# Initialize the agent for the first time
agent = create_agent()
# -------------------------

@app.route('/chat', methods=['POST'])
def chat():
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

        if not user_query: return jsonify({"error": "Missing 'query'."}), 400

        # If run_mode is specified and different from current agent's mode, create a new agent
        if run_mode and run_mode != agent.run_mode:
            print(f"--- Switching to run mode: {run_mode} ---")
            agent = create_agent(run_mode)

        result = agent.run(conversation_history, user_query)
        result['conversation_id'] = conversation_id # Return the ID to the client
        result['run_mode'] = agent.run_mode  # Include current run mode in response

        # --- Interaction Logging ---
        if ENABLE_LOGGING:
            try:
                db_manager.log_interaction(
                    conversation_id=conversation_id,
                    question=user_query,
                    generated_cypher=result.get('generated_cypher'),
                    final_summary=result.get('summary')
                )
                print(f"--- Logged interaction for conversation: {conversation_id} ---")
            except Exception as e:
                # We don't want logging failure to break the chat
                print(f"Warning: Failed to log interaction. Error: {e}")
        # -------------------------
        
        return jsonify(result)


@app.route('/feedback', methods=['POST'])
def feedback():
    global agent
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid JSON."}), 400
    
    question = data.get('question')
    generated_cypher = data.get('generated_cypher')
    correct_cypher = data.get('correct_cypher')
    rating = data.get('rating')

    if not all([question, generated_cypher, correct_cypher, rating]):
        return jsonify({"error": "Missing required feedback fields."}), 400

    try:
        # Save feedback to the database
        db_manager.save_feedback(question, generated_cypher, correct_cypher, rating)
        
        # Reload the agent with the new feedback in a thread-safe manner
        with agent_lock:
            agent = create_agent()
        
        return jsonify({"message": "Feedback received and agent reloaded."})
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return jsonify({"error": "Failed to save feedback."}), 500


if __name__ == '__main__':
    # Running in debug mode is not recommended for production
    app.run(host='0.0.0.0', port=5000, debug=True) 