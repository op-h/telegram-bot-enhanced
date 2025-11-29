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
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Please try again or contact admin."
            )
        except:
            pass
