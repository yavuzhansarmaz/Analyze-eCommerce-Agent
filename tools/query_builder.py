"""
Dynamic SQL query builder for e-commerce data analysis.
This module provides a unified interface for all query builders.
"""

from typing import Dict, Any
import logging
from bq_client import BigQueryRunner
from agent.state import AnalysisType, AnalysisContext

# Import utility functions
from .query.utils import add_time_range_filter

# Import specific query builders
from .query.customer import CustomerQueryBuilder
from .query.product import ProductQueryBuilder
from .query.sales import SalesQueryBuilder
from .query.geographic import GeographicQueryBuilder

logger = logging.getLogger(__name__)

class QueryBuilder:
    """
    Builds dynamic SQL queries for different types of e-commerce analysis.

    This class acts as a facade for specialized query builders, delegating
    to the appropriate builder based on analysis type.
    """

    def __init__(self, bq_client: BigQueryRunner):
        self.bq_client = bq_client
        self.table_schemas = {}
        self._load_table_schemas()

        # Initialize specialized query builders
        self.customer_builder = CustomerQueryBuilder(bq_client)
        self.product_builder = ProductQueryBuilder(bq_client)
        self.sales_builder = SalesQueryBuilder(bq_client)
        self.geographic_builder = GeographicQueryBuilder(bq_client)

    def _load_table_schemas(self) -> None:
        """Load schema information for all required tables."""
        tables = ["orders", "order_items", "products", "users"]

        for table in tables:
            try:
                schema = self.bq_client.get_table_schema(table)
                self.table_schemas[table] = schema
                logger.debug(f"Loaded schema for table: {table}")
            except Exception as e:
                logger.error(f"Failed to load schema for table {table}: {e}")
                raise

    def build_query(self, analysis_type: AnalysisType, context: AnalysisContext) -> str:
        """
        Build a SQL query based on analysis type and context.

        Args:
            analysis_type: Type of analysis to perform
            context: Analysis context with parameters and filters

        Returns:
            SQL query string
        """
        if analysis_type == AnalysisType.CUSTOMER_SEGMENTATION:
            return self.customer_builder.build_customer_segmentation_query(context)
        elif analysis_type == AnalysisType.CUSTOMER_BEHAVIOR:
            return self.customer_builder.build_customer_behavior_query(context)
        elif analysis_type == AnalysisType.PRODUCT_PERFORMANCE:
            return self.product_builder.build_product_performance_query(context)
        elif analysis_type == AnalysisType.PRODUCT_RECOMMENDATIONS:
            return self.product_builder.build_product_recommendations_query(context)
        elif analysis_type == AnalysisType.SALES_TRENDS:
            return self.sales_builder.build_sales_trends_query(context)
        elif analysis_type == AnalysisType.SALES_SEASONALITY:
            return self.sales_builder.build_sales_seasonality_query(context)
        elif analysis_type == AnalysisType.GEOGRAPHIC_PATTERNS:
            return self.geographic_builder.build_geographic_patterns_query(context)
        else:
            return self._build_general_insights_query(context)

    def _build_general_insights_query(self, context: AnalysisContext) -> str:
        """Build query for general business insights."""

        base_query = """
        SELECT
            -- Overall business metrics
            COUNT(DISTINCT o.order_id) as total_orders,
            SUM(o.order_total) as total_revenue,
            COUNT(DISTINCT o.user_id) as total_customers,
            AVG(o.order_total) as avg_order_value,

            -- Product insights
            COUNT(DISTINCT p.id) as total_products,
            COUNT(DISTINCT p.category) as product_categories,
            COUNT(DISTINCT p.brand) as total_brands,

            -- Customer insights
            AVG(u.age) as avg_customer_age,
            COUNT(DISTINCT u.gender) as gender_diversity,
            COUNT(DISTINCT u.city) as customer_cities,

            -- Time-based insights
            MIN(o.created_at) as first_order_date,
            MAX(o.created_at) as last_order_date,
            DATE_DIFF(MAX(o.created_at), MIN(o.created_at), DAY) as operating_days

        FROM `bigquery-public-data.thelook_ecommerce.orders` o
        JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi ON o.order_id = oi.order_id
        JOIN `bigquery-public-data.thelook_ecommerce.products` p ON oi.product_id = p.id
        LEFT JOIN `bigquery-public-data.thelook_ecommerce.users` u ON o.user_id = u.id
        WHERE o.status NOT IN ('Cancelled', 'Returned')
        """

        # Add time range filter
        if context.time_range:
            base_query = add_time_range_filter(base_query, context)

        return base_query

    def get_query_metadata(self, analysis_type: AnalysisType) -> Dict[str, Any]:
        """Get metadata about a specific query type."""

        metadata = {
            AnalysisType.CUSTOMER_SEGMENTATION: {
                "description": "Customer segmentation using RFM analysis",
                "tables": ["orders", "users"],
                "metrics": ["recency", "frequency", "monetary", "customer_segments"]
            },
            AnalysisType.CUSTOMER_BEHAVIOR: {
                "description": "Customer behavior and purchasing patterns",
                "tables": ["orders", "order_items", "products", "users"],
                "metrics": ["order_frequency", "total_spent", "product_categories", "top_categories"]
            },
            AnalysisType.PRODUCT_PERFORMANCE: {
                "description": "Product performance and profitability analysis",
                "tables": ["products", "order_items", "orders"],
                "metrics": ["total_revenue", "total_orders", "margin_percentage", "recent_performance"]
            },
            AnalysisType.PRODUCT_RECOMMENDATIONS: {
                "description": "Product recommendation engine based on co-occurrence",
                "tables": ["order_items", "products"],
                "metrics": ["cooccurrence_count", "popularity_score", "recommendation_strength"]
            },
            AnalysisType.SALES_TRENDS: {
                "description": "Sales trends and growth patterns over time",
                "tables": ["orders", "order_items"],
                "metrics": ["total_orders", "total_revenue", "avg_order_value", "unique_customers"]
            },
            AnalysisType.SALES_SEASONALITY: {
                "description": "Seasonality patterns in sales data",
                "tables": ["orders", "order_items"],
                "metrics": ["avg_monthly_orders", "season_type", "seasonal_variation"]
            },
            AnalysisType.GEOGRAPHIC_PATTERNS: {
                "description": "Geographic distribution of sales and customers",
                "tables": ["orders", "order_items", "products", "users"],
                "metrics": ["total_revenue", "total_orders", "customer_density", "regional_preferences"]
            },
            AnalysisType.GENERAL_INSIGHTS: {
                "description": "General business overview and key metrics",
                "tables": ["orders", "order_items", "products", "users"],
                "metrics": ["total_revenue", "total_customers", "total_products", "operating_metrics"]
            }
        }

        return metadata.get(analysis_type, {})