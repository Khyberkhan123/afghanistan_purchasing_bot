"""
Order tracking and referral handlers.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime

from config import settings
from bot.database import db
from bot.utils.i18n import get_text
from bot.utils.keyboards import main_menu_keyboard

router = Router()


@router.message(Command("track"))
async def cmd_track(message: Message, lang: str = "en"):
    """Handle /track command."""
    args = message.text.split()

    if len(args) < 2:
        await message.answer(
            "📦 Please provide an order number.\n"
            "Example: /track AFG-20240713-ABC123"
        )
        return

    order_number = args[1]
    await show_tracking_info(message, order_number, lang)


@router.callback_query(F.data == "menu:track")
async def menu_track(callback: CallbackQuery, lang: str = "en"):
    """Handle track menu button."""
    await callback.answer()
    await callback.message.edit_text(
        "📦 Send /track &lt;order_number&gt; to check your order status.\n\n"
        "Example: /track AFG-20240713-ABC123",
        reply_markup=main_menu_keyboard(lang)
    )


async def show_tracking_info(message_or_callback, order_number: str, lang: str):
    """Display tracking information for an order."""
    order = await db.get_order(order_number=order_number)

    if not order:
        text = f"❌ Order #{order_number} not found. Please check the order number."
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(text)
        else:
            await message_or_callback.message.edit_text(text)
        return

    # Get status history
    history = await db.fetchall(
        "SELECT * FROM order_status_history WHERE order_id = ? ORDER BY created_at DESC",
        (order["id"],)
    )

    # Get order items
    items = await db.get_order_items(order["id"])

    # Build tracking message
    status_emoji = {
        "pending": "⏳",
        "paid": "💳",
        "purchased": "🛒",
        "shipped": "📦",
        "in_transit": "🚚",
        "customs": "🛃",
        "delivered": "📍",
        "completed": "✅",
        "cancelled": "❌",
    }

    status_display = {
        "pending": "Pending Payment",
        "paid": "Paid - Processing",
        "purchased": "Purchased in China",
        "shipped": "Shipped from China",
        "in_transit": "In Transit",
        "customs": "At Customs",
        "delivered": "Delivered to Office",
        "completed": "Completed",
        "cancelled": "Cancelled",
    }

    emoji = status_emoji.get(order["status"], "📦")
    status_name = status_display.get(order["status"], order["status"])

    items_text = ""
    for item in items:
        items_text += f"• {item.get('product_title', 'Product')} x{item['quantity']}\n"

    history_text = ""
    for h in history[:5]:
        time_str = h["created_at"][:16] if isinstance(h["created_at"], str) else h["created_at"].strftime("%Y-%m-%d %H:%M")
        history_text += f"  {status_emoji.get(h['status'], '•')} {status_display.get(h['status'], h['status'])} - {time_str}\n"

    if not history_text:
        history_text = "  • Order created\n"

    tracking_text = f"""
{emoji} <b>{get_text("tracking_header", lang, order_number=order_number)}</b>

📋 <b>Status:</b> {status_name}
💰 <b>Total:</b> {order['total_afn']} AFN
🚚 <b>Shipping:</b> {order.get('shipping_method', 'Not selected').upper()}
📅 <b>Created:</b> {order['created_at'][:10] if isinstance(order['created_at'], str) else order['created_at'].strftime('%Y-%m-%d')}

📦 <b>Items:</b>
{items_text}
📝 <b>Status History:</b>
{history_text}
    """

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
