"""
Order flow handlers.
Product link extraction, quantity selection, shipping, and order confirmation.
"""
import re
import secrets
import logging
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import settings
from bot.database import db, OrderStatus
from bot.services import product_extractor, exchange_service, shipping_service
from bot.utils.i18n import get_text
from bot.utils.keyboards import (
    quantity_keyboard, photo_inspection_keyboard, 
    shipping_method_keyboard, order_confirmation_keyboard,
    payment_keyboard, main_menu_keyboard, remove_item_keyboard
)

router = Router()
logger = logging.getLogger(__name__)


class OrderStates(StatesGroup):
    """FSM states for order creation flow."""
    waiting_for_link = State()
    waiting_for_price = State()
    waiting_for_quantity = State()
    waiting_for_photo_inspection = State()
    waiting_for_shipping = State()
    waiting_for_confirmation = State()


# ── Product Link Handling ──

URL_PATTERN = re.compile(
    r"https?://(?:www\.)?"
    r"(?:"
    r"item\.taobao\.com|detail\.tmall\.com|taobao\.com/item|"
    r"mobile\.yangkeduo\.com|yangkeduo\.com|pinduoduo\.com|"
    r"detail\.1688\.com|1688\.com"
    r")"
    r"[/\w\-\.?=&%]*", 
    re.IGNORECASE
)


@router.message(F.text.regexp(URL_PATTERN))
async def handle_product_link(message: Message, state: FSMContext, lang: str = "en"):
    """Handle product link sent by user."""
    url = message.text.strip()
    user = message.from_user

    # Show processing message
    processing_msg = await message.answer("🔍 " + get_text("product_found", lang).split("\n")[0] + "...")

    # Extract product info
    product = await product_extractor.extract(url)

    if product["status"] == "success":
        await state.update_data(
            current_product=product,
            order_items=[],
            exchange_rate=await exchange_service.get_rate()
        )

        price_afn = round(product["price_cny"] * (await exchange_service.get_rate()), 2)

        product_text = get_text(
            "product_found", lang,
            title=product["title"] or "Unknown Product",
            price_cny=product["price_cny"],
            price_afn=price_afn,
            platform=product_extractor.get_platform_display_name(product_extractor.detect_platform(url)),
            weight=product["weight_kg"]
        )

        if product["image_url"]:
            try:
                await message.answer_photo(
                    photo=product["image_url"],
                    caption=product_text,
                    reply_markup=quantity_keyboard(lang)
                )
                await processing_msg.delete()
            except Exception:
                await processing_msg.edit_text(
                    product_text,
                    reply_markup=quantity_keyboard(lang)
                )
        else:
            await processing_msg.edit_text(
                product_text,
                reply_markup=quantity_keyboard(lang)
            )

        await state.set_state(OrderStates.waiting_for_quantity)

    elif product["status"] == "partial":
        await state.update_data(
            pending_product=product,
            order_items=[],
            exchange_rate=await exchange_service.get_rate()
        )

        price_afn = round((product["price_cny"] or 0) * (await exchange_service.get_rate()), 2)

        product_text = get_text(
            "product_partial", lang,
            title=product["title"] or "Unknown Product",
            platform=product_extractor.get_platform_display_name(product_extractor.detect_platform(url)),
            weight=product["weight_kg"]
        )

        if product["image_url"]:
            try:
                await message.answer_photo(
                    photo=product["image_url"],
                    caption=product_text,
                )
                await processing_msg.delete()
            except Exception:
                await processing_msg.edit_text(product_text)
        else:
            await processing_msg.edit_text(product_text)

        await state.set_state(OrderStates.waiting_for_price)

    else:
        await processing_msg.edit_text(
            get_text("product_not_found", lang)
        )
        await state.set_state(OrderStates.waiting_for_link)


