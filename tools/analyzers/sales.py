"""
Sales analyzer for trends and seasonality insights.
"""

import pandas as pd
from .base import BaseAnalyzer, AnalysisResult, create_insight
from agent.state import AnalysisType


class SalesAnalyzer(BaseAnalyzer):
    """Analyzer for sales trends and seasonality insights."""

    def __init__(self):
        super().__init__(AnalysisType.SALES_TRENDS)

    def analyze_trends(self, df: pd.DataFrame) -> AnalysisResult:
        """Analyze sales trends over time."""

        if df.empty:
            return self.handle_empty_dataframe("No sales trend data available for analysis.")

        insights = []

        # Convert time_period to datetime for trend analysis
        if 'time_period' in df.columns:
            df['time_period'] = pd.to_datetime(df['time_period'])

            # Calculate trend metrics
            if len(df) >= 2:
                first_period = df.iloc[-1]  # Oldest
                last_period = df.iloc[0]   # Most recent

                orders_growth = (last_period['total_orders'] - first_period['total_orders']) / first_period['total_orders'] if first_period['total_orders'] > 0 else 0
                revenue_growth = (last_period['total_revenue'] - first_period['total_revenue']) / first_period['total_revenue'] if first_period['total_revenue'] > 0 else 0

                insights.append(create_insight(
                    f"Sales show {'positive' if orders_growth > 0 else 'negative'} order growth of {abs(orders_growth):.1%} and {'positive' if revenue_growth > 0 else 'negative'} revenue growth of {abs(revenue_growth):.1%} over the analyzed period.",
                    AnalysisType.SALES_TRENDS,
                    supporting_data={
                        'orders_growth': float(orders_growth),
                        'revenue_growth': float(revenue_growth),
                        'periods_analyzed': len(df)
                    }
                ))

        # Recent performance vs average
        if 'total_revenue' in df.columns:
            recent_avg = df.head(5)['total_revenue'].mean()  # Most recent 5 periods
            overall_avg = df['total_revenue'].mean()

            performance_ratio = recent_avg / overall_avg if overall_avg > 0 else 0

            insights.append(create_insight(
                f"Recent performance is {abs(performance_ratio - 1):.1%} {'above' if performance_ratio > 1 else 'below'} the overall average.",
                AnalysisType.SALES_TRENDS,
                supporting_data={
                    'recent_avg': float(recent_avg),
                    'overall_avg': float(overall_avg),
                    'performance_ratio': float(performance_ratio)
                }
            ))

        return AnalysisResult(
            analysis_type=AnalysisType.SALES_TRENDS,
            insights=insights,
            summary_stats={
                'periods_analyzed': len(df),
                'total_revenue': float(df.get('total_revenue', pd.Series()).sum()),
                'total_orders': int(df.get('total_orders', pd.Series()).sum())
            }
        )

    def analyze_seasonality(self, df: pd.DataFrame) -> AnalysisResult:
        """Analyze seasonal patterns in sales data."""

        if df.empty:
            return self.handle_empty_dataframe("No seasonality data available for analysis.")

        insights = []

        # Identify high and low seasons
        high_season_months = df[df['season_type'] == 'High Season']['month'].tolist()
        low_season_months = df[df['season_type'] == 'Low Season']['month'].tolist()

        if high_season_months:
            insights.append(create_insight(
                f"High season months (months {', '.join(map(str, high_season_months))}) show elevated sales activity.",
                AnalysisType.SALES_SEASONALITY,
                supporting_data={
                    'high_season_months': high_season_months,
                    'low_season_months': low_season_months
                }
            ))

        # Seasonal variation analysis
        if 'avg_monthly_orders' in df.columns:
            max_month = df.loc[df['avg_monthly_orders'].idxmax()]
            min_month = df.loc[df['avg_monthly_orders'].idxmin()]
            variation_ratio = max_month['avg_monthly_orders'] / min_month['avg_monthly_orders'] if min_month['avg_monthly_orders'] > 0 else 0

            insights.append(create_insight(
                f"Sales vary by {variation_ratio:.1f}x between peak (Month {int(max_month['month'])}) and off-peak (Month {int(min_month['month'])}) months.",
                AnalysisType.SALES_SEASONALITY,
                supporting_data={
                    'variation_ratio': float(variation_ratio),
                    'peak_month': int(max_month['month']),
                    'off_peak_month': int(min_month['month'])
                }
            ))

        return AnalysisResult(
            analysis_type=AnalysisType.SALES_SEASONALITY,
            insights=insights,
            summary_stats={
                'months_analyzed': len(df),
                'high_season_months': len(high_season_months),
                'low_season_months': len(low_season_months)
            }
        )
