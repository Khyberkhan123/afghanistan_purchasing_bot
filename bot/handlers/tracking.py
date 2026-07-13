"""
Order tracking and referral handlers.
"""
import re
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime

from config import settings
from bot.database import db
from bot.utils.i18n import get_text
from bot.utils.keyboards import main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("track"))
async def cmd_track(message: Message, lang: str = "en"):
    """Handle /track command."""
    args = message.text.split()

    if len(args) < 2:
        await message.answer(
            "📦 <b>Track Order</b>\n\n"
            "Please provide an order number:\n"
            "<code>/track AFG-YYYYMMDD-XXX</code>\n\n"
            "You can find your order number in the confirmation message."
        )
        return

    order_number = args[1].strip()
    if not re.match(r"^AFG-\d{8}-[A-Z0-9]+$", order_number):
        await message.answer(
            "❌ Invalid order number format.\n"
            "Expected: <code>AFG-YYYYMMDD-XXX</code>\n"
            "Example: <code>/track AFG-20240713-ABC123</code>"
        )
        return

    await show_tracking_info(message, order_number, lang)


@router.callback_query(F.data == "menu:track")
async def menu_track(callback: CallbackQuery, lang: str = "en"):
    """Handle track menu button."""
    await callback.answer()
    await callback.message.edit_text(
        "📦 <b>Track Order</b>\n\n"
        "Send the order number using:\n"
        "<code>/track AFG-YYYYMMDD-XXX</code>\n\n"
        "Example: <code>/track AFG-20240713-ABC123</code>",
        reply_markup=main_menu_keyboard(lang)
    )


async def show_tracking_info(message_or_callback, order_number: str, lang: str):
    """Display tracking information for an order."""
    try:
        order = await db.get_order(order_number=order_number)
    except Exception as e:
        logger.exception("Database error fetching order %s", order_number)
        err_text = "❌ Database error. Please try again later."
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(err_text)
        else:
            await message_or_callback.message.edit_text(err_text)
        return

    if not order:
        text = (
            f"❌ Order <b>{order_number}</b> not found.\n\n"
            "Double-check the order number or contact support."
        )
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(text)
        else:
            await message_or_callback.message.edit_text(text)
        return

    try:
        history = await db.fetchall(
            "SELECT * FROM order_status_history WHERE order_id = ? ORDER BY created_at DESC",
            (order["id"],)
        )
        items = await db.get_order_items(order["id"])
    except Exception as e:
        logger.exception("Database error for order %s", order_number)
        err_text = "❌ Error loading order details."
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(err_text)
        else:
            await message_or_callback.message.edit_text(err_text)
        return

    status_emoji = {
        "pending": "⏳", "paid": "💳", "purchased": "🛒",
        "shipped": "📦", "in_transit": "🚚", "customs": "🛃",
        "delivered": "📍", "completed": "✅", "cancelled": "❌",
    }

    status_display = {
        "pending": "Pending Payment", "paid": "Paid - Processing",
        "purchased": "Purchased in China", "shipped": "Shipped from China",
        "in_transit": "In Transit", "customs": "At Customs",
        "delivered": "Delivered to Office", "completed": "Completed",
        "cancelled": "Cancelled",
    }

    emoji = status_emoji.get(order["status"], "📦")
    status_name = status_display.get(order["status"], order["status"])

    items_text = ""
    for item in items:
        title = item.get("product_title", "Product") or "Product"
        items_text += f"• {title} x{item['quantity']}\n"
    if not items_text:
        items_text = "  • (no items)\n"

    history_text = ""
    for h in history[:5]:
        raw = h["created_at"]
        if isinstance(raw, str):
            time_str = raw[:16]
        else:
            time_str = raw.strftime("%Y-%m-%d %H:%M") if hasattr(raw, "strftime") else str(raw)
        hs = h["status"]
        history_text += f"  {status_emoji.get(hs, '•')} {status_display.get(hs, hs)} - {time_str}\n"
    if not history_text:
        history_text = "  • Order placed\n"

    created = order["created_at"]
    if isinstance(created, str):
        created_str = created[:10]
    else:
        created_str = created.strftime("%Y-%m-%d") if hasattr(created, "strftime") else str(created)

    tracking_text = (
        f"{emoji} <b>Order #{order_number}</b>\n\n"
        f"📋 <b>Status:</b> {status_name}\n"
        f"💰 <b>Total:</b> {order['total_afn']} AFN\n"
        f"🚚 <b>Shipping:</b> {order.get('shipping_method', 'Not selected').upper()}\n"
        f"📅 <b>Created:</b> {created_str}\n\n"
        f"📦 <b>Items:</b>\n{items_text}\n"
        f"📝 <b>Status History:</b>\n{history_text}"
    )

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(tracking_text)
    else:
        await message_or_callback.message.edit_text(tracking_text)


# ── Referral System ──

@router.message(Command("referral"))
async def cmd_referral(message: Message, lang: str = "en"):
    """Handle /referral command."""
    user = await db.get_user(message.from_user.id)

    if not user:
        await message.answer("Please start the bot first with /start")
        return

    referral_text = get_text(
        "referral_info", lang,
        code=user["referral_code"],
        min=settings.referral_min_order_afn,
        reward=settings.referral_reward_afn,
        count=user["referral_count"],
        earnings=user["referral_earnings"]
    )

    # Add share button
    share_url = f"https://t.me/{settings.bot_username}?start={user['referral_code']}"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Share Referral Link", url=share_url)],
        [InlineKeyboardButton(text=get_text("back", lang), callback_data="menu:main")]
    ])

    await message.answer(referral_text, reply_markup=keyboard)


@router.callback_query(F.data == "menu:referral")
async def menu_referral(callback: CallbackQuery, lang: str = "en"):
    """Handle referral menu button."""
    await callback.answer()
    await cmd_referral(callback.message, lang)
