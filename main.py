import json
from agent import Text2CypherAgent

if __name__ == "__main__":
    """
    Main execution block to run the Text2Cypher agent.
    """
    print("--- Starting Cypher Generation Agent ---")
    
    try:
        # --- CHOOSE YOUR SUMMARIZER ---
        # summarizer_choice = 'llm'  # For natural language summary
        summarizer_choice = 'manual' # For structured data for a frontend
        
        # 1. Initialize the agent with the chosen summarizer type
        agent = Text2CypherAgent(summarizer_type=summarizer_choice)
        
        # 2. Define the natural language query
        natural_language_query = "Which services does the 'api-gateway' depend on?"
        print(f"User Query: {natural_language_query}\n")
        
        # 3. Run the agent with the query
        result = agent.run(natural_language_query)

        # 4. Print the results
        print("\n--- Agent Finished ---")
        print("\nFinal Generated Cypher:")
        print(result["generated_cypher"])
        
        print(f"\nFinal Summary (type: {summarizer_choice}):")
        # If the summary is a JSON string, pretty-print it. Otherwise, print as is.
        try:
            summary_data = json.loads(result["summary"])
            print(json.dumps(summary_data, indent=2))
        except (json.JSONDecodeError, TypeError):
            print(result["summary"])
        
        print("\nRaw Query Result:")
        print(json.dumps(result["raw_json_result"], indent=2))
        
        print(f"\nRetries: {result['retries']}")

    except (ValueError, ConnectionError) as e:
        print(f"Initialization failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
