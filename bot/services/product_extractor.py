import re
import json
import time
import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

from bot.database import ProductPlatform


class ProductExtractor:
    PLATFORM_PATTERNS = {
        ProductPlatform.TAOBAO: [
            r"item\.taobao\.com",
            r"detail\.tmall\.com",
            r"taobao\.com/item",
        ],
        ProductPlatform.PINDUODUO: [
            r"mobile\.yangkeduo\.com",
            r"pinduoduo\.com",
            r"yangkeduo\.com",
        ],
        ProductPlatform.ALIBABA1688: [
            r"detail\.1688\.com",
            r"1688\.com",
        ],
    }

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }

    _cache: Dict[str, Dict] = {}
    CACHE_TTL = 3600

    def detect_platform(self, url: str) -> ProductPlatform:
        url_lower = url.lower()
        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return platform
        return ProductPlatform.OTHER

    def _clean_price(self, price_str: str) -> Optional[float]:
        if not price_str:
            return None
        cleaned = re.sub(r'[^\d.]', '', price_str)
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict]:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    return data
                if isinstance(data, list) and data:
                    return data[0]
            except (json.JSONDecodeError, TypeError):
                continue
        return None

    def _extract_og_tags(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        result = {}
        for prop in ["title", "description", "image", "price:amount"]:
            meta = soup.find("meta", property=lambda x: x and f"og:{prop}" in x.lower())
            if meta:
                result[prop] = meta.get("content")
        for prop in ["twitter:title", "twitter:description", "twitter:image"]:
            meta = soup.find("meta", property=lambda x: x and prop in x.lower())
            if meta:
                result[prop.split(":")[1]] = meta.get("content")
        return result

    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        result = {}
        for name in ["description", "keywords"]:
            meta = soup.find("meta", attrs={"name": name})
            if meta:
                result[name] = meta.get("content")
        return result

    def _extract_from_script_data(self, html: str) -> Dict[str, Any]:
        result = {"title": None, "price_cny": None, "image_url": None}
        patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            r'window\.__NUXT__\s*=\s*({.*?});',
            r'window\.__DATA__\s*=\s*({.*?});',
            r'window\.rawData\s*=\s*({.*?});',
            r'var\s+data\s*=\s*({.*?});',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    items = data.get("item", data.get("goods", data.get("product", data.get("store", {}))))
                    if isinstance(items, dict):
                        result["title"] = items.get("title") or items.get("name") or items.get("itemName") or items.get("goodsName")
                        price = items.get("price") or items.get("priceCny") or items.get("salePrice") or items.get("defaultPrice")
                        if price:
                            result["price_cny"] = self._clean_price(str(price))
                        image = items.get("image") or items.get("picUrl") or items.get("imageUrl") or items.get("mainImage")
                        if image:
                            if isinstance(image, list):
                                image = image[0] if image else None
                            if image and isinstance(image, str):
                                if image.startswith("//"):
                                    image = "https:" + image
                                result["image_url"] = image
                except (json.JSONDecodeError, AttributeError):
                    pass
                if result["title"] or result["price_cny"]:
                    break
        return result

    def _extract_pinduoduo_json(self, html: str) -> Dict[str, Any]:
        result = {"title": None, "price_cny": None, "image_url": None}
        pdd_patterns = [
            r'<script[^>]*>window\.__NEXT_DATA__\s*=\s*({.*?})<\/script>',
            r'<script[^>]*>window\.__NUXT__\s*=\s*({.*?})<\/script>',
            r'<script[^>]*>window\.__INITIAL_STATE__\s*=\s*({.*?})<\/script>',
            r'"store"\s*:\s*({[^}]+"priceNormal"[^}]+})',
            r'"goodsInfo"\s*:\s*({[^}]+"price"[^}]+})',
            r'"item"\s*:\s*({[^}]+"price"[^}]+})',
        ]
        for pattern in pdd_patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, dict):
                        search_in = [data]
                        search_in.extend(data.get("props", {}).get("pageProps", {}) for _ in [1])
                        page = data.get("props", {}).get("pageProps", {}) or data
                        goods = page.get("goods", page.get("item", page.get("product", page.get("detail", {}))))
                        if isinstance(goods, dict):
                            result["title"] = goods.get("goodsName") or goods.get("itemName") or goods.get("name") or goods.get("title")
                            price = goods.get("priceNormal") or goods.get("price") or goods.get("salePrice") or goods.get("groupPrice")
                            if price:
                                result["price_cny"] = self._clean_price(str(price))
                            image = goods.get("goodsImageUrl") or goods.get("imageUrl") or goods.get("picUrl") or goods.get("image")
                            if image:
                                if isinstance(image, list):
                                    image = image[0] if image else None
                                if image and isinstance(image, str):
                                    if image.startswith("//"):
                                        image = "https:" + image
                                    result["image_url"] = image
                except (json.JSONDecodeError, AttributeError):
                    pass
                if result["title"] or result["price_cny"]:
                    break
        return result

    def _extract_pinduoduo_price_fallback(self, html: str) -> Optional[float]:
        patterns = [
            r'"priceNormal"\s*:\s*"?([\d,]+\.?\d*)"?',
            r'"groupPrice"\s*:\s*"?([\d,]+\.?\d*)"?',
            r'"price"\s*:\s*"?([\d,]+\.?\d*)"?',
            r'"minOnSaleGroupPrice"\s*:\s*"?([\d,]+\.?\d*)"?',
            r'"maxOnSaleGroupPrice"\s*:\s*"?([\d,]+\.?\d*)"?',
            r'<span[^>]*class="[^"]*price[^"]*"[^>]*>¥?\s*([\d,]+\.?\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                val = self._clean_price(match.group(1))
                if val:
                    return val
        return None

    def _parse_pinduoduo_url(self, url: str) -> Dict[str, Optional[str]]:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        result = {
            "goods_id": None,
            "ps": None,
            "mall_id": None,
        }
        if "goods_id" in params:
            result["goods_id"] = params["goods_id"][0]
        if "ps" in params:
            result["ps"] = params["ps"][0]
        if "mall_id" in params:
            result["mall_id"] = params["mall_id"][0]
        m = re.search(r'/product/(\d+)', parsed.path)
        if m:
            result["goods_id"] = m.group(1)
        m = re.search(r'/(\d+)\.html', parsed.path)
        if m and not result["goods_id"]:
            if len(m.group(1)) > 6:
                result["goods_id"] = m.group(1)
        return result

    def _extract_title(self, soup: BeautifulSoup, og: Dict, script_data: Dict, pdd_data: Dict) -> Optional[str]:
        if pdd_data.get("title"):
            return pdd_data["title"]
        if script_data.get("title"):
            return script_data["title"]
        if og.get("title"):
            return og["title"]
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title = title_tag.string.strip()
            title = re.sub(r'\s+', ' ', title)
            for suffix in [" - Taobao", " - 淘宝", " - 拼多多", " - Pinduoduo", " - 1688.com", " | 淘宝", " | 拼多多", " / 拼多多"]:
                if title.endswith(suffix):
                    title = title[:-len(suffix)].strip()
            return title
        return None

    def _extract_price(self, soup: BeautifulSoup, json_ld: Dict, og: Dict, script_data: Dict, pdd_data: Dict, html: str) -> Optional[float]:
        if pdd_data.get("price_cny"):
            return pdd_data["price_cny"]
        if script_data.get("price_cny"):
            return script_data["price_cny"]
        if json_ld:
            price = json_ld.get("offers", {}).get("price") or json_ld.get("price")
            if price:
                return self._clean_price(str(price))
        if og.get("price:amount"):
            return self._clean_price(og["price:amount"])
        meta_price = soup.find("meta", attrs={"name": "price"})
        if meta_price:
            return self._clean_price(meta_price.get("content", ""))
        pdd_fallback = self._extract_pinduoduo_price_fallback(html)
        if pdd_fallback:
            return pdd_fallback
        patterns = [
            r'"price":\s*"?([\d,]+\.?\d*)"?',
            r'"salePrice":\s*"?([\d,]+\.?\d*)"?',
            r'"currentPrice":\s*"?([\d,]+\.?\d*)"?',
            r'[¥￥]\s*([\d,]+\.?\d+)',
            r'"priceCny":\s*"?([\d,]+\.?\d*)"?',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                val = self._clean_price(match.group(1))
                if val:
                    return val
        return None

    def _extract_image(self, soup: BeautifulSoup, json_ld: Dict, og: Dict, script_data: Dict, pdd_data: Dict) -> Optional[str]:
        if pdd_data.get("image_url"):
            return pdd_data["image_url"]
        if script_data.get("image_url"):
            return script_data["image_url"]
        if json_ld:
            img = json_ld.get("image")
            if isinstance(img, list):
                img = img[0] if img else None
            if img and isinstance(img, str):
                return img if img.startswith("http") else "https:" + img
        if og.get("image"):
            img = og["image"]
            if img.startswith("//"):
                img = "https:" + img
            return img
        img_tag = soup.find("img", class_=re.compile(r"(main|primary|product|item|goods)", re.I))
        if img_tag and img_tag.get("src"):
            return img_tag["src"] if img_tag["src"].startswith("http") else None
        img_tag = soup.find("img", attrs={"data-src": True})
        if img_tag:
            src = img_tag["data-src"]
            if src.startswith("//"):
                src = "https:" + src
            return src if src.startswith("http") else None
        return None

    def _extract_weight(self, soup: BeautifulSoup, html: str) -> float:
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(kg|千克|公斤)',
            r'"weight"\s*[:=]\s*"?(\d+(?:\.\d+)?)"?',
            r'"weightKg"\s*[:=]\s*"?(\d+(?:\.\d+)?)"?',
            r'weight["\']?\s*:\s*(\d+(?:\.\d+)?)',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                val = float(match.group(1))
                if val > 0:
                    return round(val, 3)
        return 0.5

    def _check_cloudflare(self, html: str) -> bool:
        return bool(re.search(r'cloudflare|cf-browser-verification|challenge-platform|403 Forbidden', html, re.IGNORECASE))

    def get_platform_display_name(self, platform: ProductPlatform) -> str:
        names = {
            ProductPlatform.TAOBAO: "Taobao / Tmall",
            ProductPlatform.PINDUODUO: "Pinduoduo",
            ProductPlatform.ALIBABA1688: "1688 (Alibaba)",
            ProductPlatform.OTHER: "Other Platform",
        }
        return names.get(platform, "Unknown")

    def _get_cache_key(self, url: str) -> str:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        goods_id = params.get("goods_id", [None])[0] or params.get("ps", [None])[0]
        if goods_id:
            return f"{parsed.netloc}:{goods_id}"
        return url

    def _get_from_cache(self, url: str) -> Optional[Dict]:
        key = self._get_cache_key(url)
        entry = self._cache.get(key)
        if entry and (time.time() - entry["_ts"]) < self.CACHE_TTL:
            result = dict(entry)
            result.pop("_ts", None)
            return result
        return None

    def _set_cache(self, url: str, data: Dict):
        key = self._get_cache_key(url)
        entry = dict(data)
        entry["_ts"] = time.time()
        self._cache[key] = entry

    def clear_cache(self):
        self._cache.clear()

    def _status_for(self, has_title: bool, has_price: bool) -> str:
        if has_title and has_price:
            return "success"
        if has_title:
            return "partial"
        return "failed"

    async def extract(self, url: str) -> Dict[str, Any]:
        cached = self._get_from_cache(url)
        if cached:
            return cached

        result = {
            "url": url,
            "platform": self.detect_platform(url).value,
            "title": None,
            "price_cny": None,
            "original_price_cny": None,
            "image_url": None,
            "description": None,
            "weight_kg": 0.5,
            "status": "pending",
            "error": None,
        }

        try:
            async with httpx.AsyncClient(
                timeout=25.0,
                follow_redirects=True,
                headers=self.HEADERS,
            ) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    result["status"] = "failed"
                    result["error"] = f"HTTP {response.status_code}"
                    self._set_cache(url, result)
                    return result

                html = response.text

                if self._check_cloudflare(html):
                    result["status"] = "failed"
                    result["error"] = "blocked_by_cloudflare"
                    self._set_cache(url, result)
                    return result

                final_url = str(response.url)
                pdd_params = self._parse_pinduoduo_url(final_url)

                soup = BeautifulSoup(html, "lxml")
                json_ld = self._extract_json_ld(soup)
                og = self._extract_og_tags(soup)
                meta = self._extract_meta_tags(soup)
                script_data = self._extract_from_script_data(html)
                pdd_data = self._extract_pinduoduo_json(html)

                title = self._extract_title(soup, og, script_data, pdd_data)
                if title:
                    result["title"] = title

                price = self._extract_price(soup, json_ld, og, script_data, pdd_data, html)
                if price:
                    result["price_cny"] = price

                image = self._extract_image(soup, json_ld, og, script_data, pdd_data)
                if image:
                    result["image_url"] = image

                result["description"] = og.get("description") or meta.get("description", "")
                result["weight_kg"] = self._extract_weight(soup, html)
                result["status"] = self._status_for(bool(result["title"]), bool(result["price_cny"]))

                if result["status"] == "failed":
                    result["error"] = "Could not extract product details"
                elif result["status"] == "partial":
                    result["error"] = "price_not_found"

        except httpx.TimeoutException:
            result["status"] = "failed"
            result["error"] = "Request timeout - website took too long to respond"
        except httpx.RequestError as e:
            result["status"] = "failed"
            result["error"] = f"Network error: {str(e)}"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = f"Extraction error: {str(e)}"

        self._set_cache(url, result)
        return result


product_extractor = ProductExtractor()
