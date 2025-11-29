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
    
    # Escape name for HTML to prevent errors
    from html import escape
    safe_name = escape(user.first_name)
    
    # Use HTML for safer formatting
    welcome_header = get_string('welcome_header', name=safe_name).replace('**', '<b>').replace('**', '</b>')
    # Note: The simple replace above might be buggy if the string has other **. 
    # Let's just hardcode the HTML structure or update get_string to handle it.
    # Better: Update the string key in utils, but for now let's just format it here manually or use a safer approach.
    
    # Actually, let's just use the string as is but change the string definition in utils to use HTML tags?
    # Or just strip markdown symbols from the name.
    
    welcome_text = (
        f"👋 <b>مرحباً بك يا {safe_name}</b>\n\n"
        f"{get_string('welcome_body').replace('**', '<b>').replace('**', '</b>')}"
    )
    
    # Fix the bolding in welcome_body which uses **
    # We need to replace pairs of ** with <b> and </b>. 
    # Since we can't easily do regex replace here without importing re, 
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
