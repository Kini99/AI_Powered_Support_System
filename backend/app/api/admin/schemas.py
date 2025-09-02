from pydantic import BaseModel
from typing import Dict, Any, List

class AnalyticsSummary(BaseModel):
    total_agent_resolved: int
    total_human_resolved: int
    total_escalated: int
    agent_success_rate: float
    average_confidence_score: float
    cache_hits: int

class RagasEvaluation(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    last_updated: str

class AnalyticsResponse(BaseModel):
    summary: AnalyticsSummary
    daily_trends: Dict[str, Dict[str, int]]
    ragas_evaluation: RagasEvaluation