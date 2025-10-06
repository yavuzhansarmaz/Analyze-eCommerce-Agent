"""
Geographic analyzer for sales patterns and insights.
"""

import pandas as pd
from typing import List, Dict, Any
from .base import BaseAnalyzer, AnalysisResult, create_insight
from agent.state import AnalysisType


class GeographicAnalyzer(BaseAnalyzer):
    """Analyzer for geographic sales patterns and insights."""

    def __init__(self):
        super().__init__(AnalysisType.GEOGRAPHIC_PATTERNS)

    def analyze_patterns(self, df: pd.DataFrame) -> AnalysisResult:
        """Analyze geographic distribution of sales."""

        if df.empty:
            return self.handle_empty_dataframe("No geographic data available for analysis.")

        insights = []

        # Top performing regions
        if 'total_revenue' in df.columns and 'state' in df.columns:
            top_states = df.nlargest(5, 'total_revenue')
            top_state = top_states.iloc[0] if len(top_states) > 0 else None

            if top_state is not None:
                insights.append(create_insight(
                    f"{top_state['state']} leads with ${top_state['total_revenue']:,.0f} in revenue across {top_state['total_orders']:,} orders.",
                    AnalysisType.GEOGRAPHIC_PATTERNS,
                    supporting_data={
                        'top_state': top_state['state'],
                        'top_state_revenue': float(top_state['total_revenue']),
                        'top_state_orders': int(top_state['total_orders'])
                    }
                ))

        # Geographic concentration
        if 'total_revenue' in df.columns:
            total_revenue = df['total_revenue'].sum()
            top_3_revenue = df.nlargest(3, 'total_revenue')['total_revenue'].sum()
            concentration = top_3_revenue / total_revenue if total_revenue > 0 else 0

            insights.append(create_insight(
                f"Top 3 regions account for {concentration:.1%} of total revenue, indicating {'high' if concentration > 0.6 else 'moderate' if concentration > 0.4 else 'low'} geographic concentration.",
                AnalysisType.GEOGRAPHIC_PATTERNS,
                supporting_data={
                    'concentration_ratio': float(concentration),
                    'top_3_revenue': float(top_3_revenue),
                    'total_revenue': float(total_revenue)
                }
            ))

        # Customer density insights
        if 'unique_customers' in df.columns and 'state' in df.columns:
            df['orders_per_customer'] = df['total_orders'] / df['unique_customers']
            high_density_states = df[df['orders_per_customer'] > df['orders_per_customer'].quantile(0.75)]

            if len(high_density_states) > 0:
                insights.append(create_insight(
                    f"{len(high_density_states)} states show high customer engagement with above-average orders per customer.",
                    AnalysisType.GEOGRAPHIC_PATTERNS,
                    supporting_data={
                        'high_density_states': len(high_density_states),
                        'states_analyzed': len(df)
                    }
                ))

        return AnalysisResult(
            analysis_type=AnalysisType.GEOGRAPHIC_PATTERNS,
            insights=insights,
            summary_stats={
                'regions_analyzed': len(df),
                'total_revenue': float(df.get('total_revenue', pd.Series()).sum()),
                'total_customers': int(df.get('unique_customers', pd.Series()).sum())
            }
        )