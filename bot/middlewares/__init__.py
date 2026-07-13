"""Middlewares package."""
from bot.middlewares.i18n_middleware import I18nMiddleware
from bot.middlewares.admin_middleware import AdminMiddleware

__all__ = ["I18nMiddleware", "AdminMiddleware"]
