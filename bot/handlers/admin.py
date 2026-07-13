"""
Admin panel handlers.
Order management, exchange rates, shipping rates, and statistics.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import settings
from bot.database import db, OrderStatus
from bot.services import exchange_service, shipping_service
from bot.utils.i18n import get_text
from bot.utils.keyboards import admin_panel_keyboard, order_status_keyboard, main_menu_keyboard

router = Router()


class AdminStates(StatesGroup):
    """FSM states for admin operations."""
    waiting_for_rate = State()
    waiting_for_shipping_rate = State()
    waiting_for_broadcast = State()
    waiting_for_order_search = State()


# ── Admin Access Filter ──

@router.message(Command("admin"))
async def cmd_admin(message: Message, is_admin: bool, lang: str = "en"):
    """Handle /admin command."""
    if not is_admin:
        await message.answer(get_text("not_authorized", lang))
        return

    await message.answer(
        get_text("admin_panel", lang),
        reply_markup=admin_panel_keyboard(lang)
    )


# ── Statistics ──

@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery, is_admin: bool, lang: str = "en"):
    """Show business statistics."""
    if not is_admin:
        await callback.answer(get_text("not_authorized", lang), show_alert=True)
        return

    stats = await db.get_stats()

    stats_text = get_text(
        "stats_overview", lang,
        users=stats["total_users"],
        orders=stats["total_orders"],
        pending=stats["pending_orders"],
        revenue=round(stats["total_revenue_afn"], 2)
    )

    await callback.answer()
    await callback.message.edit_text(
        stats_text,
        reply_markup=admin_panel_keyboard(lang)
    )


# ── Order Management ──

@router.callback_query(F.data == "admin:orders")
async def admin_orders(callback: CallbackQuery, is_admin: bool, lang: str = "en"):
    """Show recent orders."""
    if not is_admin:
        await callback.answer(get_text("not_authorized", lang), show_alert=True)
        return

    orders = await db.fetchall(
        """SELECT o.*, u.username, u.first_name, u.telegram_id 
           FROM orders o 
           JOIN users u ON o.user_id = u.id 
           ORDER BY o.created_at DESC LIMIT 10"""
    )

    if not orders:
        await callback.answer()
        await callback.message.edit_text(
            "No orders found.",
            reply_markup=admin_panel_keyboard(lang)
        )
        return

    orders_text = "📋 <b>Recent Orders</b>\n\n"
    for order in orders:
        status_emoji = {
            "pending": "⏳", "paid": "💳", "purchased": "🛒",
            "shipped": "📦", "in_transit": "🚚", "customs": "🛃",
            "delivered": "📍", "completed": "✅", "cancelled": "❌",
        }.get(order["status"], "•")

        orders_text += (
            f"{status_emoji} <b>#{order['order_number']}</b>\n"
            f"   👤 {order.get('first_name', 'Unknown')} (@{order.get('username', 'N/A')})\n"
            f"   💰 {order['total_afn']} AFN | {order['status'].upper()}\n"
            f"   📅 {order['created_at'][:10] if isinstance(order['created_at'], str) else order['created_at'].strftime('%Y-%m-%d')}\n\n"
        )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Search Order", callback_data="admin:search_order")],
        [InlineKeyboardButton(text=get_text("back", lang), callback_data="admin:panel")]
    ])

    await callback.answer()
    await callback.message.edit_text(orders_text, reply_markup=kb)


@router.callback_query(F.data == "admin:search_order")
async def admin_search_order(callback: CallbackQuery, is_admin: bool, state: FSMContext, lang: str = "en"):
    """Prompt for order search."""
    if not is_admin:
        await callback.answer(get_text("not_authorized", lang), show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        "🔍 Send the order number to search:\nExample: AFG-20240713-ABC123"
    )
    await state.set_state(AdminStates.waiting_for_order_search)


@router.message(AdminStates.waiting_for_order_search)
async def process_order_search(message: Message, is_admin: bool, state: FSMContext, lang: str = "en"):
    """Process order search."""
    if not is_admin:
        await message.answer(get_text("not_authorized", lang))
        await state.clear()
        return

    order_number = message.text.strip()
    order = await db.get_order(order_number=order_number)

    if not order:
        await message.answer(f"❌ Order #{order_number} not found.")
        await state.clear()
        return

    # Get user info
    user = await db.fetchone("SELECT * FROM users WHERE id = ?", (order["user_id"],))

    # Get items
    items = await db.get_order_items(order["id"])

    items_text = ""
    for item in items:
        items_text += f"• {item.get('product_title', 'Product')} x{item['quantity']} - ¥{item['unit_price_cny']}\n"

    order_text = f"""
