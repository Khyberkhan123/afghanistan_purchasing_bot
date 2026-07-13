"""
Inline and reply keyboard builders for the bot.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional
from bot.utils.i18n import get_text, get_supported_languages


def language_selection_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for language selection."""
    builder = InlineKeyboardBuilder()
    languages = get_supported_languages()

    for code, name in languages.items():
        builder.button(text=name, callback_data=f"lang:{code}")

    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Main menu keyboard."""
    builder = InlineKeyboardBuilder()

    builder.button(text="🛒 " + get_text("add_to_cart", lang), callback_data="menu:new_order")
    builder.button(text="📦 " + get_text("tracking_header", lang).split(":")[0], callback_data="menu:track")
    builder.button(text="🎁 " + get_text("referral_info", lang).split("\n")[0], callback_data="menu:referral")
    builder.button(text="⚙️ " + get_text("select_language", lang).split("\n")[0], callback_data="menu:language")
    builder.button(text="📞 " + get_text("error_generic", lang).split("\n")[0], callback_data="menu:support")

    builder.adjust(1)
    return builder.as_markup()


def shipping_method_keyboard(methods: List[dict], lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for selecting shipping method."""
    builder = InlineKeyboardBuilder()

    for method in methods:
        text = f"{method['icon']} {method['name']} - ¥{method['base_rate_cny']}/kg (~{method['estimated_days']} days)"
        builder.button(text=text, callback_data=f"shipping:{method['method']}")

    builder.button(text=get_text("back", lang), callback_data="order:back")
    builder.adjust(1)
    return builder.as_markup()


def quantity_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Quick quantity selection keyboard."""
    builder = InlineKeyboardBuilder()

    for qty in [1, 2, 3, 5, 10]:
        builder.button(text=str(qty), callback_data=f"qty:{qty}")

    builder.button(text=get_text("cancel", lang), callback_data="order:cancel")
    builder.adjust(5, 1)
    return builder.as_markup()


def photo_inspection_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Yes/No keyboard for photo inspection."""
    builder = InlineKeyboardBuilder()

    builder.button(text=get_text("yes", lang), callback_data="photo:yes")
    builder.button(text=get_text("no", lang), callback_data="photo:no")
    builder.adjust(2)
    return builder.as_markup()


def order_confirmation_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Order confirmation keyboard."""
    builder = InlineKeyboardBuilder()

    builder.button(text=get_text("confirm", lang), callback_data="order:confirm")
    builder.button(text=get_text("cancel", lang), callback_data="order:cancel")
    builder.button(text="➕ " + get_text("add_to_cart", lang), callback_data="order:add_more")
    builder.adjust(2, 1)
    return builder.as_markup()


def payment_keyboard(order_number: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Payment options keyboard."""
    builder = InlineKeyboardBuilder()

    builder.button(text="💵 " + get_text("payment_instructions", lang).split("\n")[0], 
                   callback_data=f"payment:office:{order_number}")
    builder.button(text=get_text("back", lang), callback_data="order:back")
    builder.adjust(1)
    return builder.as_markup()


def admin_panel_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Admin panel keyboard."""
    builder = InlineKeyboardBuilder()

    builder.button(text="📊 Stats", callback_data="admin:stats")
    builder.button(text="📋 Orders", callback_data="admin:orders")
    builder.button(text="💱 Exchange Rate", callback_data="admin:rate")
    builder.button(text="🚚 Shipping Rates", callback_data="admin:shipping")
    builder.button(text="👥 Users", callback_data="admin:users")
    builder.button(text="🔔 Broadcast", callback_data="admin:broadcast")
    builder.button(text=get_text("back", lang), callback_data="menu:main")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def order_status_keyboard(order_id: int, current_status: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for updating order status (admin)."""
    builder = InlineKeyboardBuilder()

    statuses = [
        ("🛒 Purchased", "purchased"),
        ("📦 Shipped", "shipped"),
        ("🚚 In Transit", "in_transit"),
        ("🛃 Customs", "customs"),
        ("📍 Delivered", "delivered"),
        ("✅ Completed", "completed"),
        ("❌ Cancelled", "cancelled"),
    ]

    for label, status in statuses:
        if status != current_status:
            builder.button(text=label, callback_data=f"admin:status:{order_id}:{status}")

    builder.button(text=get_text("back", lang), callback_data="admin:orders")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def remove_item_keyboard(item_index: int, lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard to remove an item from order."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑️ Remove", callback_data=f"remove_item:{item_index}")
    return builder.as_markup()


def contact_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Reply keyboard with contact sharing button."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Share Contact", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def remove_reply_keyboard() -> InlineKeyboardMarkup:
    """Empty reply keyboard to remove existing one."""
    return InlineKeyboardMarkup(inline_keyboard=[])
