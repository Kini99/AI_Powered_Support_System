from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo 
from backend.app.db.base import get_redis

class AnalyticsService:
    def __init__(self):
        self.redis = get_redis()

    def _get_key(self, metric: str, date: str = None):
        if date is None:
            IST = ZoneInfo('Asia/Kolkata')
            date = datetime.now(IST).strftime('%Y-%m-%d')
        return f"analytics:{date}:{metric}"

    def log_event(self, event_type: str, data: Dict[str, Any] = None):
        """
        Log a key event for analytics.
        :param event_type: Type of the event (e.g., 'ticket_created', 'agent_resolved', 'human_resolved', 'escalated', 'cache_hit').
        :param data: Additional data associated with the event (e.g., {'category': 'Course Query', 'confidence': 0.95}).
        """
        key = self._get_key(event_type)
        self.redis.incr(key)

        if data and 'category' in data:
            category_key = self._get_key(f"{event_type}_by_category:{data['category']}")
            self.redis.incr(category_key)

        if event_type == 'agent_resolved' and 'confidence' in data:
            confidence_key = self._get_key('agent_confidence_scores')
            self.redis.rpush(confidence_key, data['confidence'])

    def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """
        Compute and retrieve analytics over a given number of days.
        """
        today = datetime.utcnow()
        dates = [(today - timedelta(days=d)).strftime('%Y-%m-%d') for d in range(days)]

        metrics_to_fetch = ['agent_resolved', 'human_resolved', 'escalated', 'cache_hit']
        
        daily_data = {metric: {} for metric in metrics_to_fetch}
        totals = {metric: 0 for metric in metrics_to_fetch}
        total_confidence_scores = []

        for date in dates:
            for metric in metrics_to_fetch:
                key = self._get_key(metric, date)
                value = self.redis.get(key)
                count = int(value) if value else 0
                daily_data[metric][date] = count
                totals[metric] += count

            confidence_key = self._get_key('agent_confidence_scores', date)
            scores = self.redis.lrange(confidence_key, 0, -1)
            total_confidence_scores.extend([float(s) for s in scores])
            
        total_agent_resolutions = totals['agent_resolved']
        total_escalations = totals['escalated']
        
        agent_success_rate = 0
        if (total_agent_resolutions + total_escalations) > 0:
            agent_success_rate = round((total_agent_resolutions / (total_agent_resolutions + total_escalations)) * 100, 2)
            
        avg_confidence = 0
        if total_confidence_scores:
            avg_confidence = round(sum(total_confidence_scores) / len(total_confidence_scores) * 100, 2)

        # RAGAS metrics - these would be populated by a separate, periodic evaluation process
        ragas_metrics = {
            "faithfulness": 0.92, # Example value
            "answer_relevancy": 0.89, # Example value
            "context_precision": 0.95, # Example value
            "context_recall": 0.91, # Example value
            "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        }

        return {
            "summary": {
                "total_agent_resolved": totals['agent_resolved'],
                "total_human_resolved": totals['human_resolved'],
                "total_escalated": totals['escalated'],
                "agent_success_rate": agent_success_rate,
                "average_confidence_score": avg_confidence,
                "cache_hits": totals['cache_hit']
            },
            "daily_trends": daily_data,
            "ragas_evaluation": ragas_metrics
        }

analytics_service = AnalyticsService()