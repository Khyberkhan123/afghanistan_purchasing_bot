"""
Internationalization middleware.
Attaches user's language to the handler context.
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from bot.database import db


class I18nMiddleware(BaseMiddleware):
    """Middleware to inject user's language into handler data."""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")

        if user:
            # Get user language from database
            db_user = await db.get_user(user.id)
            lang = db_user["language"] if db_user else "en"
            data["lang"] = lang
        else:
            data["lang"] = "en"

        return await handler(event, data)
