"""
Product extraction service for Chinese e-commerce platforms.
Supports Taobao, Pinduoduo, and 1688 product link parsing.
"""
import re
import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import asyncio

from bot.database import ProductPlatform


class ProductExtractor:
    """Extracts product information from Chinese e-commerce URLs."""

    # URL patterns for supported platforms
    PLATFORM_PATTERNS = {
        ProductPlatform.TAOBAO: [
            r"item\.taobao\.com",
            r"detail\.tmall\.com",
            r"taobao\.com/item",
        ],
        ProductPlatform.PINDUODUO: [
            r"mobile\.yangkeduo\.com",
            r"pinduoduo\.com",
        ],
        ProductPlatform.ALIBABA1688: [
            r"detail\.1688\.com",
            r"1688\.com",
        ],
    }

    # Price extraction patterns (fallback when scraping fails)
    PRICE_PATTERNS = [
        r'"price":\s*"?([\d,]+\.?\d*)"?',
        r'"originalPrice":\s*"?([\d,]+\.?\d*)"?',
        r'"salePrice":\s*"?([\d,]+\.?\d*)"?',
        r"price[\"']?\s*[:=]\s*[\"']?([\d,]+\.?\d*)",
        r'[¥￥]\s*([\d,]+\.?\d+)',
        r"price[\"']?\s*[:=]\s*([\d,]+\.?\d*)",
    ]

    TITLE_PATTERNS = [
        r'"title":\s*"([^"]+)"',
        r'<title[^>]*>([^<]+)</title>',
        r'"itemTitle":\s*"([^"]+)"',
    ]

    IMAGE_PATTERNS = [
        r'"picUrl":\s*"([^"]+)"',
        r'"image":\s*"([^"]+)"',
        r'<img[^>]*src="([^"]+)"[^>]*class="[^"]*main[^"]*"',
    ]

    def detect_platform(self, url: str) -> ProductPlatform:
        """Detect which platform a URL belongs to."""
        url_lower = url.lower()

        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return platform

        return ProductPlatform.OTHER

    def _extract_with_regex(self, html: str, patterns: list) -> Optional[str]:
        """Extract value using regex patterns."""
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _clean_price(self, price_str: str) -> Optional[float]:
        """Clean and parse price string."""
        if not price_str:
            return None
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.]', '', price_str)
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

    async def extract(self, url: str) -> Dict[str, Any]:
        """
        Extract product information from a URL.

        Returns dict with:
        - url: original URL
        - platform: detected platform
        - title: product title
        - price_cny: extracted price in CNY
        - original_price_cny: original price if on sale
        - image_url: product image URL
        - description: short description
        - weight_kg: estimated weight (default 0.5kg if unknown)
        - status: extraction status
        - error: error message if failed
        """
        result = {
            "url": url,
            "platform": self.detect_platform(url).value,
            "title": None,
            "price_cny": None,
            "original_price_cny": None,
            "image_url": None,
            "description": None,
            "weight_kg": 0.5,  # Default estimate
            "status": "pending",
            "error": None
        }

        try:
            # Fetch the page
            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                }
            ) as client:
                response = await client.get(url)

                if response.status_code != 200:
                    result["status"] = "failed"
                    result["error"] = f"HTTP {response.status_code}"
                    return result

                html = response.text

                # Extract title
                title = self._extract_with_regex(html, self.TITLE_PATTERNS)
                if title:
                    result["title"] = title

                # Extract price
                price = self._extract_with_regex(html, self.PRICE_PATTERNS)
                if price:
                    result["price_cny"] = self._clean_price(price)

                # Try to find original price (for sale items)
                # Look for patterns suggesting a discount
                original_match = re.search(r'"originalPrice":\s*"?([\d,]+\.?\d*)"?', html)
                if original_match:
                    result["original_price_cny"] = self._clean_price(original_match.group(1))

                # Extract image
                image = self._extract_with_regex(html, self.IMAGE_PATTERNS)
                if image:
                    # Make absolute URL if relative
                    if image.startswith("//"):
                        image = "https:" + image
                    elif image.startswith("/"):
                        parsed = urlparse(url)
                        image = f"{parsed.scheme}://{parsed.netloc}{image}"
                    result["image_url"] = image

                # Try to extract description from meta tags
                soup = BeautifulSoup(html, "lxml")
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc:
                    result["description"] = meta_desc.get("content", "")

                # Try to find weight information
                weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(kg|g|kilogram)', html, re.IGNORECASE)
                if weight_match:
                    weight_val = float(weight_match.group(1))
                    unit = weight_match.group(2).lower()
                    if unit in ("g",):
                        weight_val = weight_val / 1000
                    result["weight_kg"] = round(weight_val, 3)

                result["status"] = "success"

        except httpx.TimeoutException:
            result["status"] = "failed"
            result["error"] = "Request timeout - website took too long to respond"
        except httpx.RequestError as e:
            result["status"] = "failed"
            result["error"] = f"Network error: {str(e)}"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = f"Extraction error: {str(e)}"

        return result

    def get_platform_display_name(self, platform: ProductPlatform) -> str:
        """Get human-readable platform name."""
        names = {
            ProductPlatform.TAOBAO: "Taobao / Tmall",
            ProductPlatform.PINDUODUO: "Pinduoduo",
            ProductPlatform.ALIBABA1688: "1688 (Alibaba)",
            ProductPlatform.OTHER: "Other Platform",
        }
        return names.get(platform, "Unknown")


# Singleton instance
product_extractor = ProductExtractor()
