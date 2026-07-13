"""
Admin authorization middleware.
Checks if user is an admin before allowing admin commands.
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from config import settings
from bot.database import db


class AdminMiddleware(BaseMiddleware):
    """Middleware to check admin privileges."""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")

        if user:
            # Check if user is in admin list
            is_admin = user.id in settings.admin_ids

            if not is_admin:
                # Also check database role
                db_user = await db.get_user(user.id)
                is_admin = db_user and db_user.get("role") in ("admin", "super_admin")

            data["is_admin"] = is_admin
        else:
            data["is_admin"] = False

        return await handler(event, data)
