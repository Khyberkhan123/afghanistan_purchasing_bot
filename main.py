"""
Afghanistan Purchasing Bot - Main Entry Point
==============================================

A professional Telegram bot for China-to-Afghanistan purchasing agent business.
Supports multi-language, product extraction, shipping calculation, and admin panel.

Usage:
    python main.py              # Start with polling (development)
    python main.py --webhook    # Start with webhook (production)
"""
import asyncio
import logging
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import settings
from bot.database import db
from bot.handlers import all_routers
from bot.middlewares import I18nMiddleware, AdminMiddleware


# ── Logging Setup ──

def setup_logging():
    """Configure structured logging for the application."""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))

    # File handler
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format))

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Reduce noise from libraries
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    return root_logger


logger = setup_logging()


# ── Bot & Dispatcher Setup ──

async def init_database():
    """Initialize database connection and schema."""
    logger.info("Initializing database...")
    Path("data").mkdir(parents=True, exist_ok=True)
    await db.connect()
    await db.init_schema()
    logger.info("Database initialized successfully")


async def shutdown_database():
    """Close database connection."""
    logger.info("Closing database connection...")
    await db.close()
    logger.info("Database connection closed")


def create_dispatcher() -> Dispatcher:
    """Create and configure the aiogram dispatcher."""
    dp = Dispatcher()

    # Register middlewares
    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())
    dp.message.middleware(AdminMiddleware())
    dp.callback_query.middleware(AdminMiddleware())

    # Register all routers
    for router in all_routers:
        dp.include_router(router)

    return dp


# ── Lifecycle Events ──

async def on_startup(bot: Bot, dispatcher: Dispatcher):
    """Actions to perform on bot startup."""
    logger.info("=" * 50)
    logger.info(f"Bot starting up: {settings.company_name}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Admin IDs: {settings.admin_ids}")
    logger.info("=" * 50)

    await init_database()

    # Set bot commands
    commands = [
        ("/start", "Start the bot and register"),
        ("/help", "Show help and instructions"),
        ("/track", "Track your order status"),
        ("/referral", "Get your referral code"),
        ("/language", "Change language"),
        ("/admin", "Admin panel (admins only)"),
    ]

    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command=cmd, description=desc) 
        for cmd, desc in commands
    ])

    logger.info("Bot commands registered")


async def on_shutdown(bot: Bot, dispatcher: Dispatcher):
    """Actions to perform on bot shutdown."""
    logger.info("Bot shutting down...")
    await shutdown_database()
    logger.info("Shutdown complete")


# ── Run Modes ──

async def run_polling():
    """Run bot in polling mode (development)."""
    logger.info("Starting in POLLING mode")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = create_dispatcher()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def run_webhook():
    """Run bot in webhook mode (production)."""
    logger.info("Starting in WEBHOOK mode")

    if not settings.webhook_url:
        raise ValueError("WEBHOOK_URL must be set for webhook mode")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = create_dispatcher()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Create aiohttp app
    app = web.Application()

    # Webhook handler
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret
    )
    webhook_handler.register(app, path="/webhook")

    # Health check endpoint
    async def health_check(request):
        return web.json_response({
            "status": "ok",
            "bot": settings.bot_username,
            "environment": settings.environment
        })

    app.router.add_get("/health", health_check)

    # Setup startup/shutdown
    setup_application(app, dp, bot=bot)

    # Set webhook
    await bot.set_webhook(
        url=f"{settings.webhook_url}/webhook",
        secret_token=settings.webhook_secret,
        drop_pending_updates=True
    )

    logger.info(f"Webhook set to: {settings.webhook_url}/webhook")

    # Run server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    logger.info("Server started on port 8080")

    # Keep running
    while True:
        await asyncio.sleep(3600)


# ── Main ──

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Afghanistan Purchasing Bot")
    parser.add_argument(
        "--webhook", 
        action="store_true", 
        help="Run in webhook mode (production)"
    )
    parser.add_argument(
        "--polling",
        action="store_true",
        help="Run in polling mode (development)"
    )
    args = parser.parse_args()

    # Default to polling if no mode specified
    # Webhook only if --webhook flag OR (production AND webhook_url is configured)
    use_webhook = args.webhook or (settings.is_production and settings.webhook_url and not args.polling)

    try:
        if use_webhook:
            asyncio.run(run_webhook())
        else:
            asyncio.run(run_polling())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
