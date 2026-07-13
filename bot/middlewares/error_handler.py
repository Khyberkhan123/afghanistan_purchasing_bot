import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)

ERROR_MESSAGE = "❌ An error occurred. Please try again or contact support."


class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception("Unhandled error in %s", type(event).__name__)
            lang = data.get("lang", "en")
            if isinstance(event, Message):
                await event.answer(ERROR_MESSAGE)
            elif isinstance(event, CallbackQuery):
                await event.answer(ERROR_MESSAGE, show_alert=True)
            return None
