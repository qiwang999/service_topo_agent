import json
from agent import Text2CypherAgent
from langchain_core.messages import AIMessage

def main():
    """
    Main execution block to run the Text2Cypher agent in a conversational loop.
    """
    print("--- Starting Service Topology Agent (Conversational) ---")
    print("Type 'exit' or 'quit' to end the conversation.")
    
    try:
        # --- CHOOSE YOUR SUMMARIZER ---
        summarizer_choice = 'llm'  # 'llm' or 'manual'
        
        # 1. Initialize the agent
        agent = Text2CypherAgent(summarizer_type=summarizer_choice)
        
        # This list will store the conversation history
        conversation_history = []

        while True:
            # 2. Get user input
            user_query = input("\n👤 You: ")
            if user_query.lower() in ["exit", "quit"]:
                print("🤖 Agent: Goodbye!")
                break

            # 3. Run the agent with the current history and new query
            final_state = agent.run(conversation_history, user_query)
            
            # 4. Extract the summary and update history
            summary = final_state.get("summary", "I'm sorry, I couldn't process that.")
            
            # Update history with the user's query and the agent's summary response
            # Note: We only add the final summary to the history for the next turn's context.
            conversation_history = final_state["messages"]


            # 5. Print the agent's response to the user
            print(f"🤖 Agent: {summary}")

            # Optional: Print debug info
            # print("\n--- DEBUG INFO ---")
            # print(f"Generated Cypher: {final_state.get('generation')}")
            # print(f"Retries: {final_state.get('retries')}")
            # print("--- END DEBUG ---\n")


    except (ValueError, ConnectionError) as e:
        print(f"Initialization failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
