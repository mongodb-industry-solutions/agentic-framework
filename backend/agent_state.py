from typing import Any, List, Literal, Optional
from typing_extensions import TypedDict

# --- Define State Types ---

class TelemetryRecord(TypedDict):
    timestamp: str
    engine_temperature: str
    oil_pressure: str
    avg_fuel_consumption: str

class SimilarIssue(TypedDict):
    issue: str
    recommendation: str

class AgentState(TypedDict):
    issue_report: str
    chain_of_thought: str
    telemetry_data: List[TelemetryRecord]
    embedding_vector: List[float]
    similar_issues_list: List[SimilarIssue]
    recommendation_text: str
    next_step: Literal[
        "reasoning_node", "data_from_csv", "embedding_node",
        "vector_search", "persistence_node", "recommendation_node", "end"
    ]
    updates: List[str]
    thread_id: Optional[str]