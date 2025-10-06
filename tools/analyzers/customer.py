"""
Customer analyzer for segmentation and behavior insights.
"""

import pandas as pd
from typing import List, Dict, Any
from .base import BaseAnalyzer, AnalysisResult, create_insight
from agent.state import AnalysisType


class CustomerAnalyzer(BaseAnalyzer):
    """Analyzer for customer segmentation and behavior insights."""

    def __init__(self):
        super().__init__(AnalysisType.CUSTOMER_SEGMENTATION)
        self.segment_colors = {
            'Champions': 'green',
            'Loyal Customers': 'blue',
            'Regular Customers': 'orange',
            'New Customers': 'purple',
            'At Risk': 'red',
            'Lost Customers': 'gray'
        }

    def analyze_segmentation(self, df: pd.DataFrame) -> AnalysisResult:
        """Analyze customer segmentation from RFM data."""

        if df.empty:
            return self.handle_empty_dataframe("No customer data available for segmentation analysis.")

        insights = []

        # Basic segmentation statistics
        total_customers = len(df)
        segment_counts = df['customer_segment'].value_counts()
        segment_percentages = (segment_counts / total_customers * 100).round(1)

        # Generate insights
        insights.append(create_insight(
            f"Customer base segmented into {len(segment_counts)} distinct groups with {total_customers:,} total customers.",
            self.analysis_type,
            supporting_data={
                'total_customers': total_customers,
                'segment_counts': segment_counts.to_dict(),
                'segment_percentages': segment_percentages.to_dict()
            }
        ))

        # Analyze each segment
        for segment, count in segment_counts.items():
            percentage = segment_percentages[segment]

            if segment == 'Champions':
                insights.append(create_insight(
                    f"Champions represent {percentage}% of customers but likely drive significant revenue through high recency and frequency scores.",
                    self.analysis_type,
                    confidence=0.9,
                    supporting_data={
                        'segment': segment,
                        'count': int(count),
                        'percentage': float(percentage)
                    }
                ))
            elif segment == 'At Risk':
                insights.append(create_insight(
                    f"At Risk customers ({percentage}%) haven't purchased recently and may need re-engagement campaigns.",
                    self.analysis_type,
                    confidence=0.8,
                    supporting_data={
                        'segment': segment,
                        'count': int(count),
                        'percentage': float(percentage)
                    }
                ))

        # Demographic insights
        if 'age' in df.columns and not df['age'].isna().all():
            avg_age = df['age'].mean()
            insights.append(create_insight(
                f"Average customer age is {avg_age:.1f} years across all segments.",
                self.analysis_type,
                supporting_data={'average_age': float(avg_age)}
            ))

        # Revenue concentration
        top_segment_revenue = df.groupby('customer_segment')['total_spent'].sum().max()
        total_revenue = df['total_spent'].sum()
        concentration_ratio = top_segment_revenue / total_revenue if total_revenue > 0 else 0

        insights.append(create_insight(
            f"The highest-value segment accounts for {concentration_ratio:.1%} of total customer revenue.",
            self.analysis_type,
            confidence=0.9,
            supporting_data={
                'concentration_ratio': float(concentration_ratio),
                'top_segment_revenue': float(top_segment_revenue),
                'total_revenue': float(total_revenue)
            }
        ))

        # Generate recommendations
        recommendations = self._generate_segmentation_recommendations(df)

        return AnalysisResult(
            analysis_type=self.analysis_type,
            insights=insights,
            summary_stats={
                'total_customers': total_customers,
                'segments': len(segment_counts),
                'segment_distribution': segment_counts.to_dict(),
                'avg_customer_value': float(df['total_spent'].mean()) if 'total_spent' in df.columns else 0
            },
            recommendations=recommendations
        )

    def _generate_segmentation_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate actionable recommendations based on segmentation analysis."""

        recommendations = []

        segment_counts = df['customer_segment'].value_counts()

        # Champions recommendations
        if 'Champions' in segment_counts:
            recommendations.append(
                "Focus loyalty programs and VIP experiences on Champion customers to maintain their high engagement"
            )

        # At Risk recommendations
        if 'At Risk' in segment_counts:
            recommendations.append(
                "Implement win-back campaigns for At Risk customers with personalized offers and communications"
            )

        # New Customers recommendations
        if 'New Customers' in segment_counts:
            recommendations.append(
                "Develop onboarding sequences and first-purchase incentives for New Customers to increase retention"
            )

        # Geographic opportunities
        if 'state' in df.columns:
            top_states = df['state'].value_counts().head(3)
            for state in top_states.index:
                recommendations.append(
                    f"Consider targeted marketing campaigns in {state} where customer concentration is high"
                )

        return recommendations

    def analyze_behavior(self, df: pd.DataFrame) -> AnalysisResult:
        """Analyze customer behavior patterns."""

        if df.empty:
            return self.handle_empty_dataframe("No customer behavior data available for analysis.")

        insights = []

        # Purchase frequency analysis
        if 'order_frequency' in df.columns:
            avg_frequency = df['order_frequency'].mean()
            high_frequency_customers = len(df[df['order_frequency'] > avg_frequency * 1.5])

            insights.append(create_insight(
                f"Average customer places {avg_frequency:.2f} orders, with {high_frequency_customers} high-frequency shoppers.",
                self.analysis_type,
                supporting_data={
                    'avg_frequency': float(avg_frequency),
                    'high_frequency_customers': int(high_frequency_customers)
                }
            ))

        # Category diversity analysis
        if 'unique_categories' in df.columns:
            avg_categories = df['unique_categories'].mean()
            diverse_customers = len(df[df['unique_categories'] > 3])

            insights.append(create_insight(
                f"Customers purchase from an average of {avg_categories:.1f} categories, indicating {'diverse' if avg_categories > 2 else 'focused'} shopping behavior.",
                self.analysis_type,
                supporting_data={
                    'avg_categories': float(avg_categories),
                    'diverse_customers': int(diverse_customers)
                }
            ))

        # Top categories analysis
        if 'top_categories' in df.columns:
            category_counts = {}
            for categories in df['top_categories'].dropna():
                for category in categories:
                    category_counts[category] = category_counts.get(category, 0) + 1

            if category_counts:
                top_category = max(category_counts, key=category_counts.get)
                insights.append(create_insight(
                    f"'{top_category}' is the most popular category across customer behavior patterns.",
                    self.analysis_type,
                    supporting_data={
                        'top_category': top_category,
                        'category_popularity': category_counts
                    }
                ))

        return AnalysisResult(
            analysis_type=self.analysis_type,
            insights=insights,
            summary_stats={
                'total_customers': len(df),
                'avg_order_frequency': float(df.get('order_frequency', pd.Series()).mean()),
                'avg_spending': float(df.get('total_spent', pd.Series()).mean())
            }
        )