import logging
import os
from typing import Optional, List, Dict, Any
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError


class BigQueryRunner:
    """A lean BigQuery client for executing SQL queries and returning DataFrame results."""

    def __init__(self, project_id: Optional[str] = None, dataset_id: Optional[str] = "bigquery-public-data.thelook_ecommerce") -> None:
        """Initialize BigQuery client.

        Args:
            project_id: Google Cloud project ID. If None, uses default credentials.
            dataset_id: BigQuery dataset ID. If None, uses default dataset.
        """
        logging.debug("Initializing BigQuery client")
        try:
            # Check for service account credentials first
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            service_account_file = 'gen-lang-client-0785455107-d1de870653ee.json'

            # Try service account file if it exists (for local development)
            if os.path.exists(service_account_file):
                logging.debug(f"Using service account credentials from: {service_account_file}")
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_file,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                self.client = bigquery.Client(
                    project=project_id or credentials.project_id,
                    credentials=credentials
                )
            elif credentials_path and os.path.exists(credentials_path):
                logging.debug(f"Using service account credentials from: {credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                self.client = bigquery.Client(
                    project=project_id or credentials.project_id,
                    credentials=credentials
                )
            else:
                # Try to use Application Default Credentials (ADC)
                logging.debug("Attempting to use Application Default Credentials")
                try:
                    self.client = bigquery.Client(project=project_id)
                except DefaultCredentialsError:
                    logging.warning("No credentials found. Please set GOOGLE_APPLICATION_CREDENTIALS or run in GCP environment.")
                    raise ValueError("BigQuery credentials not configured. Set GOOGLE_APPLICATION_CREDENTIALS environment variable or run in GCP.")

            self.dataset_id = dataset_id
            logging.info(f"BigQuery client ready for dataset: {self.dataset_id}")
        except Exception as e:
            logging.error(f"Failed to initialize BigQuery client: {str(e)}")
            raise
    
    def execute_query(self, sql_query: str) -> pd.DataFrame:
        """Execute a SQL query and return results as a DataFrame.
        
        Args:
            sql_query: The SQL query to execute.
            
        Returns:
            DataFrame containing the query results.
            
        Raises:
            Exception: If query execution fails.
        """
        try:
            logging.debug(f"Executing BigQuery query")
            query_job = self.client.query(sql_query)
            df = query_job.result().to_dataframe()
            logging.info(f"Query completed successfully, returned {len(df)} rows")
            return df
        except Exception as e:
            logging.error(f"BigQuery execution failed: {str(e)}")
            raise 

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table.
        
        Args:
            table_name: Name of the table (orders, order_items, products, users).
            
        Returns:
            List of dictionaries containing column information.
        """
        try:
            table_ref = f"{self.dataset_id}.{table_name}"
            table = self.client.get_table(table_ref)
            schema_info = []
            for field in table.schema:
                schema_info.append({
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode,
                    "description": field.description or ""
                })
            logging.debug(f"Retrieved schema for table {table_name}")
            return schema_info
        except Exception as e:
            logging.error(f"Failed to get schema for table {table_name}: {str(e)}")
            raise        