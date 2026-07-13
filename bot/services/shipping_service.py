"""
Shipping cost calculation service.
Calculates shipping costs based on weight, method, and destination.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config import settings
from bot.database import db, ShippingMethod


class ShippingService:
    """Service for calculating shipping costs and delivery estimates."""

    # Weight tiers for volume-based pricing
    WEIGHT_TIERS = [
        (0, 1, 1.0),      # 0-1kg: base rate
        (1, 5, 0.9),      # 1-5kg: 10% discount
        (5, 10, 0.85),    # 5-10kg: 15% discount
        (10, 20, 0.8),    # 10-20kg: 20% discount
        (20, 50, 0.75),   # 20-50kg: 25% discount
        (50, 999, 0.7),   # 50kg+: 30% discount
    ]

    async def get_shipping_methods(self) -> List[Dict]:
        """Get all available shipping methods with current rates."""
        rates = await db.get_shipping_rates()
        methods = []

        for rate in rates:
            method_info = {
                "method": rate["method"],
                "name": self._get_method_name(rate["method"]),
                "base_rate_cny": rate["base_rate"],
                "estimated_days": rate["estimated_days"],
                "description": self._get_method_description(rate["method"]),
                "icon": self._get_method_icon(rate["method"]),
            }
            methods.append(method_info)

        return methods

    def _get_method_name(self, method: str) -> str:
        """Get display name for shipping method."""
        names = {
            "air": "✈️ Air Freight",
            "sea": "🚢 Sea Freight", 
            "land": "🚛 Land Transport",
        }
        return names.get(method, method.title())

    def _get_method_description(self, method: str) -> str:
        """Get description for shipping method."""
        descriptions = {
            "air": "Fastest option. Best for urgent or lightweight items.",
            "sea": "Most economical for heavy/bulk orders. Longer delivery time.",
            "land": "Balanced speed and cost via road/rail through Central Asia.",
        }
        return descriptions.get(method, "")

    def _get_method_icon(self, method: str) -> str:
        """Get icon for shipping method."""
        icons = {
            "air": "✈️",
            "sea": "🚢",
            "land": "🚛",
        }
        return icons.get(method, "📦")

    def calculate_shipping_cost(self, weight_kg: float, method: str, base_rate: float) -> Dict:
        """
        Calculate shipping cost for given weight and method.

        Returns dict with:
        - weight_kg: input weight
        - method: shipping method
        - base_rate: rate per kg
        - tier_discount: applied discount percentage
        - cost_cny: total shipping cost in CNY
        - cost_afn: total shipping cost in AFN (if rate provided)
        """
        # Find applicable weight tier
        discount = 1.0
        for min_w, max_w, disc in self.WEIGHT_TIERS:
            if min_w <= weight_kg < max_w:
                discount = disc
                break

        # Calculate cost
        cost_cny = round(weight_kg * base_rate * discount, 2)

        return {
            "weight_kg": weight_kg,
            "method": method,
            "base_rate": base_rate,
            "tier_discount": round((1 - discount) * 100, 1),
            "cost_cny": cost_cny,
            "cost_afn": None,  # Will be set by caller with exchange rate
        }

    def estimate_delivery(self, method: str, estimated_days: int) -> Dict:
        """
        Estimate delivery date range.

        Returns dict with:
        - estimated_days: business days estimate
        - earliest_date: earliest possible delivery
        - latest_date: latest expected delivery
        - formatted_range: human-readable date range
        """
        today = datetime.now()

        # Add buffer days for processing
        processing_days = 2
        total_days_min = estimated_days + processing_days
        total_days_max = estimated_days + processing_days + 5  # Buffer

        earliest = today + timedelta(days=total_days_min)
        latest = today + timedelta(days=total_days_max)

        return {
            "estimated_days": estimated_days,
            "processing_days": processing_days,
            "total_days_min": total_days_min,
            "total_days_max": total_days_max,
            "earliest_date": earliest,
            "latest_date": latest,
            "formatted_range": f"{earliest.strftime('%b %d')} - {latest.strftime('%b %d, %Y')}",
        }

    async def calculate_order_totals(self, items: List[Dict], shipping_method: str, 
                                    exchange_rate: float, include_photo_inspection: bool = False) -> Dict:
        """
        Calculate complete order totals.

        Args:
            items: List of order items with weight_kg and price_cny
            shipping_method: Selected shipping method
            exchange_rate: Current CNY to AFN rate
            include_photo_inspection: Whether to include photo inspection fee

        Returns dict with all cost breakdowns.
        """
        # Get shipping rate
        rates = await db.get_shipping_rates()
        rate_info = next((r for r in rates if r["method"] == shipping_method), None)

        if not rate_info:
            raise ValueError(f"Invalid shipping method: {shipping_method}")

        # Calculate product totals
        total_product_cny = sum(item.get("price_cny", 0) * item.get("quantity", 1) for item in items)
        total_weight = sum(item.get("weight_kg", 0.5) * item.get("quantity", 1) for item in items)

        # Calculate shipping
        shipping = self.calculate_shipping_cost(total_weight, shipping_method, rate_info["base_rate"])
        shipping_cost_cny = shipping["cost_cny"]

        # Calculate service fee
        service_fee_cny = round(total_product_cny * (settings.service_fee_percent / 100), 2)

        # Photo inspection fee
        photo_fee_cny = settings.photo_inspection_fee if include_photo_inspection else 0

        # Totals in CNY
        total_cny = round(total_product_cny + shipping_cost_cny + service_fee_cny + photo_fee_cny, 2)

        # Convert to AFN
        total_product_afn = round(total_product_cny * exchange_rate, 2)
        shipping_cost_afn = round(shipping_cost_cny * exchange_rate, 2)
        service_fee_afn = round(service_fee_cny * exchange_rate, 2)
        photo_fee_afn = round(photo_fee_cny * exchange_rate, 2)
        total_afn = round(total_cny * exchange_rate, 2)

        # Delivery estimate
        delivery = self.estimate_delivery(shipping_method, rate_info["estimated_days"])

        return {
            "items_count": len(items),
            "total_weight_kg": round(total_weight, 2),

            "product_cost_cny": round(total_product_cny, 2),
            "product_cost_afn": total_product_afn,

            "shipping_cost_cny": shipping_cost_cny,
            "shipping_cost_afn": shipping_cost_afn,
            "shipping_details": shipping,

            "service_fee_cny": service_fee_cny,
            "service_fee_afn": service_fee_afn,
            "service_fee_percent": settings.service_fee_percent,

            "photo_inspection_cny": photo_fee_cny,
            "photo_inspection_afn": photo_fee_afn,

            "total_cny": total_cny,
            "total_afn": total_afn,

            "exchange_rate": exchange_rate,
            "delivery_estimate": delivery,
        }


# Singleton instance
shipping_service = ShippingService()
