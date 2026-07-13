"""
Unit tests for business services.
"""
import pytest
from bot.services.shipping_service import ShippingService
from bot.services.exchange_service import ExchangeService


class TestShippingService:
    """Tests for shipping calculations."""

    def setup_method(self):
        self.service = ShippingService()

    def test_calculate_shipping_cost(self):
        """Test basic shipping cost calculation."""
        result = self.service.calculate_shipping_cost(2.5, "air", 80.0)

        assert result["weight_kg"] == 2.5
        assert result["method"] == "air"
        assert result["cost_cny"] > 0
        assert result["tier_discount"] >= 0

    def test_weight_tier_discount(self):
        """Test that weight tiers apply discounts correctly."""
        # 0.5kg should have no discount
        r1 = self.service.calculate_shipping_cost(0.5, "air", 80.0)
        assert r1["tier_discount"] == 0.0

        # 3kg should have 10% discount
        r2 = self.service.calculate_shipping_cost(3, "air", 80.0)
        assert r2["tier_discount"] == 10.0

        # 7kg should have 15% discount
        r3 = self.service.calculate_shipping_cost(7, "air", 80.0)
        assert r3["tier_discount"] == 15.0


class TestExchangeService:
    """Tests for exchange rate service."""

    def setup_method(self):
        self.service = ExchangeService()

    def test_cny_to_afn_conversion(self):
        """Test currency conversion."""
        result = self.service.cny_to_afn(100.0, 9.8)
        assert result == 980.0

    def test_afn_to_cny_conversion(self):
        """Test reverse currency conversion."""
        result = self.service.afn_to_cny(980.0, 9.8)
        assert result == 100.0
