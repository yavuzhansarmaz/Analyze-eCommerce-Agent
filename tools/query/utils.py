"""
Utility functions for query building operations.
"""

from agent.state import AnalysisContext


def add_time_range_filter(base_query: str, context: AnalysisContext) -> str:
    """Add time range filter to a query if specified in context."""
    if context.time_range:
        start_date = context.time_range.get('start')
        end_date = context.time_range.get('end')
        if start_date:
            base_query += f" AND o.created_at >= '{start_date}'"
        if end_date:
            base_query += f" AND o.created_at <= '{end_date}'"
    return base_query


def add_default_time_filter(base_query: str, default_days: int = 730) -> str:
    """Add default time filter if no specific time range is provided."""
    return base_query + f" AND o.created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL {default_days} DAY)"