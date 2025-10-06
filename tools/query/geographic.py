"""
Geographic-specific query builders.
"""

from bq_client import BigQueryRunner
from agent.state import AnalysisContext
from .utils import add_time_range_filter


class GeographicQueryBuilder:
    """Query builder for geographic analyses."""

    def __init__(self, bq_client: BigQueryRunner):
        self.bq_client = bq_client

    def build_geographic_patterns_query(self, context: AnalysisContext) -> str:
        """Build query for geographic sales pattern analysis."""

        base_query = """
        SELECT
            COALESCE(u.state, 'Unknown') as state,
            COALESCE(u.city, 'Unknown') as city,
            u.country,
            COUNT(DISTINCT o.order_id) as total_orders,
            COALESCE(SUM(oi.sale_price), 0) as total_revenue,
            COUNT(*) as total_items,
            COUNT(DISTINCT o.user_id) as unique_customers,
            COALESCE(AVG(oi.sale_price), 0) as avg_order_value,
            COUNT(DISTINCT p.category) as product_categories,
            AVG(u.age) as avg_customer_age
        FROM `bigquery-public-data.thelook_ecommerce.orders` o
        JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi ON o.order_id = oi.order_id
        JOIN `bigquery-public-data.thelook_ecommerce.products` p ON oi.product_id = p.id
        LEFT JOIN `bigquery-public-data.thelook_ecommerce.users` u ON o.user_id = u.id
        WHERE o.status NOT IN ('Cancelled', 'Returned')
          AND oi.status NOT IN ('Cancelled', 'Returned')
        """

        # Add time range filter
        if context.time_range:
            base_query = add_time_range_filter(base_query, context)

        base_query += """
        GROUP BY u.state, u.city, u.country
        HAVING total_orders > 10
        ORDER BY total_revenue DESC
        """

        return base_query