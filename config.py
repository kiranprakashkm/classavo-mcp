"""Configuration management for Classavo MCP Server."""

import os
from typing import Optional
from dotenv import load_dotenv


class ClassavoConfig:
    """Configuration class for Classavo API and MCP server settings."""

    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # API Configuration
        self.api_url: str = os.getenv("CLASSAVO_API_URL", "http://localhost:8000")
        self.api_token: Optional[str] = os.getenv("CLASSAVO_API_TOKEN")

        # Login credentials (alternative to token)
        self.username: Optional[str] = os.getenv("CLASSAVO_USERNAME")
        self.password: Optional[str] = os.getenv("CLASSAVO_PASSWORD")

        # Rate limiting
        self.rate_limit: int = int(os.getenv("CLASSAVO_RATE_LIMIT", "10"))

        # Debug mode
        self.debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    @property
    def has_credentials(self) -> bool:
        """Check if login credentials are configured."""
        return bool(self.username and self.password)

    @property
    def has_token(self) -> bool:
        """Check if API token is configured."""
        return bool(self.api_token)

    @property
    def is_configured(self) -> bool:
        """Check if either token or credentials are configured."""
        return self.has_token or self.has_credentials


# Global configuration instance
config = ClassavoConfig()
