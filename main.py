import logging
import os
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from bot.config import TOKEN, DATABASE_URL
from bot.database import DatabaseManager
from bot.handlers import common, user, admin

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    if not TOKEN:
        logger.error("❌ BOT_TOKEN environment variable is required")
        return
        
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL environment variable is required")
        return

    # Initialize Database
    try:
        db = DatabaseManager()
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        return

    try:
        app = Application.builder().token(TOKEN).build()
        
        # Store db in bot_data for handlers to access
        app.bot_data['db'] = db
        
        # Command Handlers
        app.add_handler(CommandHandler("start", common.start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user.handle_search))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin.handle_broadcast))
        # Note: MessageHandlers overlap. I need to check state inside them or use ConversationHandler.
        # Since I'm using simple state flags in user_data, I should combine them or use a dispatcher function.
        # Or better, use a single text handler that delegates based on state.
        
        async def text_router(update, context):
            if context.user_data.get("awaiting_folder_name"):
                await admin.handle_folder_name(update, context)
            elif context.user_data.get("awaiting_search"):
                await user.handle_search(update, context)
            elif context.user_data.get("awaiting_broadcast"):
                await admin.handle_broadcast(update, context)
            else:
                pass # Ignore other text
        
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
        
        app.add_handler(MessageHandler(
            (filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO) & ~filters.COMMAND, 
            admin.handle_file_upload
        ))
        
        # Error Handler
        app.add_error_handler(common.error_handler)
        
        logger.info("✅ Bot started successfully")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
    finally:
        if 'db' in locals() and db:
            db.close()

if __name__ == "__main__":
    main()
