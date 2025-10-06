"""
Customer-specific query builders.
"""

from bq_client import BigQueryRunner
from agent.state import AnalysisContext
from .utils import add_time_range_filter


class CustomerQueryBuilder:
    """Query builder for customer-related analyses."""

    def __init__(self, bq_client: BigQueryRunner):
        self.bq_client = bq_client

    def build_customer_segmentation_query(self, context: AnalysisContext) -> str:
        """Build query for customer segmentation analysis."""

        # RFM Analysis (Recency, Frequency, Monetary)
        base_query = """
        WITH customer_metrics AS (
            SELECT
                o.user_id,
                MAX(o.created_at) as last_order_date,
                COUNT(DISTINCT o.order_id) as total_orders,
                COALESCE(SUM(oi.sale_price), 0) as total_spent,
                COALESCE(AVG(oi.sale_price), 0) as avg_order_value,
                MIN(o.created_at) as first_order_date
            FROM `bigquery-public-data.thelook_ecommerce.orders` o
            LEFT JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi ON o.order_id = oi.order_id
            WHERE o.status NOT IN ('Cancelled', 'Returned')
              AND (oi.status IS NULL OR oi.status NOT IN ('Cancelled', 'Returned'))
        """

        # Add time range filter if specified
        base_query = add_time_range_filter(base_query, context)

        base_query += """
            GROUP BY o.user_id
        ),
        rfm_scores AS (
            SELECT
                user_id,
                DATE_DIFF(CURRENT_DATE(), DATE(last_order_date), DAY) as recency,
                total_orders as frequency,
                total_spent as monetary,
                CASE
                    WHEN DATE_DIFF(CURRENT_DATE(), DATE(last_order_date), DAY) <= 30 THEN 4
                    WHEN DATE_DIFF(CURRENT_DATE(), DATE(last_order_date), DAY) <= 90 THEN 3
                    WHEN DATE_DIFF(CURRENT_DATE(), DATE(last_order_date), DAY) <= 180 THEN 2
                    ELSE 1
                END as recency_score,
                CASE
                    WHEN total_orders >= 10 THEN 4
                    WHEN total_orders >= 5 THEN 3
                    WHEN total_orders >= 2 THEN 2
                    ELSE 1
                END as frequency_score,
                CASE
                    WHEN total_spent >= 1000 THEN 4
                    WHEN total_spent >= 500 THEN 3
                    WHEN total_spent >= 200 THEN 2
                    ELSE 1
                END as monetary_score
            FROM customer_metrics
        ),
        customer_segments AS (
            SELECT
                *,
                monetary as total_spent,
                CONCAT(CAST(recency_score AS STRING), CAST(frequency_score AS STRING), CAST(monetary_score AS STRING)) as rfm_segment,
                CASE
                    WHEN recency_score >= 4 AND frequency_score >= 4 THEN 'Champions'
                    WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Loyal Customers'
                    WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'New Customers'
                    WHEN recency_score <= 2 AND frequency_score >= 3 THEN 'At Risk'
                    WHEN recency_score <= 2 AND frequency_score <= 2 THEN 'Lost Customers'
                    ELSE 'Regular Customers'
                END as customer_segment
            FROM rfm_scores
        )
        """

        # Add user demographics if available
        base_query += """
        SELECT
            cs.*,
            u.age,
            u.gender,
            u.city,
            u.state,
            u.country
        FROM customer_segments cs
        LEFT JOIN `bigquery-public-data.thelook_ecommerce.users` u ON cs.user_id = u.id
        ORDER BY total_spent DESC
        """

        return base_query

    def build_customer_behavior_query(self, context: AnalysisContext) -> str:
        """Build query for customer behavior analysis."""

        base_query = """
        WITH customer_orders AS (
            SELECT
                o.user_id,
                o.created_at as order_date,
                oi.product_id,
                1 as quantity,
                oi.sale_price,
                p.category as product_category,
                p.brand,
                p.name as product_name
            FROM `bigquery-public-data.thelook_ecommerce.orders` o
            JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi ON o.order_id = oi.order_id
            JOIN `bigquery-public-data.thelook_ecommerce.products` p ON oi.product_id = p.id
            WHERE o.status NOT IN ('Cancelled', 'Returned')
              AND oi.status NOT IN ('Cancelled', 'Returned')
        """

        # Add time range filter
        if context.time_range:
            base_query = add_time_range_filter(base_query, context)

        base_query += """
        ),
        behavior_metrics AS (
            SELECT
                user_id,
                COUNT(DISTINCT order_date) as order_frequency,
                COUNT(*) as total_items_purchased,
                SUM(quantity) as total_quantity,
                SUM(sale_price * quantity) as total_spent,
                AVG(sale_price) as avg_item_price,
                COUNT(DISTINCT product_category) as unique_categories,
                COUNT(DISTINCT product_id) as unique_products,
                ARRAY_AGG(DISTINCT product_category ORDER BY COUNT(*) DESC LIMIT 3) as top_categories
            FROM customer_orders
            GROUP BY user_id
        )
        """

        # Add user demographics
        base_query += """
        SELECT
            bm.*,
            u.age,
            u.gender,
            u.city,
            u.state,
            u.country
        FROM behavior_metrics bm
        LEFT JOIN `bigquery-public-data.thelook_ecommerce.users` u ON bm.user_id = u.id
        ORDER BY total_spent DESC
        """

        return base_query