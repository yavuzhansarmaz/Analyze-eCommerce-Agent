"""
Product analyzer for performance and recommendation insights.
"""

import pandas as pd
from .base import BaseAnalyzer, AnalysisResult, create_insight
from agent.state import AnalysisType

class ProductAnalyzer(BaseAnalyzer):
    """Analyzer for product performance and recommendation insights."""

    def __init__(self):
        super().__init__(AnalysisType.PRODUCT_PERFORMANCE)

    def analyze_performance(self, df: pd.DataFrame) -> AnalysisResult:
        """Analyze product performance metrics."""

        if df.empty:
            return self.handle_empty_dataframe("No product performance data available for analysis.")

        insights = []

        # Top performing products
        if 'total_revenue' in df.columns:
            total_revenue = df['total_revenue'].sum()
            top_products_revenue = df.nlargest(5, 'total_revenue')['total_revenue'].sum()
            concentration = top_products_revenue / total_revenue if total_revenue > 0 else 0

            insights.append(create_insight(
                f"Top 5 products generate {concentration:.1%} of total product revenue, indicating revenue concentration.",
                self.analysis_type,
                confidence=0.9,
                supporting_data={
                    'top_products_concentration': float(concentration),
                    'top_products_revenue': float(top_products_revenue),
                    'total_revenue': float(total_revenue)
                }
            ))

        # Margin analysis
        if 'margin_percentage' in df.columns:
            high_margin_products = len(df[df['margin_percentage'] > 0.3])
            avg_margin = df['margin_percentage'].mean()

            insights.append(create_insight(
                f"{high_margin_products} products have margins above 30%, with average margin of {avg_margin:.1%} across all products.",
                self.analysis_type,
                supporting_data={
                    'high_margin_products': int(high_margin_products),
                    'avg_margin': float(avg_margin)
                }
            ))

        # Recent performance trends
        if 'recent_orders' in df.columns:
            recent_total = df['recent_orders'].sum()
            old_total = df['total_orders'].sum() - recent_total
            growth_rate = (recent_total - old_total) / old_total if old_total > 0 else 0

            insights.append(create_insight(
                f"Recent 90-day orders show {'growth' if growth_rate > 0 else 'decline'} of {abs(growth_rate):.1%} compared to historical performance.",
                self.analysis_type,
                supporting_data={
                    'recent_orders': int(recent_total),
                    'historical_orders': int(old_total),
                    'growth_rate': float(growth_rate)
                }
            ))

        return AnalysisResult(
            analysis_type=self.analysis_type,
            insights=insights,
            summary_stats={
                'total_products': len(df),
                'total_revenue': float(df.get('total_revenue', pd.Series()).sum()),
                'avg_margin': float(df.get('margin_percentage', pd.Series()).mean())
            }
        )

    def analyze_recommendations(self, df: pd.DataFrame) -> AnalysisResult:
        """Analyze product recommendation opportunities."""

        if df.empty:
            return self.handle_empty_dataframe("No product co-occurrence data available for recommendations.")

        insights = []

        # Strongest product relationships
        if 'cooccurrence_count' in df.columns:
            strongest_relationships = df.nlargest(5, 'cooccurrence_count')
            top_relationship = strongest_relationships.iloc[0] if len(strongest_relationships) > 0 else None

            if top_relationship is not None:
                insights.append(create_insight(
                    f"Strongest product relationship: '{top_relationship['product_a_name']}' and '{top_relationship['product_b_name']}' co-occur in {top_relationship['cooccurrence_count']} orders.",
                    AnalysisType.PRODUCT_RECOMMENDATIONS,
                    supporting_data={
                        'product_a': top_relationship['product_a_name'],
                        'product_b': top_relationship['product_b_name'],
                        'cooccurrence_count': int(top_relationship['cooccurrence_count'])
                    }
                ))

        # Category-based recommendations
        if 'product_a_category' in df.columns and 'product_b_category' in df.columns:
            same_category_pairs = len(df[df['product_a_category'] == df['product_b_category']])
            cross_category_pairs = len(df) - same_category_pairs

            insights.append(create_insight(
                f"{same_category_pairs} same-category pairs vs {cross_category_pairs} cross-category pairs suggest {'strong' if same_category_pairs > cross_category_pairs else 'weak'} category cohesion.",
                AnalysisType.PRODUCT_RECOMMENDATIONS,
                supporting_data={
                    'same_category_pairs': int(same_category_pairs),
                    'cross_category_pairs': int(cross_category_pairs)
                }
            ))

        return AnalysisResult(
            analysis_type=AnalysisType.PRODUCT_RECOMMENDATIONS,
            insights=insights,
            summary_stats={
                'total_relationships': len(df),
                'avg_cooccurrence': float(df.get('cooccurrence_count', pd.Series()).mean())
            }
        )