"""Handlers package."""
from aiogram import Router

from bot.handlers.common import router as common_router
from bot.handlers.orders import router as orders_router
from bot.handlers.tracking import router as tracking_router
from bot.handlers.admin import router as admin_router

# Combine all routers
all_routers = [
    common_router,
    orders_router,
    tracking_router,
    admin_router,
]

__all__ = ["all_routers"]
