#!/usr/bin/env python3
"""
Telegram Bot for YouTube and Instagram Downloads
Supports multiple Userbot sessions with load balancing
"""

import asyncio
import logging
from pathlib import Path

from config import BOT_TOKEN, API_ID, API_HASH
from handlers.bot_handlers import setup_bot_handlers
from handlers.admin_handlers import setup_admin_handlers
from services.session_manager import SessionManager
from utils.database import Database
from utils.logging_config import BotLogger

# Setup logging
bot_logger = BotLogger()
logger = logging.getLogger(__name__)

async def main():
    """Main entry point"""
    try:
        logger.info("🚀 Starting Telegram Bot with Userbot support...")
        
        # Network testing removed for better performance
        
        # Initialize database
        database = Database()
        await database.initialize()
        
        # Initialize session manager
        session_manager = SessionManager()
        await session_manager.initialize()
        
        # Setup bot handlers
        bot = await setup_bot_handlers(session_manager)
        
        # Setup admin handlers
        admin_handlers = setup_admin_handlers(bot, session_manager, database)
        logger.info("✅ Admin panel initialized")
        
        logger.info("✅ Bot started successfully!")
        logger.info(f"📊 Active sessions: {len(session_manager.active_sessions)}")
        
        # Run bot
        await bot.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
    finally:
        logger.info("🛑 Bot shutting down...")

if __name__ == "__main__":
    asyncio.run(main())