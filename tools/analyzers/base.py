"""
Base analyzer class and common utilities for all analyzers.
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
import logging
from agent.state import AnalysisType, Insight


def create_insight(content: str, analysis_type: AnalysisType, confidence: float = 1.0,
                  supporting_data: Optional[Dict[str, Any]] = None) -> Insight:
    """Create an Insight with consistent defaults."""
    return Insight(
        content=content,
        confidence=confidence,
        analysis_type=analysis_type,
        supporting_data=supporting_data
    )


@dataclass
class AnalysisResult:
    """Container for analysis results and insights."""
    analysis_type: AnalysisType
    insights: List[Insight]
    summary_stats: Dict[str, Any]
    visualizations: Optional[Dict[str, Any]] = None
    recommendations: List[str] = None


class BaseAnalyzer:
    """Base class for all analyzers to eliminate repetitive code patterns."""

    def __init__(self, analysis_type: AnalysisType):
        self.analysis_type = analysis_type

    def handle_empty_dataframe(self, empty_message: str) -> AnalysisResult:
        """Create a standard AnalysisResult for empty DataFrames."""
        return AnalysisResult(
            analysis_type=self.analysis_type,
            insights=[create_insight(empty_message, self.analysis_type)],
            summary_stats={}
        )

    def analyze(self, df: pd.DataFrame) -> AnalysisResult:
        """Template method for analysis - should be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement analyze method")


logger = logging.getLogger(__name__)