"""
Specialized data analyzers for e-commerce insights.
This module provides a unified interface for all analyzer classes.
"""

import logging
from agent.state import AnalysisType

# Import all analyzer classes from the analyzers package
from .analyzers import BaseAnalyzer, AnalysisResult, create_insight
from .analyzers import CustomerAnalyzer, ProductAnalyzer, SalesAnalyzer, GeographicAnalyzer

logger = logging.getLogger(__name__)

# Convenience function for backward compatibility
def get_analyzer(analysis_type: AnalysisType) -> BaseAnalyzer:
    """Factory function to get the appropriate analyzer for a given analysis type."""
    if analysis_type == AnalysisType.CUSTOMER_SEGMENTATION or analysis_type == AnalysisType.CUSTOMER_BEHAVIOR:
        return CustomerAnalyzer()
    elif analysis_type == AnalysisType.PRODUCT_PERFORMANCE or analysis_type == AnalysisType.PRODUCT_RECOMMENDATIONS:
        return ProductAnalyzer()
    elif analysis_type == AnalysisType.SALES_TRENDS or analysis_type == AnalysisType.SALES_SEASONALITY:
        return SalesAnalyzer()
    elif analysis_type == AnalysisType.GEOGRAPHIC_PATTERNS:
        return GeographicAnalyzer()
    else:
        raise ValueError(f"No analyzer available for analysis type: {analysis_type}")

# Export all classes for external use
__all__ = [
    'BaseAnalyzer',
    'AnalysisResult',
    'create_insight',
    'CustomerAnalyzer',
    'ProductAnalyzer',
    'SalesAnalyzer',
    'GeographicAnalyzer',
    'get_analyzer'
]