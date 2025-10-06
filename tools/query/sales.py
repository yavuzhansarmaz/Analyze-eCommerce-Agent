"""
Sales-specific query builders.
"""

from bq_client import BigQueryRunner
from agent.state import AnalysisContext
from .utils import add_time_range_filter, add_default_time_filter


class SalesQueryBuilder:
    """Query builder for sales-related analyses."""

    def __init__(self, bq_client: BigQueryRunner):
        self.bq_client = bq_client

    def build_sales_trends_query(self, context: AnalysisContext) -> str:
        """Build query for sales trends analysis."""

        base_query = """
        SELECT
            DATE_TRUNC(o.created_at, """

        # Determine time granularity based on context
        if context.parameters.get('granularity') == 'monthly':
            base_query += "MONTH"
        elif context.parameters.get('granularity') == 'weekly':
            base_query += "WEEK"
        else:
            base_query += "DAY"

        base_query += """) as time_period,
            COUNT(DISTINCT o.order_id) as total_orders,
            COALESCE(SUM(oi.sale_price), 0) as total_revenue,
            COUNT(*) as total_items_sold,
            COALESCE(AVG(oi.sale_price), 0) as avg_order_value,
            COUNT(DISTINCT o.user_id) as unique_customers
        FROM `bigquery-public-data.thelook_ecommerce.orders` o
        JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi ON o.order_id = oi.order_id
        WHERE o.status NOT IN ('Cancelled', 'Returned')
          AND oi.status NOT IN ('Cancelled', 'Returned')
        """

        # Add time range filter
        if context.time_range:
            base_query = add_time_range_filter(base_query, context)
        else:
            # Default to last year
            base_query = add_default_time_filter(base_query, 365)

        base_query += """
        GROUP BY time_period
        ORDER BY time_period DESC
        """

        return base_query

    def build_sales_seasonality_query(self, context: AnalysisContext) -> str:
        """Build query for sales seasonality analysis."""

        base_query = """
        WITH monthly_sales AS (
            SELECT
                EXTRACT(YEAR FROM o.created_at) as year,
                EXTRACT(MONTH FROM o.created_at) as month,
                COUNT(DISTINCT o.order_id) as total_orders,
                COALESCE(SUM(oi.sale_price), 0) as total_revenue,
                COUNT(*) as total_items,
                COUNT(DISTINCT o.user_id) as unique_customers
            FROM `bigquery-public-data.thelook_ecommerce.orders` o
            JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi ON o.order_id = oi.order_id
            WHERE o.status NOT IN ('Cancelled', 'Returned')
              AND oi.status NOT IN ('Cancelled', 'Returned')
        """

        # Add time range filter
        if context.time_range:
            base_query = add_time_range_filter(base_query, context)

        base_query += """
            GROUP BY year, month
        ),
        seasonality_analysis AS (
            SELECT
                month,
                AVG(total_orders) as avg_monthly_orders,
                AVG(total_revenue) as avg_monthly_revenue,
                STDDEV(total_orders) as order_stddev,
                STDDEV(total_revenue) as revenue_stddev,
                MAX(total_orders) as max_orders,
                MIN(total_orders) as min_orders
            FROM monthly_sales
            GROUP BY month
        )
        SELECT
            month,
            avg_monthly_orders,
            avg_monthly_revenue,
            CASE
                WHEN avg_monthly_orders > (SELECT AVG(avg_monthly_orders) FROM seasonality_analysis) + (SELECT STDDEV(avg_monthly_orders) FROM seasonality_analysis)
                THEN 'High Season'
                WHEN avg_monthly_orders < (SELECT AVG(avg_monthly_orders) FROM seasonality_analysis) - (SELECT STDDEV(avg_monthly_orders) FROM seasonality_analysis)
                THEN 'Low Season'
                ELSE 'Regular Season'
            END as season_type
        FROM seasonality_analysis
        ORDER BY month
        """

        return base_query