@router.message(OrderStates.waiting_for_price)
async def handle_price_input(message: Message, state: FSMContext, lang: str = "en"):
    """Handle manual price input when extraction found title but no price."""
    text = message.text.strip()
    text = text.replace("¥", "").replace("CNY", "").replace("$", "").replace(",", "").strip()

    try:
        price = float(text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer(get_text("invalid_price", lang))
        return

    data = await state.get_data()
    product = data.get("pending_product")
    if not product:
        await message.answer(get_text("product_not_found", lang))
        await state.set_state(OrderStates.waiting_for_link)
        return

    product["price_cny"] = price
    product["status"] = "success"
    product["original_price_cny"] = price

    await state.update_data(current_product=product, pending_product=None)

    price_afn = round(price * data.get("exchange_rate", await exchange_service.get_rate()), 2)

    product_text = get_text(
        "product_found", lang,
        title=product["title"] or "Unknown Product",
        price_cny=price,
        price_afn=price_afn,
        platform=product_extractor.get_platform_display_name(product_extractor.detect_platform(product["url"])),
        weight=product["weight_kg"]
    )

    await message.answer(
        product_text,
        reply_markup=quantity_keyboard(lang)
    )
    await state.set_state(OrderStates.waiting_for_quantity)


@router.callback_query(F.data.startswith("qty:"), OrderStates.waiting_for_quantity)
async def process_quantity(callback: CallbackQuery, state: FSMContext, lang: str = "en"):
    """Handle quantity selection."""
    quantity = int(callback.data.split(":")[1])

    data = await state.get_data()
    product = data["current_product"]

    # Update product with quantity
    product["quantity"] = quantity
    product["total_price_cny"] = round(product["price_cny"] * quantity, 2)

    await state.update_data(current_product=product)

    await callback.answer()

    # Ask about photo inspection
    photo_fee_cny = settings.photo_inspection_fee
    rate = data.get("exchange_rate", await exchange_service.get_rate())
    photo_fee_afn = round(photo_fee_cny * rate, 2)

    await callback.message.edit_text(
        get_text(
            "photo_inspection_prompt", lang,
            fee=photo_fee_cny,
            fee_afn=photo_fee_afn
        ),
        reply_markup=photo_inspection_keyboard(lang)
    )

    await state.set_state(OrderStates.waiting_for_photo_inspection)


@router.callback_query(F.data.startswith("photo:"), OrderStates.waiting_for_photo_inspection)
async def process_photo_inspection(callback: CallbackQuery, state: FSMContext, lang: str = "en"):
    """Handle photo inspection choice."""
    wants_photo = callback.data == "photo:yes"

    data = await state.get_data()
    product = data["current_product"]
    product["photo_inspection"] = wants_photo

    # Add to order items
    items = data.get("order_items", [])
    items.append(product)

    await state.update_data(
        order_items=items,
        current_product=None
    )

    await callback.answer()

    # Show current cart and ask for shipping method
    await show_order_summary(callback, state, lang, editable=True)
    await state.set_state(OrderStates.waiting_for_shipping)


async def show_order_summary(callback: CallbackQuery, state: FSMContext, lang: str, editable: bool = False):
    """Display current order summary."""
    data = await state.get_data()
    items = data.get("order_items", [])
    exchange_rate = data.get("exchange_rate", await exchange_service.get_rate())

    if not items:
        await callback.message.edit_text("Your cart is empty.")
        return

    # Get shipping methods
    methods = await shipping_service.get_shipping_methods()

    # Build item list text
    items_text = ""
    for i, item in enumerate(items, 1):
        price_afn = round(item["price_cny"] * exchange_rate, 2) if item["price_cny"] else 0
        photo_icon = "📸" if item.get("photo_inspection") else ""
        items_text += f"{i}. {item.get('title', 'Product')} x{item.get('quantity', 1)} - ¥{item.get('price_cny', 0)} ({price_afn} AFN) {photo_icon}\n"

    summary_text = f"""
🛒 <b>Your Cart ({len(items)} items)</b>

{items_text}
💱 Rate: 1 CNY = {exchange_rate} AFN

Please select shipping method:
    """

    if editable:
        await callback.message.edit_text(
            summary_text,
            reply_markup=shipping_method_keyboard(methods, lang)
        )
    else:
        await callback.message.answer(
            summary_text,
            reply_markup=shipping_method_keyboard(methods, lang)
        )


@router.callback_query(F.data.startswith("shipping:"), OrderStates.waiting_for_shipping)
async def process_shipping(callback: CallbackQuery, state: FSMContext, lang: str = "en"):
    """Handle shipping method selection."""
    method = callback.data.split(":")[1]

    await state.update_data(shipping_method=method)

    data = await state.get_data()
    items = data.get("order_items", [])
    exchange_rate = data.get("exchange_rate", await exchange_service.get_rate())

    # Calculate full order totals
    totals = await shipping_service.calculate_order_totals(
        items=items,
        shipping_method=method,
        exchange_rate=exchange_rate,
        include_photo_inspection=any(item.get("photo_inspection") for item in items)
    )

    await state.update_data(order_totals=totals)

    # Generate order summary
    photo_line = ""
    if totals["photo_inspection_cny"] > 0:
        photo_line = f"📸 Photo Inspection: ¥{totals['photo_inspection_cny']} ({totals['photo_inspection_afn']} AFN)\n"

    summary = get_text(
        "order_summary", lang,
        order_number="PENDING",
        items_count=totals["items_count"],
        weight=totals["total_weight_kg"],
        product_cny=totals["product_cost_cny"],
        product_afn=totals["product_cost_afn"],
        method=method.upper(),
        shipping_cny=totals["shipping_cost_cny"],
        shipping_afn=totals["shipping_cost_afn"],
        fee_pct=totals["service_fee_percent"],
        service_cny=totals["service_fee_cny"],
        service_afn=totals["service_fee_afn"],
        photo_line=photo_line,
        total_cny=totals["total_cny"],
        total_afn=totals["total_afn"],
        delivery=totals["delivery_estimate"]["formatted_range"],
        rate=exchange_rate
    )

    await callback.answer()
    await callback.message.edit_text(
        summary,
        reply_markup=order_confirmation_keyboard(lang)
    )

    await state.set_state(OrderStates.waiting_for_confirmation)


@router.callback_query(F.data == "order:confirm", OrderStates.waiting_for_confirmation)
async def confirm_order(callback: CallbackQuery, state: FSMContext, lang: str = "en"):
    """Handle order confirmation."""
    try:
        data = await state.get_data()
        user = callback.from_user

        # Generate order number
        order_number = f"AFG-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"

        # Get user from DB
        db_user = await db.get_user(user.id)
        if not db_user:
            await callback.answer("User not found. Send /start first.", show_alert=True)
            await state.clear()
            return
        user_id = db_user["id"]

        totals = data.get("order_totals")
        exchange_rate = data.get("exchange_rate")
        items = data.get("order_items", [])
        shipping_method = data.get("shipping_method")

        if not totals or not items or not shipping_method:
            await callback.answer("Order data missing. Please start again.", show_alert=True)
            await state.clear()
            return

        # Create order in database
        order_id = await db.create_order(
            user_id=user_id,
            order_number=order_number,
            status="pending",
            shipping_method=shipping_method,
            total_product_cny=totals["product_cost_cny"],
            total_product_afn=totals["product_cost_afn"],
            shipping_cost_cny=totals["shipping_cost_cny"],
            shipping_cost_afn=totals["shipping_cost_afn"],
            service_fee_cny=totals["service_fee_cny"],
            service_fee_afn=totals["service_fee_afn"],
            photo_inspection_fee_cny=totals["photo_inspection_cny"],
            photo_inspection_fee_afn=totals["photo_inspection_afn"],
            total_cny=totals["total_cny"],
            total_afn=totals["total_afn"],
            exchange_rate_used=exchange_rate,
            payment_status="unpaid"
        )

        # Add order items
        for item in items:
            await db.add_order_item(
                order_id=order_id,
                product_url=item.get("url", "manual://unknown"),
                product_title=item.get("title"),
                quantity=item.get("quantity", 1),
                unit_price_cny=item.get("price_cny"),
                unit_price_afn=round(item["price_cny"] * exchange_rate, 2) if item.get("price_cny") else 0,
                total_price_cny=item.get("total_price_cny", item.get("price_cny", 0)),
                total_price_afn=round(item.get("total_price_cny", item.get("price_cny", 0)) * exchange_rate, 2),
                weight_kg=item.get("weight_kg", 0.5),
                photo_inspection=item.get("photo_inspection", False)
            )

        # Log initial status in history
        await db.execute(
            "INSERT INTO order_status_history (order_id, status) VALUES (?, ?)",
            (order_id, "pending")
        )

        # Update user stats
        await db.update_user(
            user.id,
            total_orders=db_user["total_orders"] + 1,
            total_spent=db_user["total_spent"] + totals["total_afn"]
        )

        # Check referral fulfillment
        if db_user.get("referred_by"):
            referrals = await db.fetchall(
                "SELECT * FROM referrals WHERE referred_id = ? AND status = 'pending'",
                (user_id,)
            )
            for ref in referrals:
                if totals["total_afn"] >= settings.referral_min_order_afn:
                    await db.fulfill_referral(
                        ref["id"], order_id, settings.referral_reward_afn
                    )

        await callback.answer()

        # Show payment instructions
        payment_text = get_text(
            "payment_instructions", lang,
            address=settings.office_address,
            phone=settings.office_phone,
            hours=settings.business_hours,
            order_number=order_number,
            amount_afn=totals["total_afn"]
        )

        await callback.message.edit_text(payment_text)

        # Send confirmation message
        confirm_text = get_text(
            "order_confirmed", lang,
            order_number=order_number
        )
        await callback.message.answer(confirm_text)

        # Clear state
        await state.clear()

    except Exception as e:
        logger.exception("Order confirmation failed for user %s", user.id)
        await callback.answer("❌ Failed to create order. Please try again.", show_alert=True)
        await state.clear()


@router.callback_query(F.data == "order:add_more", OrderStates.waiting_for_confirmation)
async def add_more_items(callback: CallbackQuery, state: FSMContext, lang: str = "en"):
    """Allow adding more items to the order."""
    await callback.answer()
    await callback.message.edit_text(
        "Send another product link to add more items, or use the menu below.",
        reply_markup=main_menu_keyboard(lang)
    )
    await state.set_state(OrderStates.waiting_for_link)


@router.callback_query(F.data == "menu:new_order")
async def menu_new_order(callback: CallbackQuery, state: FSMContext, lang: str = "en"):
    """Handle new order from main menu."""
    await callback.answer()
    await callback.message.edit_text(
        "🛒 Send me a product link from Taobao, Pinduoduo, or 1688.\n\n"
        "Or enter details manually in format:\n"
        "<b>Product Name | Price (CNY) | Weight (kg)</b>\n\n"
        "Example: <i>iPhone Case | 25 | 0.3</i>"
    )
    await state.set_state(OrderStates.waiting_for_link)


@router.callback_query(F.data == "order:cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext, lang: str = "en"):
    """Cancel current order flow."""
    await state.clear()
    await callback.answer(get_text("cancel", lang))
    await callback.message.edit_text(
        get_text("welcome", lang, company_name=settings.company_name),
        reply_markup=main_menu_keyboard(lang)
    )


@router.callback_query(F.data == "order:back")
async def order_back(callback: CallbackQuery, state: FSMContext, lang: str = "en"):
    """Go back to main menu."""
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        get_text("welcome", lang, company_name=settings.company_name),
        reply_markup=main_menu_keyboard(lang)
    )


# ── Manual Product Entry (when extraction fails) ──

@router.message(OrderStates.waiting_for_link)
async def manual_product_entry(message: Message, state: FSMContext, lang: str = "en"):
    """Handle manual product entry when auto-extraction fails."""
    # Expect format: Name | Price | Weight
    text = message.text.strip()
    parts = [p.strip() for p in text.split("|")]

    if len(parts) >= 2:
        try:
            price = float(parts[1].replace("¥", "").replace(",", "").strip())
            weight = float(parts[2]) if len(parts) > 2 else 0.5

            product = {
                "url": "manual://" + secrets.token_hex(8),
                "platform": "other",
                "title": parts[0],
                "price_cny": price,
                "original_price_cny": None,
                "image_url": None,
                "weight_kg": weight,
                "status": "success",
                "error": None
            }

            await state.update_data(
                current_product=product,
                order_items=[],
                exchange_rate=await exchange_service.get_rate()
            )

            await message.answer(
                get_text(
                    "product_found", lang,
                    title=product["title"],
                    price_cny=product["price_cny"],
                    price_afn=round(product["price_cny"] * (await exchange_service.get_rate()), 2),
                    platform="Manual Entry",
                    weight=product["weight_kg"]
                ),
                reply_markup=quantity_keyboard(lang)
            )

            await state.set_state(OrderStates.waiting_for_quantity)

        except ValueError:
            await message.answer(
                "❌ Invalid format. Please use: Product Name | Price | Weight(kg)\n"
                "Example: iPhone 15 Case | 25 | 0.3"
            )
    else:
        await message.answer(
            "❌ Please use format: Product Name | Price(CNY) | Weight(kg)\n"
            "Or send a valid product link."
        )
