"""
Database models for the Afghanistan Purchasing Bot.
Uses SQLite with aiosqlite for async operations.
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import aiosqlite
from config import settings


class OrderStatus(str, Enum):
    """Order lifecycle statuses."""
    PENDING = "pending"           # Order created, awaiting payment
    PAID = "paid"                 # Payment confirmed at office
    PURCHASED = "purchased"       # Items purchased in China
    SHIPPED = "shipped"           # Shipped from China
    IN_TRANSIT = "in_transit"     # In transit to Afghanistan
    CUSTOMS = "customs"           # At customs
    DELIVERED = "delivered"       # Delivered to office
    COMPLETED = "completed"       # Customer picked up
    CANCELLED = "cancelled"       # Order cancelled


class ShippingMethod(str, Enum):
    """Available shipping methods."""
    AIR = "air"
    SEA = "sea"
    LAND = "land"


class PaymentMethod(str, Enum):
    """Payment methods."""
    OFFICE_CASH = "office_cash"
    OFFICE_BANK = "office_bank"


class UserRole(str, Enum):
    """User roles."""
    CUSTOMER = "customer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class ProductPlatform(str, Enum):
    """Supported e-commerce platforms."""
    TAOBAO = "taobao"
    PINDUODUO = "pinduoduo"
    ALIBABA1688 = "1688"
    OTHER = "other"


# SQL Schema for database initialization
SCHEMA_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    language TEXT DEFAULT 'en',
    role TEXT DEFAULT 'customer',
    referral_code TEXT UNIQUE,
    referred_by INTEGER REFERENCES users(id),
    referral_count INTEGER DEFAULT 0,
    referral_earnings REAL DEFAULT 0,
    total_orders INTEGER DEFAULT 0,
    total_spent REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exchange rates table (historical tracking)
CREATE TABLE IF NOT EXISTS exchange_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cny_to_afn REAL NOT NULL,
    usd_to_afn REAL,
    source TEXT DEFAULT 'manual',
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shipping rates table (admin configurable)
CREATE TABLE IF NOT EXISTS shipping_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    method TEXT NOT NULL UNIQUE,
    base_rate REAL NOT NULL,
    min_weight REAL DEFAULT 0,
    max_weight REAL DEFAULT 999,
    extra_per_kg REAL DEFAULT 0,
    estimated_days INTEGER NOT NULL,
    active BOOLEAN DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table (extracted from links)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    platform TEXT NOT NULL,
    title TEXT,
    description TEXT,
    price_cny REAL,
    original_price_cny REAL,
    image_url TEXT,
    weight_kg REAL DEFAULT 0,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_status TEXT DEFAULT 'pending'
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    status TEXT DEFAULT 'pending',
    shipping_method TEXT,
    shipping_address TEXT,
    total_product_cny REAL DEFAULT 0,
    total_product_afn REAL DEFAULT 0,
    shipping_cost_cny REAL DEFAULT 0,
    shipping_cost_afn REAL DEFAULT 0,
    service_fee_cny REAL DEFAULT 0,
    service_fee_afn REAL DEFAULT 0,
    photo_inspection_fee_cny REAL DEFAULT 0,
    photo_inspection_fee_afn REAL DEFAULT 0,
    total_cny REAL DEFAULT 0,
    total_afn REAL DEFAULT 0,
    exchange_rate_used REAL,
    payment_method TEXT,
    payment_status TEXT DEFAULT 'unpaid',
    paid_at TIMESTAMP,
    estimated_delivery TIMESTAMP,
    notes TEXT,
    referral_discount_afn REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items (many products per order)
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    product_url TEXT NOT NULL,
    product_title TEXT,
    quantity INTEGER DEFAULT 1,
    unit_price_cny REAL,
    unit_price_afn REAL,
    total_price_cny REAL,
    total_price_afn REAL,
    weight_kg REAL DEFAULT 0,
    photo_inspection BOOLEAN DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order status history (tracking notifications)
CREATE TABLE IF NOT EXISTS order_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    location TEXT,
    notes TEXT,
    notified BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Photo inspections
CREATE TABLE IF NOT EXISTS photo_inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_item_id INTEGER NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
    photo_url TEXT,
    photo_file_id TEXT,
    inspection_notes TEXT,
    status TEXT DEFAULT 'pending',
    taken_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Referrals tracking
CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL REFERENCES users(id),
    referred_id INTEGER NOT NULL REFERENCES users(id),
    reward_afn REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    order_id INTEGER REFERENCES orders(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fulfilled_at TIMESTAMP
);

-- Admin audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    table_name TEXT,
    record_id INTEGER,
    old_value TEXT,
    new_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_status_history_order_id ON order_status_history(order_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
"""


