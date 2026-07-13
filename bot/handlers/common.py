"""
Common handlers for the bot.
Start, help, language selection, and main menu.
"""
import secrets
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from config import settings
from bot.database import db
from bot.utils.i18n import get_text, get_supported_languages
from bot.utils.keyboards import language_selection_keyboard, main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, lang: str = "en"):
    """Handle /start command - register new user or welcome existing."""
    user = message.from_user

    # Check if user exists
    db_user = await db.get_user(user.id)

    if not db_user:
        # Check for referral code in deep link
        args = message.text.split() if message.text else []
        referred_by = None

        if len(args) > 1:
            # Format: /start REFCODE
            ref_code = args[1]
            referrer = await db.get_user_by_referral(ref_code)
            if referrer:
                referred_by = referrer["id"]

        # Create new user
        await db.create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language=lang,
            referred_by=referred_by
        )

        # If referred, create referral record
        if referred_by:
            new_user = await db.get_user(user.id)
            await db.create_referral(referred_by, new_user["id"])

        # Ask for language selection
        await message.answer(
            get_text("select_language", lang),
            reply_markup=language_selection_keyboard()
        )
    else:
        # Existing user - show welcome with main menu
        lang = db_user.get("language", "en")
        await message.answer(
            get_text("welcome", lang, company_name=settings.company_name),
            reply_markup=main_menu_keyboard(lang)
        )


@router.callback_query(F.data.startswith("lang:"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext):
    """Handle language selection callback."""
    lang = callback.data.split(":")[1]
    user = callback.from_user

    # Update user language
    await db.update_user(user.id, language=lang)

    await callback.answer()
    await callback.message.edit_text(
        get_text("language_selected", lang)
    )

    # Show welcome message with main menu
    await callback.message.answer(
        get_text("welcome", lang, company_name=settings.company_name),
        reply_markup=main_menu_keyboard(lang)
    )


@router.message(Command("language"))
async def cmd_language(message: Message, lang: str = "en"):
    """Handle /language command."""
    await message.answer(
        get_text("select_language", lang),
        reply_markup=language_selection_keyboard()
    )


@router.callback_query(F.data == "menu:language")
async def menu_language(callback: CallbackQuery, lang: str = "en"):
    """Handle language menu button."""
    await callback.answer()
    await callback.message.edit_text(
        get_text("select_language", lang),
        reply_markup=language_selection_keyboard()
    )


@router.callback_query(F.data == "menu:main")
async def menu_main(callback: CallbackQuery, lang: str = "en"):
    """Return to main menu."""
    await callback.answer()
    await callback.message.edit_text(
        get_text("welcome", lang, company_name=settings.company_name),
        reply_markup=main_menu_keyboard(lang)
    )


@router.message(Command("help"))
async def cmd_help(message: Message, lang: str = "en"):
    """Handle /help command."""
    rate = await db.get_latest_rate()

    help_text = f"""📖 <b>{settings.company_name}</b>

🛒 <b>How to Order:</b>
1. Send a product link from Taobao, Pinduoduo, or 1688
2. Review extracted details
3. Set quantity
4. Choose photo inspection (optional)
5. Select shipping method
6. Review order summary
7. Visit our office to pay

📦 <b>Track Orders:</b>
Use /track &lt;order_number&gt;

🎁 <b>Referral Program:</b>
Use /referral to get your code

📞 <b>Support:</b>
{settings.office_phone}
{settings.office_address}

💱 <b>Current Rate:</b> 1 CNY = {rate} AFN"""

    await message.answer(help_text)


@router.callback_query(F.data == "menu:support")
async def menu_support(callback: CallbackQuery, lang: str = "en"):
    """Handle support menu button."""
    await callback.answer()

    support_text = f"""📞 {get_text("error_generic", lang).split(chr(10))[0]}

🏢 <b>{settings.company_name}</b>
📍 {settings.office_address}
📞 {settings.office_phone}
🕐 {settings.business_hours}

Send us a message anytime!"""

    await callback.message.edit_text(support_text)
