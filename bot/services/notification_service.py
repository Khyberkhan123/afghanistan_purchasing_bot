"""
Notification service for order status updates.
Sends tracking notifications to customers when order status changes.
"""
from typing import Optional
from datetime import datetime
from aiogram import Bot
from config import settings
from bot.database import db
from bot.utils.i18n import get_text


class NotificationService:
    """Service for sending order status notifications to customers."""

    STATUS_MESSAGES = {
        "purchased": {
            "emoji": "🛒",
            "title_en": "Items Purchased!",
            "title_fa": "اقلام خریداری شد!",
            "title_ps": "توکي پیرودل شول!",
            "title_zh": "商品已采购！",
            "message_en": "Your items have been purchased in China and are being prepared for shipment.",
            "message_fa": "اقلام شما در چین خریداری شده و در حال آماده‌سازی برای ارسال هستند.",
            "message_ps": "ستاسو توکي په چین کې پیرودل شوي او د لېږد لپاره چمتو کیږي.",
            "message_zh": "您的商品已在中国采购，正在准备发货。",
        },
        "shipped": {
            "emoji": "📦",
            "title_en": "Order Shipped!",
            "title_fa": "سفارش ارسال شد!",
            "title_ps": "سفارش ولېږل شو!",
            "title_zh": "订单已发货！",
            "message_en": "Your order has been shipped from China! Track its journey to Afghanistan.",
            "message_fa": "سفارش شما از چین ارسال شد! مسیر آن تا افغانستان را دنبال کنید.",
            "message_ps": "ستاسو سفارش له چین څخه ولېږل شو! د افغانستان پورې د هغه سفر تعقیب کړئ.",
            "message_zh": "您的订单已从中国发货！追踪它到阿富汗的旅程。",
        },
        "in_transit": {
            "emoji": "🚚",
            "title_en": "In Transit",
            "title_fa": "در حال حمل",
            "title_ps": "په لاره کې",
            "title_zh": "运输中",
            "message_en": "Your order is currently in transit. It's on its way to Afghanistan!",
            "message_fa": "سفارش شما در حال حمل است. در راه افغانستان است!",
            "message_ps": "ستاسو سفارش اوس په لاره کې دی. هغه افغانستان ته روان دی!",
            "message_zh": "您的订单正在运输中。正在运往阿富汗！",
        },
        "customs": {
            "emoji": "🛃",
            "title_en": "At Customs",
            "title_fa": "در گمرک",
            "title_ps": "په ګمرک کې",
            "title_zh": "海关清关中",
            "message_en": "Your order is currently at customs for clearance. This usually takes 1-3 days.",
            "message_fa": "سفارش شما در حال حاضر در گمرک برای ترخیص است. این معمولاً 1-3 روز طول می‌کشد.",
            "message_ps": "ستاسو سفارش اوس د پاکولو لپاره په ګمرک کې دی. دا معمولاً 1-3 ورځې وخت نیسي.",
            "message_zh": "您的订单正在海关清关。通常需要1-3天。",
        },
        "delivered": {
            "emoji": "📍",
            "title_en": "Delivered to Office!",
            "title_fa": "به دفتر تحویل داده شد!",
            "title_ps": "دفتر ته تحویل شو!",
            "title_zh": "已送达办公室！",
            "message_en": "Great news! Your order has arrived at our office. Please visit to collect it.",
            "message_fa": "خبر خوب! سفارش شما به دفتر ما رسیده است. لطفاً برای دریافت آن مراجعه کنید.",
            "message_ps": "ښه خبر! ستاسو سفارش زموږ دفتر ته رسیدلی دی. مهرباني وکړئ د ترلاسه کولو لپاره ورشئ.",
            "message_zh": "好消息！您的订单已到达我们的办公室。请来领取。",
        },
        "completed": {
            "emoji": "✅",
            "title_en": "Order Completed!",
            "title_fa": "سفارش تکمیل شد!",
            "title_ps": "سفارش بشپړ شو!",
            "title_zh": "订单已完成！",
            "message_en": "Thank you for your business! Your order is complete. We hope to serve you again soon.",
            "message_fa": "از اعتماد شما سپاسگزاریم! سفارش شما تکمیل شد. امیدواریم دوباره خدمتگزار شما باشیم.",
            "message_ps": "ستاسو د اعتماد څخه مننه! ستاسو سفارش بشپړ شو. موږ هیله لرو چې ژر بیا تاسو ته خدمت وکړو.",
            "message_zh": "感谢您的信任！您的订单已完成。期待再次为您服务。",
        },
    }

    async def send_status_notification(self, bot: Bot, order_id: int, status: str, 
                                        location: str = None, notes: str = None):
        """
        Send status update notification to customer.

        Args:
            bot: Aiogram Bot instance
            order_id: Database order ID
            status: New order status
            location: Optional location info
            notes: Optional notes
        """
        # Get order and user
        order = await db.get_order(order_id)
        if not order:
            return

        user = await db.fetchone("SELECT * FROM users WHERE id = ?", (order["user_id"],))
        if not user:
            return

        lang = user.get("language", "en")
        order_number = order["order_number"]

        # Get status message template
        template = self.STATUS_MESSAGES.get(status)
        if not template:
            # Generic notification
            template = {
                "emoji": "📦",
                f"title_{lang}": f"Status Update: {status}",
                f"message_{lang}": f"Your order status has been updated to: {status}",
            }

        title = template.get(f"title_{lang}", template.get("title_en", "Status Update"))
        message = template.get(f"message_{lang}", template.get("message_en", ""))
        emoji = template["emoji"]

        # Build notification text
        notification_text = f"""
{emoji} <b>{title}</b>

📋 <b>Order:</b> #{order_number}
📊 <b>Status:</b> {status.upper()}
{message}
        """

        if location:
            notification_text += f"\n📍 <b>Location:</b> {location}"
        if notes:
            notification_text += f"\n📝 <b>Notes:</b> {notes}"

        notification_text += f"\n\n💰 <b>Total:</b> {order['total_afn']} AFN"

        # Send notification
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text=notification_text
            )

            # Mark as notified in history
            await db.execute(
                "UPDATE order_status_history SET notified = 1 WHERE order_id = ? AND status = ? ORDER BY created_at DESC LIMIT 1",
                (order_id, status)
            )

        except Exception as e:
            print(f"Failed to notify user {user['telegram_id']}: {e}")

    async def send_payment_reminder(self, bot: Bot, order_id: int):
        """Send payment reminder for pending orders."""
        order = await db.get_order(order_id)
        if not order or order["payment_status"] != "unpaid":
            return

        user = await db.fetchone("SELECT * FROM users WHERE id = ?", (order["user_id"],))
        if not user:
            return

        lang = user.get("language", "en")

        reminder_text = get_text(
            "payment_instructions", lang,
            address=settings.office_address,
            phone=settings.office_phone,
            hours=settings.business_hours,
            order_number=order["order_number"],
            amount_afn=order["total_afn"]
        )

        try:
            await bot.send_message(user["telegram_id"], reminder_text)
        except Exception as e:
            print(f"Failed to send payment reminder: {e}")

    async def send_photo_inspection(self, bot: Bot, order_item_id: int, photo_file_id: str, notes: str = None):
        """Send photo inspection results to customer."""
        # Get order item and user
        item = await db.fetchone(
            "SELECT oi.*, o.user_id, u.telegram_id, u.language FROM order_items oi "
            "JOIN orders o ON oi.order_id = o.id JOIN users u ON o.user_id = u.id "
            "WHERE oi.id = ?",
            (order_item_id,)
        )

        if not item:
            return

        lang = item.get("language", "en")

        photo_text = f"""
📸 <b>Photo Inspection Results</b>

🛒 <b>Product:</b> {item.get('product_title', 'Product')}
{"✅ Passed" if not notes else "⚠️ " + notes}

Your item has been inspected before shipping.
        """

        try:
            await bot.send_photo(
                chat_id=item["telegram_id"],
                photo=photo_file_id,
                caption=photo_text
            )
        except Exception as e:
            print(f"Failed to send photo inspection: {e}")


# Singleton instance
notification_service = NotificationService()
