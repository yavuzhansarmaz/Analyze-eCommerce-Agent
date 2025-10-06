"""
Product-specific query builders.
"""

from bq_client import BigQueryRunner
from agent.state import AnalysisContext
from .utils import add_time_range_filter, add_default_time_filter


class ProductQueryBuilder:
    """Query builder for product-related analyses."""

    def __init__(self, bq_client: BigQueryRunner):
        self.bq_client = bq_client

    def build_product_performance_query(self, context: AnalysisContext) -> str:
        """Build query for product performance analysis."""

        base_query = """
        SELECT
            p.id as product_id,
            p.name as product_name,
            p.category,
            p.brand,
            p.retail_price,
            p.cost,

            -- Sales metrics
            COUNT(oi.order_id) as total_orders,
            COUNT(*) as total_quantity_sold,
            SUM(oi.sale_price) as total_revenue,
            AVG(oi.sale_price) as avg_sale_price,

            -- Performance indicators
            CASE
                WHEN p.retail_price > 0 THEN (p.retail_price - p.cost) / p.retail_price
                ELSE 0
            END as margin_percentage,

            -- Time-based metrics (last 90 days)
            COUNT(CASE WHEN DATE(o.created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                      THEN oi.order_id END) as recent_orders,
            COUNT(CASE WHEN DATE(o.created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                      THEN oi.id END) as recent_quantity

        FROM `bigquery-public-data.thelook_ecommerce.products` p
        LEFT JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi ON p.id = oi.product_id
        LEFT JOIN `bigquery-public-data.thelook_ecommerce.orders` o ON oi.order_id = o.order_id
        """

        # Add time range filter
        if context.time_range:
            base_query = add_time_range_filter(base_query, context)
        else:
            # Default to last 2 years if no time range specified
            base_query = add_default_time_filter(base_query, 730)

        base_query += """
        GROUP BY p.id, p.name, p.category, p.brand, p.retail_price, p.cost
        HAVING total_orders > 0
        ORDER BY total_revenue DESC
        """

        return base_query

    def build_product_recommendations_query(self, context: AnalysisContext) -> str:
        """Build query for product recommendation analysis."""

        base_query = """
        WITH product_cooccurrence AS (
            SELECT
                a.product_id as product_a,
                b.product_id as product_b,
                COUNT(*) as cooccurrence_count,
                COUNT(DISTINCT a.order_id) as order_count
            FROM `bigquery-public-data.thelook_ecommerce.order_items` a
            JOIN `bigquery-public-data.thelook_ecommerce.order_items` b ON a.order_id = b.order_id
            WHERE a.product_id < b.product_id
        """

        # Add time range filter
        if context.time_range:
            start_date = context.time_range.get('start')
            end_date = context.time_range.get('end')
            if start_date:
                base_query += f" AND DATE(a.created_at) >= '{start_date}'"
            if end_date:
                base_query += f" AND DATE(a.created_at) <= '{end_date}'"

        base_query += """
            GROUP BY a.product_id, b.product_id
            HAVING cooccurrence_count >= 5
        ),
        product_popularity AS (
            SELECT
                product_id,
                COUNT(DISTINCT order_id) as popularity_score,
                ROW_NUMBER() OVER (ORDER BY COUNT(DISTINCT order_id) DESC) as popularity_rank
            FROM `bigquery-public-data.thelook_ecommerce.order_items`
        """

        if context.time_range:
            start_date = context.time_range.get('start')
            end_date = context.time_range.get('end')
            if start_date:
                base_query += f" WHERE DATE(created_at) >= '{start_date}'"
            if end_date:
                base_query += f" AND DATE(created_at) <= '{end_date}'"

        base_query += """
            GROUP BY product_id
        )
        SELECT
            pc.product_a,
            p1.name as product_a_name,
            p1.category as product_a_category,
            pc.product_b,
            p2.name as product_b_name,
            p2.category as product_b_category,
            pc.cooccurrence_count,
            pc.order_count,
            pp1.popularity_score as product_a_popularity,
            pp2.popularity_score as product_b_popularity
        FROM product_cooccurrence pc
        JOIN `bigquery-public-data.thelook_ecommerce.products` p1 ON pc.product_a = p1.id
        JOIN `bigquery-public-data.thelook_ecommerce.products` p2 ON pc.product_b = p2.id
        JOIN product_popularity pp1 ON pc.product_a = pp1.product_id
        JOIN product_popularity pp2 ON pc.product_b = pp2.product_id
        ORDER BY pc.cooccurrence_count DESC, pc.order_count DESC
        LIMIT 100
        """

        return base_query