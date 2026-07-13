"""
Configuration module for the Afghanistan Purchasing Bot.
Uses Pydantic Settings for type-safe environment variable loading.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Bot Configuration ──
    bot_token: str = Field(..., description="Telegram Bot API token")
    bot_username: str = Field("afghanistan_purchasing_bot", description="Bot username without @")

    # ── Webhook (for production) ──
    webhook_url: Optional[str] = Field(None, description="Webhook URL for production")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret token")

    # ── Admin Configuration ──
    admin_ids: List[int] = Field(default_factory=list, description="List of admin Telegram IDs")
    admin_username: Optional[str] = Field(None, description="Admin username for quick access")

    # ── Database ──
    database_url: str = Field("sqlite:///data/bot.db", description="Database connection string")

    # ── Exchange Rates ──
    exchange_rate_api_key: Optional[str] = Field(None, description="API key for exchange rate service")
    fallback_cny_to_afn: float = Field(9.8, description="Fallback CNY to AFN rate")

    # ── Shipping Configuration ──
    shipping_air_base: float = Field(80.0, description="Air shipping cost per kg (CNY)")
    shipping_sea_base: float = Field(25.0, description="Sea shipping cost per kg (CNY)")
    shipping_land_base: float = Field(35.0, description="Land shipping cost per kg (CNY)")

    delivery_air_days: int = Field(7, description="Air delivery estimate (days)")
    delivery_sea_days: int = Field(45, description="Sea delivery estimate (days)")
    delivery_land_days: int = Field(20, description="Land delivery estimate (days)")

    # ── Business Settings ──
    company_name: str = Field("Afghanistan Purchasing Agent", description="Business name")
    office_address: str = Field("Kabul, Afghanistan", description="Office address")
    office_phone: str = Field("+93-XXX-XXXX-XXX", description="Office phone")
    business_hours: str = Field("Saturday-Thursday 8:00-17:00", description="Business hours")

    service_fee_percent: float = Field(5.0, description="Service fee percentage")
    photo_inspection_fee: float = Field(15.0, description="Photo inspection fee (CNY)")

    # ── Referral System ──
    referral_reward_afn: float = Field(500.0, description="Referral reward in AFN")
    referral_min_order_afn: float = Field(2000.0, description="Minimum order for referral reward")

    # ── Logging ──
    log_level: str = Field("INFO", description="Logging level")
    log_file: str = Field("logs/bot.log", description="Log file path")

    # ── Environment ──
    environment: str = Field("development", description="Environment: development/staging/production")
    debug: bool = Field(False, description="Debug mode")

    @validator("admin_ids", pre=True)
    def parse_admin_ids(cls, v):
        """Parse comma-separated admin IDs into list of integers."""
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
