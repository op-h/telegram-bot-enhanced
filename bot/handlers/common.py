from telegram import Update
from telegram.ext import ContextTypes
from bot.config import ADMIN_USERNAME, PLATFORM
from bot.utils import main_menu_buttons
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data.get('db')
    
    # Track user
    if db:
        db.add_user(user.id, user.username)
    
    # Initialize user state
    context.user_data['current_path'] = []
    is_admin = user.username == ADMIN_USERNAME
    
    if not db:
        await update.message.reply_text("❌ Database connection failed. Please contact admin.")
        return
    
    await update.message.reply_text(
        f"📁 **Cybersecurity Lectures Bot**\n\n"
        f"🚀 Enhanced & Refactored\n"
        f"💾 **From A ---> Z**\n\n"
        f"🌐 Running on: {PLATFORM}",
        reply_markup=main_menu_buttons(is_admin),
        parse_mode='Markdown'
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify admin"""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Please try again or contact admin."
            )
        except:
            pass
