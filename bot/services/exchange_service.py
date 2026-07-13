"""
Exchange rate service for CNY to AFN conversion.
Supports API fetching with fallback to manual rates.
"""
import httpx
from typing import Optional
from datetime import datetime, timedelta
from config import settings
from bot.database import db


class ExchangeService:
    """Service for managing currency exchange rates."""

    # Free API endpoint (no key required for basic usage)
    API_URL = "https://api.exchangerate-api.com/v4/latest/CNY"
    BACKUP_API_URL = "https://open.er-api.com/v6/latest/CNY"

    _cached_rate: Optional[float] = None
    _cached_at: Optional[datetime] = None
    _cache_ttl = timedelta(hours=1)  # Cache for 1 hour

    async def get_rate(self) -> float:
        """Get current CNY to AFN exchange rate."""
        # Check cache first
        if self._cached_rate and self._cached_at:
            if datetime.now() - self._cached_at < self._cache_ttl:
                return self._cached_rate

        # Try to fetch from database (latest recorded rate)
        db_rate = await db.get_latest_rate()
        if db_rate:
            self._cached_rate = db_rate
            self._cached_at = datetime.now()
            return db_rate

        # Try API
        api_rate = await self._fetch_from_api()
        if api_rate:
            await db.set_exchange_rate(api_rate, source="api")
            self._cached_rate = api_rate
            self._cached_at = datetime.now()
            return api_rate

        # Fallback to settings
        return settings.fallback_cny_to_afn

    async def _fetch_from_api(self) -> Optional[float]:
        """Fetch rate from external API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try primary API
                response = await client.get(self.API_URL)
                if response.status_code == 200:
                    data = response.json()
                    if "rates" in data and "AFN" in data["rates"]:
                        return float(data["rates"]["AFN"])

                # Try backup API
                response = await client.get(self.BACKUP_API_URL)
                if response.status_code == 200:
                    data = response.json()
                    if "rates" in data and "AFN" in data["rates"]:
                        return float(data["rates"]["AFN"])

        except Exception as e:
            # Log error but don't crash - will use fallback
            print(f"Exchange API error: {e}")

        return None

    async def set_manual_rate(self, rate: float) -> None:
        """Set a manual exchange rate (admin function)."""
        await db.set_exchange_rate(rate, source="manual")
        self._cached_rate = rate
        self._cached_at = datetime.now()

    def cny_to_afn(self, amount_cny: float, rate: float = None) -> float:
        """Convert CNY amount to AFN."""
        if rate is None:
            # Will be called with awaited rate in async context
            raise ValueError("Rate must be provided. Use await get_rate() first.")
        return round(amount_cny * rate, 2)

    def afn_to_cny(self, amount_afn: float, rate: float) -> float:
        """Convert AFN amount to CNY."""
        return round(amount_afn / rate, 2) if rate > 0 else 0


# Singleton instance
exchange_service = ExchangeService()
