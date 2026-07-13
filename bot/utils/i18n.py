"""
Internationalization (i18n) module.
Supports English, Dari/Farsi, Pashto, and Chinese.
"""
from typing import Dict, Optional
from enum import Enum


class Language(str, Enum):
    """Supported languages."""
    ENGLISH = "en"
    FARSI = "fa"      # Dari/Persian
    PASHTO = "ps"
    CHINESE = "zh"


# Translation dictionary
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # ── Common ──
    "welcome": {
        "en": "Welcome to {company_name}!\n\nI am your purchasing assistant for buying products from China (Taobao, Pinduoduo, 1688) and delivering them to Afghanistan.\n\nSend me a product link to get started!",
        "fa": "به {company_name} خوش آمدید!\n\nمن دستیار خرید شما برای خرید محصولات از چین (Taobao, Pinduoduo, 1688) و تحویل آنها به افغانستان هستم.\n\nبرای شروع، لینک محصول را برای من ارسال کنید!",
        "ps": "{company_name} ته ښه راغلاست!\n\nزه ستاسو د چین (Taobao, Pinduoduo, 1688) څخه د توکو د پیرودلو او هغه افغانستان ته د لېږدولو مرستیال یم.\n\nد پیل لپاره زما ته د محصول لینک ولېږئ!",
        "zh": "欢迎使用{company_name}！\n\n我是您的中国采购助手，帮您从淘宝、拼多多、1688购买商品并运送到阿富汗。\n\n发送商品链接即可开始！",
    },
    "language_selected": {
        "en": "Language set to English.",
        "fa": "زبان به فارسی تنظیم شد.",
        "ps": "ژبه په پښتو وټاکل شوه.",
        "zh": "语言已设置为中文。",
    },
    "select_language": {
        "en": "Please select your preferred language:",
        "fa": "لطفاً زبان مورد نظر خود را انتخاب کنید:",
        "ps": "مهرباني وکړئ خپله غوره ژبه وټاکئ:",
        "zh": "请选择您的首选语言：",
    },

    # ── Product ──
    "product_found": {
        "en": "📦 Product Found\n\n🛒 {title}\n💰 Price: ¥{price_cny} ({price_afn} AFN)\n🏪 Platform: {platform}\n⚖️ Est. Weight: {weight}kg",
        "fa": "📦 محصول یافت شد\n\n🛒 {title}\n💰 قیمت: ¥{price_cny} ({price_afn} افغانی)\n🏪 پلتفرم: {platform}\n⚖️ وزن تخمینی: {weight} کیلوگرم",
        "ps": "📦 محصول وموندل شو\n\n🛒 {title}\n💰 بیه: ¥{price_cny} ({price_afn} افغانی)\n🏪 پلیټ فارم: {platform}\n⚖️ اټکل شوی وزن: {weight} کیلو",
        "zh": "📦 找到商品\n\n🛒 {title}\n💰 价格: ¥{price_cny} ({price_afn} 阿富汗尼)\n🏪 平台: {platform}\n⚖️ 预估重量: {weight}公斤",
    },
    "product_not_found": {
        "en": "⚠️ Could not extract product details from this link.\n\nYou can still add it manually. Please send:\n1. Product name\n2. Price in CNY (¥)\n3. Estimated weight in kg",
        "fa": "⚠️ نتوانستیم جزئیات محصول را از این لینک استخراج کنیم.\n\nهمچنان می‌توانید آن را به صورت دستی اضافه کنید. لطفاً ارسال کنید:\n1. نام محصول\n2. قیمت به یوان چین (¥)\n3. وزن تخمینی به کیلوگرم",
        "ps": "⚠️ له دې لینک څخه د محصول توضیحات استخراج نشول.\n\nتاسو لا هم کولی شئ دا په لاسي ډول اضافه کړئ. مهرباني وکړئ ولېږئ:\n1. د محصول نوم\n2. بیه په چینایي یوان (¥)\n3. اټکل شوی وزن په کیلو",
        "zh": "⚠️ 无法从此链接提取商品详情。\n\n您仍可手动添加。请发送：\n1. 商品名称\n2. 人民币价格 (¥)\n3. 预估重量（公斤）",
    },
    "product_partial": {
        "en": "✅ Product Found!\n\n📦 {title}\n🏪 Platform: {platform}\n⚖️ Est. Weight: {weight}kg\n\n⚠️ Could not auto-detect the price.\n\n<b>Please enter the product price in CNY (¥) below:</b>\nExample: 25.50",
        "fa": "✅ محصول یافت شد!\n\n📦 {title}\n🏪 پلتفرم: {platform}\n⚖️ وزن تخمینی: {weight} کیلوگرم\n\n⚠️ قیمت به صورت خودکار تشخیص داده نشد.\n\n<b>لطفاً قیمت محصول را به یوان چین (¥) وارد کنید:</b>\nمثال: 25.50",
        "ps": "✅ محصول وموندل شو!\n\n📦 {title}\n🏪 پلیټ فارم: {platform}\n⚖️ اټکل شوی وزن: {weight} کیلو\n\n⚠️ بیه په اتوماتيک ډول کشف نشوه.\n\n<b>مهرباني وکړئ د محصول بیه په چینایي یوان (¥) کې دننه کړئ:</b>\nبېلګه: 25.50",
        "zh": "✅ 找到商品！\n\n📦 {title}\n🏪 平台: {platform}\n⚖️ 预估重量: {weight}公斤\n\n⚠️ 无法自动检测价格。\n\n<b>请输入商品价格（人民币 ¥）：</b>\n例如：25.50",
    },
    "invalid_price": {
        "en": "❌ Invalid price. Please enter a number, e.g. 25.50",
        "fa": "❌ قیمت نامعتبر. لطفاً یک عدد وارد کنید، مثال: 25.50",
        "ps": "❌ ناسمه بیه. مهرباني وکړئ یوه شمېره دننه کړئ، بېلګه: 25.50",
        "zh": "❌ 价格无效。请输入数字，例如：25.50",
    },
    "add_to_cart": {
        "en": "➕ Add to Order",
        "fa": "➕ افزودن به سفارش",
        "ps": "➕ سفارش ته اضافه کړئ",
        "zh": "➕ 加入订单",
    },
    "quantity_prompt": {
        "en": "How many units would you like to order?",
        "fa": "چند واحد می‌خواهید سفارش دهید؟",
        "ps": "تاسو څو واحدونه سفارش کول غواړئ؟",
        "zh": "您想订购多少件？",
    },
    "photo_inspection_prompt": {
        "en": "📸 Would you like photo inspection for this item?\n\nWe will take photos of the actual product before shipping for ¥{fee} ({fee_afn} AFN).",
        "fa": "📸 آیا می‌خواهید برای این کالا بازرسی عکسی داشته باشید؟\n\nما قبل از ارسال عکس‌های واقعی محصول را به مبلغ ¥{fee} ({fee_afn} افغانی) خواهیم گرفت.",
        "ps": "📸 ایا تاسو غواړئ د دې توکي لپاره د عکسونو معاینه وکړئ؟\n\nموږ به د لېږد مخه د حقیقي محصول عکسونه د ¥{fee} ({fee_afn} افغانی) په بدل کې واخلو.",
        "zh": "📸 您需要此商品的照片验货服务吗？\n\n我们将在发货前拍摄实际商品照片，费用为 ¥{fee} ({fee_afn} 阿富汗尼)。",
    },

    # ── Order Summary ──
    "order_summary": {
        "en": "📋 ORDER SUMMARY\n\nOrder #{order_number}\nItems: {items_count}\nTotal Weight: {weight}kg\n\n💵 COST BREAKDOWN:\nProducts: ¥{product_cny} ({product_afn} AFN)\nShipping ({method}): ¥{shipping_cny} ({shipping_afn} AFN)\nService Fee ({fee_pct}%): ¥{service_cny} ({service_afn} AFN)\n{photo_line}\n━━━━━━━━━━━━━━\n💰 TOTAL: ¥{total_cny}\n💰 TOTAL: {total_afn} AFN\n\n📅 Est. Delivery: {delivery}\n💱 Rate: 1 CNY = {rate} AFN",
        "fa": "📋 خلاصه سفارش\n\nسفارش #{order_number}\nاقلام: {items_count}\nوزن کل: {weight} کیلوگرم\n\n💵 جزئیات هزینه:\nمحصولات: ¥{product_cny} ({product_afn} افغانی)\nحمل و نقل ({method}): ¥{shipping_cny} ({shipping_afn} افغانی)\nهزینه خدمات ({fee_pct}%): ¥{service_cny} ({service_afn} افغانی)\n{photo_line}\n━━━━━━━━━━━━━━\n💰 کل: ¥{total_cny}\n💰 کل: {total_afn} افغانی\n\n📅 تحویل تخمینی: {delivery}\n💱 نرخ: 1 یوان = {rate} افغانی",
        "ps": "📋 د سفارش لنډیز\n\nسفارش #{order_number}\nتوکي: {items_count}\nټول وزن: {weight} کیلو\n\n💵 د لګښت تفصیل:\nمحصولات: ¥{product_cny} ({product_afn} افغانی)\nلېږد ({method}): ¥{shipping_cny} ({shipping_afn} افغانی)\nد خدماتو فیس ({fee_pct}%): ¥{service_cny} ({service_afn} افغانی)\n{photo_line}\n━━━━━━━━━━━━━━\n💰 ټول: ¥{total_cny}\n💰 ټول: {total_afn} افغانی\n\n📅 اټکل شوی تحویل: {delivery}\n💱 نرخ: 1 یوان = {rate} افغانی",
        "zh": "📋 订单摘要\n\n订单号 #{order_number}\n商品数: {items_count}\n总重量: {weight}公斤\n\n💵 费用明细:\n商品: ¥{product_cny} ({product_afn} 阿富汗尼)\n运费 ({method}): ¥{shipping_cny} ({shipping_afn} 阿富汗尼)\n服务费 ({fee_pct}%): ¥{service_cny} ({service_afn} 阿富汗尼)\n{photo_line}\n━━━━━━━━━━━━━━\n💰 总计: ¥{total_cny}\n💰 总计: {total_afn} 阿富汗尼\n\n📅 预计送达: {delivery}\n💱 汇率: 1 人民币 = {rate} 阿富汗尼",
    },

    # ── Payment ──
    "payment_instructions": {
        "en": "💳 PAYMENT INSTRUCTIONS\n\nPlease visit our office to complete payment:\n\n📍 {address}\n📞 {phone}\n🕐 {hours}\n\nOrder: #{order_number}\nAmount Due: {amount_afn} AFN\n\nBring this order number with you. Payment accepted in cash or bank transfer at our office.",
        "fa": "💳 دستورالعمل‌های پرداخت\n\nلطفاً برای تکمیل پرداخت به دفتر ما مراجعه کنید:\n\n📍 {address}\n📞 {phone}\n🕐 {hours}\n\nسفارش: #{order_number}\nمبلغ قابل پرداخت: {amount_afn} افغانی\n\nاین شماره سفارش را با خود بیاورید. پرداخت نقدی یا انتقال بانکی در دفتر ما پذیرفته می‌شود.",
        "ps": "💳 د تادیې لارښوونې\n\nمهرباني وکړئ د تادیې بشپړولو لپاره زموږ د دفتر ته ورشئ:\n\n📍 {address}\n📞 {phone}\n🕐 {hours}\n\nسفارش: #{order_number}\nد تادیې اندازه: {amount_afn} افغانی\n\nدا د سفارش شمیره له ځان سره راوړئ. نقدي تادیه یا بانکي انتقال زموږ د دفتر کې منل کیږي.",
        "zh": "💳 付款说明\n\n请到我们的办公室完成付款：\n\n📍 {address}\n📞 {phone}\n🕐 {hours}\n\n订单号: #{order_number}\n应付金额: {amount_afn} 阿富汗尼\n\n请携带此订单号。我们办公室接受现金或银行转账。",
    },
    "order_confirmed": {
        "en": "✅ Order #{order_number} Confirmed!\n\nWe will purchase your items and notify you when they ship.\nTrack your order anytime with /track {order_number}",
        "fa": "✅ سفارش #{order_number} تأیید شد!\n\nما اقلام شما را خریداری خواهیم کرد و هنگام ارسال به شما اطلاع خواهیم داد.\nبا /track {order_number} سفارش خود را دنبال کنید",
        "ps": "✅ سفارش #{order_number} تایید شو!\n\nموږ به ستاسو توکي پیرود کوو او کله چې لېږل شي ستاسو ته خبر درکوو.\nپه هر وخت کې د /track {order_number} سره خپل سفارش تعقیب کړئ",
        "zh": "✅ 订单 #{order_number} 已确认！\n\n我们将采购您的商品，发货时通知您。\n随时使用 /track {order_number} 追踪订单",
    },

    # ── Tracking ──
    "tracking_header": {
        "en": "📦 Order Tracking: #{order_number}",
        "fa": "📦 پیگیری سفارش: #{order_number}",
        "ps": "📦 د سفارش تعقیب: #{order_number}",
        "zh": "📦 订单追踪: #{order_number}",
    },
    "status_update": {
        "en": "🔄 Status Update\n\nOrder #{order_number}\nNew Status: {status}\n{location}\n{notes}\n\nUpdated: {time}",
        "fa": "🔄 به‌روزرسانی وضعیت\n\nسفارش #{order_number}\nوضعیت جدید: {status}\n{location}\n{notes}\n\nبه‌روزرسانی: {time}",
        "ps": "🔄 د حالت تازه کول\n\nسفارش #{order_number}\nنوی حالت: {status}\n{location}\n{notes}\n\nتازه شوی: {time}",
        "zh": "🔄 状态更新\n\n订单 #{order_number}\n新状态: {status}\n{location}\n{notes}\n\n更新时间: {time}",
    },

    # ── Referral ──
    "referral_info": {
        "en": "🎁 Referral Program\n\nYour referral code: `{code}`\n\nShare this code with friends! When they place their first order over {min} AFN, you earn {reward} AFN credit.\n\nReferrals: {count}\nTotal Earnings: {earnings} AFN",
        "fa": "🎁 برنامه معرفی\n\nکد معرفی شما: `{code}`\n\nاین کد را با دوستان خود به اشتراک بگذارید! وقتی آنها اولین سفارش خود را بالای {min} افغانی ثبت کنند، شما {reward} افغانی اعتبار دریافت می‌کنید.\n\nمعرفی‌ها: {count}\nدرآمد کل: {earnings} افغانی",
        "ps": "🎁 د معرفي پروګرام\n\nستاسو د معرفي کوډ: `{code}`\n\nدا کوډ له ملګرو سره شریک کړئ! کله چې دوی خپل لومړی سفارش چې له {min} افغانی زیات وي ثبت کړي، تاسو {reward} افغانی کریډیټ ترلاسه کوئ.\n\nمعرفي شوي: {count}\nټولې ګټې: {earnings} افغانی",
        "zh": "🎁 推荐计划\n\n您的推荐码: `{code}`\n\n与朋友分享此码！当他们完成首单超过 {min} 阿富汗尼时，您可获得 {reward} 阿富汗尼奖励。\n\n推荐人数: {count}\n总收益: {earnings} 阿富汗尼",
    },
    "referral_success": {
        "en": "🎉 You were referred by {referrer}!\n\nAfter your first order is completed, they will receive {reward} AFN credit.",
        "fa": "🎉 شما توسط {referrer} معرفی شدید!\n\nپس از تکمیل اولین سفارش شما، آنها {reward} افغانی اعتبار دریافت خواهند کرد.",
        "ps": "🎉 تاسو د {referrer} لخوا معرفي شوئ!\n\nد ستاسو د لومړي سفارش بشپړیدو وروسته، هغوی به {reward} افغانی کریډیټ ترلاسه کړي.",
        "zh": "🎉 您被 {referrer} 推荐！\n\n您的首单完成后，他们将获得 {reward} 阿富汗尼奖励。",
    },

    # ── Admin ──
    "admin_panel": {
        "en": "🔧 Admin Panel\n\nSelect an action:",
        "fa": "🔧 پنل مدیریت\n\nیک عمل را انتخاب کنید:",
        "ps": "🔧 د ادمین پانل\n\nیو عمل وټاکئ:",
        "zh": "🔧 管理面板\n\n选择操作：",
    },
    "stats_overview": {
        "en": "📊 Business Statistics\n\n👥 Total Users: {users}\n📦 Total Orders: {orders}\n⏳ Pending Orders: {pending}\n💰 Total Revenue: {revenue} AFN",
        "fa": "📊 آمار کسب‌وکار\n\n👥 کل کاربران: {users}\n📦 کل سفارش‌ها: {orders}\n⏳ سفارش‌های در انتظار: {pending}\n💰 درآمد کل: {revenue} افغانی",
        "ps": "📊 د سوداګرۍ احصایې\n\n👥 ټول کاروونکي: {users}\n📦 ټول سفارشونه: {orders}\n⏳ د انتظار سفارشونه: {pending}\n💰 ټولې ګټې: {revenue} افغانی",
        "zh": "📊 业务统计\n\n👥 总用户: {users}\n📦 总订单: {orders}\n⏳ 待处理订单: {pending}\n💰 总收入: {revenue} 阿富汗尼",
    },

    # ── Errors ──
    "error_generic": {
        "en": "❌ An error occurred. Please try again or contact support.",
        "fa": "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
        "ps": "❌ یوه تیروتنه رامنځته شوه. مهرباني وکړئ بیا هڅه وکړئ یا د ملاتړ سره اړیکه ونیسئ.",
        "zh": "❌ 发生错误。请重试或联系客服。",
    },
    "not_authorized": {
        "en": "⛔ You are not authorized to use this feature.",
        "fa": "⛔ شما مجاز به استفاده از این ویژگی نیستید.",
        "ps": "⛔ تاسو د دې ځانګړتیا د کارولو اجازه نلرئ.",
        "zh": "⛔ 您无权使用此功能。",
    },

    "error_database": {
        "en": "❌ Database error. Please try again later.",
        "fa": "❌ خطای پایگاه داده. لطفاً بعداً دوباره تلاش کنید.",
        "ps": "❌ د ډیټابیس تېروتنه. مهرباني وکړئ وروسته بیا هڅه وکړئ.",
        "zh": "❌ 数据库错误。请稍后重试。",
    },
    "error_order_not_found": {
        "en": "❌ Order not found. Please check the order number.",
        "fa": "❌ سفارش یافت نشد. لطفاً شماره سفارش را بررسی کنید.",
        "ps": "❌ امر ونه موندل شو. مهرباني وکړئ د امر شمیره وګورئ.",
        "zh": "❌ 未找到订单。请检查订单号。",
    },
    "order_tracking_prompt": {
        "en": "📦 Send /track &lt;order_number&gt; to check your order status.\n\nExample: /track AFG-20240713-ABC123",
        "fa": "📦 برای بررسی وضعیت سفارش خود /track &lt;شماره_سفارش&gt; را ارسال کنید.\n\nمثال: /track AFG-20240713-ABC123",
        "ps": "📦 د خپل امر حالت معلومولو لپاره /track &lt;د_امر_شمیره&gt; ولېږئ.\n\nبېلګه: /track AFG-20240713-ABC123",
        "zh": "📦 发送 /track &lt;订单号&gt; 来查看订单状态。\n\n示例: /track AFG-20240713-ABC123",
    },

    # ── Navigation ──
    "back": {
        "en": "◀️ Back",
        "fa": "◀️ بازگشت",
        "ps": "◀️ شاته",
        "zh": "◀️ 返回",
    },
    "cancel": {
        "en": "❌ Cancel",
        "fa": "❌ لغو",
        "ps": "❌ لغوه",
        "zh": "❌ 取消",
    },
    "confirm": {
        "en": "✅ Confirm",
        "fa": "✅ تأیید",
        "ps": "✅ تایید",
        "zh": "✅ 确认",
    },
    "yes": {
        "en": "✅ Yes",
        "fa": "✅ بله",
        "ps": "✅ هو",
        "zh": "✅ 是",
    },
    "no": {
        "en": "❌ No",
        "fa": "❌ خیر",
        "ps": "❌ نه",
        "zh": "❌ 否",
    },
}


def get_text(key: str, lang: str = "en", **kwargs) -> str:
    """
    Get translated text by key.

    Args:
        key: Translation key
        lang: Language code (en/fa/ps/zh)
        **kwargs: Format arguments for the translation string

    Returns:
        Translated and formatted string
    """
    lang = lang.lower()[:2]  # Normalize language code

    if key not in TRANSLATIONS:
        return f"[Missing: {key}]"

    translations = TRANSLATIONS[key]
    text = translations.get(lang, translations.get("en", f"[Missing: {key}]"))

    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            # If formatting fails, return raw text
            pass

    return text


def get_supported_languages() -> Dict[str, str]:
    """Get dictionary of supported language codes and names."""
    return {
        "en": "🇬🇧 English",
        "fa": "🇦🇫 فارسی (Dari)",
        "ps": "🇦🇫 پښتو (Pashto)",
        "zh": "🇨🇳 中文 (Chinese)",
    }
