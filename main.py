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
        
        # Admin Handlers
        app.add_handler(CommandHandler("broadcast", admin.broadcast))
        app.add_handler(CommandHandler("stats", admin.stats))
        app.add_handler(CallbackQueryHandler(admin.admin_main, pattern="^admin_main$"))
        app.add_handler(CallbackQueryHandler(admin.admin_stats, pattern="^admin_stats$"))
        app.add_handler(CallbackQueryHandler(admin.admin_current, pattern="^admin_current$"))
        app.add_handler(CallbackQueryHandler(admin.create_folder_start, pattern="^create_folder_current$"))
        app.add_handler(CallbackQueryHandler(admin.upload_start, pattern="^upload_current$"))
        app.add_handler(CallbackQueryHandler(admin.delete_folder_start, pattern="^delete_folder_current$"))
        app.add_handler(CallbackQueryHandler(admin.delete_folder_confirm, pattern="^delete_folder_confirm\|"))
        app.add_handler(CallbackQueryHandler(admin.delete_file_start, pattern="^delete_file_current$"))
        app.add_handler(CallbackQueryHandler(admin.delete_file_confirm, pattern="^delete_file_confirm\|"))
        app.add_handler(CallbackQueryHandler(admin.broadcast_start, pattern="^broadcast_start$"))
        
        # User Handlers
        app.add_handler(CallbackQueryHandler(user.browse_folders, pattern="^browse_folders$"))
        app.add_handler(CallbackQueryHandler(user.open_folder, pattern="^open_folder\|"))
        app.add_handler(CallbackQueryHandler(user.download_file, pattern="^download\|"))
        app.add_handler(CallbackQueryHandler(user.search_start, pattern="^search_start$"))
        app.add_handler(CallbackQueryHandler(user.download_by_id, pattern="^download_id\|"))
        
        # Common Handlers
        app.add_handler(CallbackQueryHandler(user.back, pattern="^back$"))
        app.add_handler(CallbackQueryHandler(user.clear_interface, pattern="^clear_interface$"))
        app.add_handler(CallbackQueryHandler(common.close_handler, pattern="^close_interface$"))
        
        # Inline Query Handler (Real-time Search)
        from telegram.ext import InlineQueryHandler
        from bot.handlers import inline
        app.add_handler(InlineQueryHandler(inline.inline_query))
        
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
