# --- Define Prompt Generation Functions ---

def get_chain_of_thoughts_prompt(profile: str, rules: str, goals: str, issue_report: str, agent_motive: str,
                                 agent_data_consumed: str, embedding_model_name: str, chat_completion_model_name: str) -> str:
    """
    Generate a prompt for the chain of thoughts reasoning.

    Args:
        profile (str): Instructions for the agent profile.
        rules (str): Rules for the agent profile.
        goals (str): Goals for the agent profile.
        issue_report (str): Issue report to be used by the agent.
        agent_motive (str): Motive for the agent.
        agent_data_consumed (str): Data consumed by the agent.
        embedding_model_name (str): Name of the embedding model.
        chat_completion_model_name (str): Name of the chat completion model.

    Returns:
        str: The prompt for the chain of thoughts reasoning
    """

    return f"""
        Agent Profile:
        Instructions: {profile}
        Rules: {rules}
        Goals: {goals}


        You are an AI agent designed to {agent_motive}. Given the issue report:
        {issue_report}
        
        Generate a detailed chain-of-thought reasoning that outlines the following steps:
        1. Consume {agent_data_consumed}.
        2. Generate an embedding for the complaint using {embedding_model_name}
        3. Perform a vector search on past issues in MongoDB Atlas.
        4. Persist {agent_data_consumed} into MongoDB.
        5. Use {chat_completion_model_name}'s ChatCompletion model to generate a final summary and recommendation.
        
        Please provide your chain-of-thought as a numbered list with explanations for each step.
        """


def get_llm_recommendation_prompt(critical_info: str, telemetry_data: str, similar_issues: str) -> str:
    """
    Generate a prompt for the LLM recommendation.

    Args:
        critical_info (str): Critical information for the vehicle maintenance advisor.
        telemetry_data (str): Telemetry data for the vehicle.
        similar_issues (str): Similar past issues for the vehicle.

    Returns:
        str: The prompt for the LLM recommendation
    """

    return f"""
        You are a vehicle maintenance advisor. {critical_info} 
        
        Given the following telemetry data and past similar issues, please analyze the data and recommend an immediate action (continue driving, pull off the road, or schedule maintenance) with a clear explanation.
        
        Telemetry Data: {telemetry_data}

        Similar Past Issues: {similar_issues}
        """