class Database:
    """Async database manager with connection pooling."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """Establish database connection."""
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        return self

    async def close(self):
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def init_schema(self):
        """Initialize database schema."""
        await self._connection.executescript(SCHEMA_SQL)
        await self._connection.commit()

        # Insert default shipping rates
        await self._connection.execute("""
            INSERT OR IGNORE INTO shipping_rates (method, base_rate, estimated_days)
            VALUES 
                ('air', ?, ?),
                ('sea', ?, ?),
                ('land', ?, ?)
        """, (
            settings.shipping_air_base, settings.delivery_air_days,
            settings.shipping_sea_base, settings.delivery_sea_days,
            settings.shipping_land_base, settings.delivery_land_days
        ))
        await self._connection.commit()

    async def execute(self, query: str, parameters: tuple = ()) -> aiosqlite.Cursor:
        """Execute a query."""
        cursor = await self._connection.execute(query, parameters)
        await self._connection.commit()
        return cursor

    async def fetchone(self, query: str, parameters: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row."""
        cursor = await self._connection.execute(query, parameters)
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def fetchall(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        cursor = await self._connection.execute(query, parameters)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def fetchval(self, query: str, parameters: tuple = ()) -> Any:
        """Fetch a single value."""
        cursor = await self._connection.execute(query, parameters)
        row = await cursor.fetchone()
        return row[0] if row else None

    # ── User Operations ──

    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID."""
        return await self.fetchone(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )

    async def create_user(self, telegram_id: int, username: str = None,
                         first_name: str = None, last_name: str = None,
                         language: str = "en", referred_by: int = None) -> int:
        """Create a new user and return the user ID."""
        import secrets
        referral_code = secrets.token_urlsafe(8)

        cursor = await self.execute("""
            INSERT INTO users (telegram_id, username, first_name, last_name, language, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (telegram_id, username, first_name, last_name, language, referral_code, referred_by))

        return cursor.lastrowid

    async def update_user(self, telegram_id: int, **kwargs) -> bool:
        """Update user fields."""
        if not kwargs:
            return False

        fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [telegram_id]

        await self.execute(
            f"UPDATE users SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            tuple(values)
        )
        return True

    async def get_user_by_referral(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Get user by referral code."""
        return await self.fetchone(
            "SELECT * FROM users WHERE referral_code = ?", (referral_code,)
        )

    # ── Order Operations ──

    async def create_order(self, user_id: int, order_number: str, **kwargs) -> int:
        """Create a new order."""
        columns = ["user_id", "order_number"] + list(kwargs.keys())
        placeholders = ", ".join(["?"] * len(columns))
        values = [user_id, order_number] + list(kwargs.values())

        cursor = await self.execute(
            f"INSERT INTO orders ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(values)
        )
        return cursor.lastrowid

    async def get_order(self, order_id: int = None, order_number: str = None) -> Optional[Dict[str, Any]]:
        """Get order by ID or order number."""
        if order_id:
            return await self.fetchone(
                "SELECT * FROM orders WHERE id = ?", (order_id,)
            )
        elif order_number:
            return await self.fetchone(
                "SELECT * FROM orders WHERE order_number = ?", (order_number,)
            )
        return None

    async def get_user_orders(self, user_id: int, status: str = None) -> List[Dict[str, Any]]:
        """Get all orders for a user."""
        if status:
            return await self.fetchall(
                "SELECT * FROM orders WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                (user_id, status)
            )
        return await self.fetchall(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )

    async def update_order_status(self, order_id: int, status: str, notes: str = None) -> bool:
        """Update order status and log history."""
        await self.execute(
            "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, order_id)
        )

        await self.execute(
            "INSERT INTO order_status_history (order_id, status, notes) VALUES (?, ?, ?)",
            (order_id, status, notes)
        )
        return True

    async def get_order_items(self, order_id: int) -> List[Dict[str, Any]]:
        """Get items for an order."""
        return await self.fetchall(
            "SELECT * FROM order_items WHERE order_id = ?", (order_id,)
        )

    async def add_order_item(self, order_id: int, product_url: str, **kwargs) -> int:
        """Add an item to an order."""
        columns = ["order_id", "product_url"] + list(kwargs.keys())
        placeholders = ", ".join(["?"] * len(columns))
        values = [order_id, product_url] + list(kwargs.values())

        cursor = await self.execute(
            f"INSERT INTO order_items ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(values)
        )
        return cursor.lastrowid

    # ── Exchange Rate Operations ──

    async def get_latest_rate(self) -> Optional[float]:
        """Get the latest CNY to AFN exchange rate."""
        rate = await self.fetchval(
            "SELECT cny_to_afn FROM exchange_rates ORDER BY fetched_at DESC LIMIT 1"
        )
        return rate or settings.fallback_cny_to_afn

    async def set_exchange_rate(self, cny_to_afn: float, source: str = "manual") -> None:
        """Set a new exchange rate."""
        await self.execute(
            "INSERT INTO exchange_rates (cny_to_afn, source) VALUES (?, ?)",
            (cny_to_afn, source)
        )

    # ── Shipping Rate Operations ──

    async def get_shipping_rates(self) -> List[Dict[str, Any]]:
        """Get all active shipping rates."""
        return await self.fetchall(
            "SELECT * FROM shipping_rates WHERE active = 1 ORDER BY base_rate"
        )

    async def update_shipping_rate(self, method: str, base_rate: float, estimated_days: int) -> bool:
        """Update shipping rate (admin only)."""
        await self.execute(
            "UPDATE shipping_rates SET base_rate = ?, estimated_days = ?, updated_at = CURRENT_TIMESTAMP WHERE method = ?",
            (base_rate, estimated_days, method)
        )
        return True

    # ── Referral Operations ──

    async def create_referral(self, referrer_id: int, referred_id: int) -> int:
        """Record a referral."""
        cursor = await self.execute(
            "INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
            (referrer_id, referred_id)
        )

        # Update referrer count
        await self.execute(
            "UPDATE users SET referral_count = referral_count + 1 WHERE id = ?",
            (referrer_id,)
        )
        return cursor.lastrowid

    async def fulfill_referral(self, referral_id: int, order_id: int, reward_afn: float) -> bool:
        """Mark referral as fulfilled with reward."""
        await self.execute(
            """UPDATE referrals 
               SET status = 'fulfilled', order_id = ?, reward_afn = ?, fulfilled_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (order_id, reward_afn, referral_id)
        )

        # Update referrer earnings
        referrer = await self.fetchone(
            "SELECT referrer_id FROM referrals WHERE id = ?", (referral_id,)
        )
        if referrer:
            await self.execute(
                "UPDATE users SET referral_earnings = referral_earnings + ? WHERE id = ?",
                (reward_afn, referrer["referrer_id"])
            )
        return True

    # ── Statistics ──

    async def get_stats(self) -> Dict[str, Any]:
        """Get business statistics."""
        total_users = await self.fetchval("SELECT COUNT(*) FROM users")
        total_orders = await self.fetchval("SELECT COUNT(*) FROM orders")
        pending_orders = await self.fetchval("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
        total_revenue = await self.fetchval("SELECT COALESCE(SUM(total_afn), 0) FROM orders WHERE payment_status = 'paid'")

        return {
            "total_users": total_users,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "total_revenue_afn": total_revenue
        }


# Singleton database instance
db = Database()
