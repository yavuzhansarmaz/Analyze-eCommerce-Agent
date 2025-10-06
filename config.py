"""
Configuration management for the Data Analysis Agent.
Handles environment variables, API keys, and service configurations.
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Initialize logging before any Google Cloud imports to avoid warnings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

@dataclass
class BigQueryConfig:
    """BigQuery configuration settings."""
    project_id: Optional[str] = None
    dataset_id: str = "bigquery-public-data.thelook_ecommerce"
    location: str = "US"

@dataclass
class GeminiConfig:
    """Google Gemini configuration settings."""
    model: str = "gemini-1.5-pro"
    temperature: float = 0.1
    max_tokens: int = 4000
    api_key: Optional[str] = None

@dataclass
class AppConfig:
    """Main application configuration."""
    bq_config: BigQueryConfig
    gemini_config: GeminiConfig
    log_level: str = "WARNING"

class ConfigManager:
    """Manages application configuration from environment variables."""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> AppConfig:
        """Load configuration from environment variables."""

        # BigQuery configuration
        bq_config = BigQueryConfig(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            dataset_id=os.getenv("BQ_DATASET_ID", "bigquery-public-data.thelook_ecommerce")
        )

        # Gemini configuration
        gemini_config = GeminiConfig(
            model=os.getenv("GOOGLE_MODEL", "gemini-1.5-pro"),
            temperature=float(os.getenv("TEMPERATURE", "0.1")),
            api_key=os.getenv("GOOGLE_API_KEY")
        )

        # Validate required configurations
        if not gemini_config.api_key:
            raise ValueError("Google Gemini API key is required")

        return AppConfig(
            bq_config=bq_config,
            gemini_config=gemini_config,
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )

    def get_config(self) -> AppConfig:
        """Get the loaded application configuration."""
        return self.config

    def setup_logging(self) -> None:
        """Configure logging based on the current configuration."""
        # Update the logging level based on configuration
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, self.config.log_level.upper()))

        # Add file handler if not already present
        if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
            file_handler = logging.FileHandler('agent.log', mode='a')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)

# Global configuration instance (lazy initialization)
_config_manager = None

def get_config() -> AppConfig:
    """Get the global application configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.setup_logging()
    return _config_manager.get_config()

def setup_gemini():
    """Set up and return the Google Gemini LLM instance."""
    config = get_config()

    # Check if API key is available
    if not config.gemini_config.api_key:
        logging.warning("Google Gemini API key not found. LLM enhancement will be disabled.")
        return None

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        # Create client but don't test it yet - we'll handle errors in the enhancement step
        return ChatGoogleGenerativeAI(
            model=config.gemini_config.model,
            temperature=config.gemini_config.temperature,
            max_tokens=config.gemini_config.max_tokens,
            google_api_key=config.gemini_config.api_key
        )
    except Exception as e:
        logging.warning(f"Failed to initialize Google Gemini client: {e}. LLM enhancement will be disabled.")
        return None

def create_bigquery_client() -> 'BigQueryRunner':
    """Create and return a BigQuery client instance."""
    from bq_client import BigQueryRunner
    config = get_config()
    return BigQueryRunner(
        project_id=config.bq_config.project_id,
        dataset_id=config.bq_config.dataset_id
    )