📋 <b>Order #{order['order_number']}</b>

👤 <b>Customer:</b> {user.get('first_name', 'Unknown')} (@{user.get('username', 'N/A')})
📞 <b>Phone:</b> {user.get('phone', 'Not provided')}
📅 <b>Created:</b> {order['created_at'][:16] if isinstance(order['created_at'], str) else order['created_at'].strftime('%Y-%m-%d %H:%M')}

📦 <b>Items:</b>
{items_text}
💰 <b>Total:</b> {order['total_afn']} AFN
🚚 <b>Shipping:</b> {order.get('shipping_method', 'N/A').upper()}
💳 <b>Payment:</b> {order.get('payment_status', 'unpaid').upper()}
📊 <b>Status:</b> {order['status'].upper()}

Select new status:
    """

    await message.answer(
        order_text,
        reply_markup=order_status_keyboard(order["id"], order["status"], lang)
    )
    await state.clear()


@router.callback_query(F.data.startswith("admin:status:"))
async def update_order_status(callback: CallbackQuery, is_admin: bool, lang: str = "en"):
    """Update order status."""
    if not is_admin:
        await callback.answer(get_text("not_authorized", lang), show_alert=True)
        return

    parts = callback.data.split(":")
    order_id = int(parts[2])
    new_status = parts[3]

    await db.update_order_status(order_id, new_status)

    # Get order and notify customer
    order = await db.get_order(order_id)
    if order:
        user = await db.fetchone("SELECT * FROM users WHERE id = ?", (order["user_id"],))
        if user:
            # Notify customer of status update
            from aiogram import Bot
            bot = callback.bot

            status_names = {
                "purchased": "🛒 Purchased in China",
                "shipped": "📦 Shipped from China",
                "in_transit": "🚚 In Transit",
                "customs": "🛃 At Customs",
                "delivered": "📍 Delivered to Office",
                "completed": "✅ Completed",
                "cancelled": "❌ Cancelled",
            }

            notify_text = get_text(
                "status_update", lang,
                order_number=order["order_number"],
                status=status_names.get(new_status, new_status),
                location="",
                notes="",
                time="Now"
            )

            try:
                await bot.send_message(user["telegram_id"], notify_text)
            except Exception:
                pass  # User may have blocked the bot

    await callback.answer(f"Status updated to {new_status}")
    await callback.message.edit_text(
        f"✅ Order status updated to: {new_status.upper()}",
        reply_markup=admin_panel_keyboard(lang)
    )


# ── Exchange Rate Management ──

@router.callback_query(F.data == "admin:rate")
async def admin_rate(callback: CallbackQuery, is_admin: bool, state: FSMContext, lang: str = "en"):
    """Show current exchange rate and option to update."""
    if not is_admin:
        await callback.answer(get_text("not_authorized", lang), show_alert=True)
        return

    current_rate = await exchange_service.get_rate()

    await callback.answer()
    await callback.message.edit_text(
        f"💱 <b>Exchange Rate Management</b>\n\n"
        f"Current Rate: <b>1 CNY = {current_rate} AFN</b>\n\n"
        f"Send a new rate to update (e.g., 9.85):",
        reply_markup=main_menu_keyboard(lang)
    )
    await state.set_state(AdminStates.waiting_for_rate)


@router.message(AdminStates.waiting_for_rate)
async def process_rate_update(message: Message, is_admin: bool, state: FSMContext, lang: str = "en"):
    """Process exchange rate update."""
    if not is_admin:
        await message.answer(get_text("not_authorized", lang))
        await state.clear()
        return

    try:
        new_rate = float(message.text.strip())
        await exchange_service.set_manual_rate(new_rate)

        await message.answer(
            f"✅ Exchange rate updated!\n"
            f"New rate: <b>1 CNY = {new_rate} AFN</b>"
        )
    except ValueError:
        await message.answer("❌ Invalid rate. Please send a number like 9.85")

    await state.clear()


# ── Shipping Rate Management ──

@router.callback_query(F.data == "admin:shipping")
async def admin_shipping(callback: CallbackQuery, is_admin: bool, state: FSMContext, lang: str = "en"):
    """Show shipping rates and option to update."""
    if not is_admin:
        await callback.answer(get_text("not_authorized", lang), show_alert=True)
        return

    rates = await db.get_shipping_rates()

    rates_text = "🚚 <b>Shipping Rates</b>\n\n"
    for rate in rates:
        rates_text += (
            f"{rate['method'].upper()}: ¥{rate['base_rate']}/kg\n"
            f"   Est. Delivery: {rate['estimated_days']} days\n\n"
        )

    rates_text += "Send rate update in format:\nMETHOD RATE DAYS\nExample: air 85 7"

    await callback.answer()
    await callback.message.edit_text(rates_text)
    await state.set_state(AdminStates.waiting_for_shipping_rate)


@router.message(AdminStates.waiting_for_shipping_rate)
async def process_shipping_rate(message: Message, is_admin: bool, state: FSMContext, lang: str = "en"):
    """Process shipping rate update."""
    if not is_admin:
        await message.answer(get_text("not_authorized", lang))
        await state.clear()
        return

    parts = message.text.strip().split()

    if len(parts) < 3:
        await message.answer("❌ Invalid format. Use: METHOD RATE DAYS\nExample: air 85 7")
        return

    try:
        method = parts[0].lower()
        rate = float(parts[1])
        days = int(parts[2])

        await db.update_shipping_rate(method, rate, days)

        await message.answer(
            f"✅ Shipping rate updated!\n"
            f"{method.upper()}: ¥{rate}/kg, {days} days"
        )
    except (ValueError, Exception) as e:
        await message.answer(f"❌ Error: {str(e)}")

    await state.clear()


# ── Broadcast ──

@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast(callback: CallbackQuery, is_admin: bool, state: FSMContext, lang: str = "en"):
    """Prompt for broadcast message."""
    if not is_admin:
        await callback.answer(get_text("not_authorized", lang), show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        "📢 <b>Broadcast Message</b>\n\n"
        "Send the message you want to broadcast to all users:",
        reply_markup=main_menu_keyboard(lang)
    )
    await state.set_state(AdminStates.waiting_for_broadcast)


@router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: Message, is_admin: bool, state: FSMContext, lang: str = "en"):
    """Send broadcast to all users."""
    if not is_admin:
        await message.answer(get_text("not_authorized", lang))
        await state.clear()
        return

    broadcast_text = message.text
    users = await db.fetchall("SELECT telegram_id FROM users")

    sent = 0
    failed = 0

    for user in users:
        try:
            await message.bot.send_message(user["telegram_id"], broadcast_text)
            sent += 1
        except Exception:
            failed += 1

    await message.answer(
        f"📢 Broadcast sent!\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )
    await state.clear()


@router.callback_query(F.data == "admin:users")
async def admin_users(callback: CallbackQuery, is_admin: bool, lang: str = "en"):
    """Show users list (admin only)."""
    if not is_admin:
        await callback.answer(get_text("not_authorized", lang), show_alert=True)
        return

    users = await db.fetchall(
        "SELECT telegram_id, username, first_name, language, total_orders, total_spent, created_at "
        "FROM users ORDER BY created_at DESC LIMIT 20"
    )

    if not users:
        await callback.answer()
        await callback.message.edit_text("No users found.", reply_markup=admin_panel_keyboard(lang))
        return

    text = "👥 <b>Recent Users</b>\n\n"
    for u in users:
        name = u.get("first_name") or u.get("username") or str(u["telegram_id"])
        text += f"• {name} (@{u.get('username', 'N/A')}) | {u.get('language', 'en')} | {u.get('total_orders', 0)} orders | {u.get('total_spent', 0)} AFN\n"

    await callback.answer()
    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard(lang))


@router.callback_query(F.data == "admin:panel")
async def back_to_admin(callback: CallbackQuery, is_admin: bool, lang: str = "en"):
    """Return to admin panel."""
    if not is_admin:
        await callback.answer(get_text("not_authorized", lang), show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        get_text("admin_panel", lang),
        reply_markup=admin_panel_keyboard(lang)
    )
