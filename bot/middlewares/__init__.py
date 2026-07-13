"""Middlewares package."""
from bot.middlewares.i18n_middleware import I18nMiddleware
from bot.middlewares.admin_middleware import AdminMiddleware
from bot.middlewares.error_handler import ErrorHandlerMiddleware

__all__ = ["I18nMiddleware", "AdminMiddleware", "ErrorHandlerMiddleware"]
