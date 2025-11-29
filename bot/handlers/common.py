from telegram import Update
from telegram.ext import ContextTypes
from bot.config import ADMIN_USERNAME, PLATFORM
from bot.utils import main_menu_buttons, safe_edit_message, get_string
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
        msg = get_string('error_db')
        if update.callback_query:
            await update.callback_query.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    welcome_text = get_string('welcome_header', name=user.first_name) + "\n\n" + get_string('welcome_body')
    
    if update.callback_query:
        await update.callback_query.answer()
        await safe_edit_message(update.callback_query, welcome_text, reply_markup=main_menu_buttons(is_admin))
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=main_menu_buttons(is_admin),
            parse_mode='Markdown'
        )

async def close_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass

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
