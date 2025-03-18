from langgraph.graph import StateGraph, END
from agent_state import AgentState
from agent_tools import get_data_from_csv_tool, vector_search_tool, generate_chain_of_thought_tool, process_data_tool, get_query_embedding_tool, process_vector_search_tool, persist_data_tool, get_llm_recommendation_tool, route_by_telemetry_severity_tool

# --- Create LangGraph StateGraph ---
def create_workflow_graph(checkpointer=None):
    """
    Create the LangGraph StateGraph for the agent workflow.

    Args:
        checkpointer (AgentCheckpointer, optional): AgentCheckpointer instance. Default is None.

    Returns:
        StateGraph: LangGraph StateGraph for the agent workflow
    """
    graph = StateGraph(AgentState)
    graph.add_node("reasoning_node", generate_chain_of_thought_tool)
    graph.add_node("data_from_csv", get_data_from_csv_tool)
    graph.add_node("process_data", process_data_tool)
    graph.add_node("embedding_node", get_query_embedding_tool)
    graph.add_node("vector_search", vector_search_tool)
    graph.add_node("process_vector_search", process_vector_search_tool)
    graph.add_node("persistence_node", persist_data_tool)
    graph.add_node("recommendation_node", get_llm_recommendation_tool)
    graph.add_edge("reasoning_node", "data_from_csv")
    graph.add_edge("data_from_csv", "process_data")
    graph.add_conditional_edges("process_data", route_by_telemetry_severity_tool)
    graph.add_edge("embedding_node", "vector_search")
    graph.add_edge("vector_search", "process_vector_search")
    graph.add_edge("process_vector_search", "persistence_node")
    graph.add_edge("persistence_node", "recommendation_node")
    graph.add_edge("recommendation_node", END)
    graph.set_entry_point("reasoning_node")
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        return graph.compile()