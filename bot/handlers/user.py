from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import ADMIN_USERNAME
from bot.utils import path_to_string, safe_edit_message, add_back_button, main_menu_buttons, build_folder_buttons, get_breadcrumbs, get_file_icon
import logging

logger = logging.getLogger(__name__)

async def browse_folders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    is_admin = user.username == ADMIN_USERNAME
    db = context.bot_data.get('db')
    
    # Reset path
    context.user_data['current_path'] = []
    
    folder_data = db.get_folder_structure('/')
    buttons = build_folder_buttons(folder_data, is_admin=is_admin)
    
    breadcrumbs = get_breadcrumbs([])
    text = f"{breadcrumbs}\n\n👇 **Select a folder to browse:**"
    
    await safe_edit_message(query, text, add_back_button(buttons))

async def open_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    is_admin = user.username == ADMIN_USERNAME
    db = context.bot_data.get('db')
    
    folder_name = query.data.split("|", 1)[1]
    
    # Update path
    path = context.user_data.get('current_path', [])
    path.append(folder_name)
    context.user_data['current_path'] = path
    
    new_path = path_to_string(path)
    folder_data = db.get_folder_structure(new_path)
    buttons = build_folder_buttons(folder_data, is_admin=is_admin)
    
    breadcrumbs = get_breadcrumbs(path)
    file_count = len(folder_data.get('files', {}))
    folder_count = len(folder_data.get('subfolders', {}))
    
    text = (
        f"{breadcrumbs}\n"
        f"──────────────────\n"
        f"📂 **Contents**: {folder_count} folders, {file_count} files\n"
    )
    
    await safe_edit_message(query, text, add_back_button(buttons))

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    is_admin = user.username == ADMIN_USERNAME
    db = context.bot_data.get('db')
    
    path = context.user_data.get('current_path', [])
    
    if path:
        path.pop()
        context.user_data['current_path'] = path
        current_path = path_to_string(path)
        
        if path:
            folder_data = db.get_folder_structure(current_path)
            buttons = build_folder_buttons(folder_data, is_admin=is_admin)
            breadcrumbs = get_breadcrumbs(path)
            text = f"{breadcrumbs}\n──────────────────\n📂 **Contents**:"
            await safe_edit_message(query, text, add_back_button(buttons))
        else:
            # Back to root
            folder_data = db.get_folder_structure('/')
            buttons = build_folder_buttons(folder_data, is_admin=is_admin)
            breadcrumbs = get_breadcrumbs([])
            text = f"{breadcrumbs}\n\n👇 **Select a folder to browse:**"
            await safe_edit_message(query, text, add_back_button(buttons))
    else:
        # Back to main menu
        await safe_edit_message(query, "📁 **Main Menu**\n\nWelcome back! What would you like to do?", main_menu_buttons(is_admin))

async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = context.bot_data.get('db')
    
    filename = query.data.split("|", 1)[1]
    path = context.user_data.get('current_path', [])
    current_path = path_to_string(path)
    
    file_id = db.get_file_id(current_path, filename)
    
    if file_id:
        try:
            icon = get_file_icon(filename)
            await query.message.reply_document(file_id, caption=f"{icon} **{filename}**\n\n✅ Here is your file.", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"❌ Error sending file {filename}: {e}")
            await query.answer("❌ Error downloading file", show_alert=True)
    else:
        await query.answer("❌ File not found", show_alert=True)

async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['awaiting_search'] = True
    await safe_edit_message(query, "🔍 **File Search**\n\nPlease type the name of the file you are looking for:", add_back_button([]))

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_search'):
        return
        
    query_text = update.message.text
    db = context.bot_data.get('db')
    results = db.search_files(query_text)
    
    if not results:
        await update.message.reply_text("❌ **No files found matching your query.**\nTry a different keyword.")
        context.user_data['awaiting_search'] = False
        return
        
    buttons = []
    for res in results:
        icon = get_file_icon(res['filename'])
        display_name = f"{res['filename']} ({res['folder_path']})"
        buttons.append([InlineKeyboardButton(f"{icon} {display_name[:50]}", callback_data=f"download_id|{res['file_id']}")])
        
    await update.message.reply_text(f"🔍 **Found {len(results)} files:**", reply_markup=InlineKeyboardMarkup(buttons), parse_mode='Markdown')
    context.user_data['awaiting_search'] = False

async def download_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    file_id = query.data.split("|", 1)[1]
    
    try:
        await query.message.reply_document(file_id, caption="📄 **Search Result**", parse_mode='Markdown')
    except Exception as e:
        await query.answer("❌ Error downloading file", show_alert=True)

async def clear_interface(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    is_admin = user.username == ADMIN_USERNAME
    
    try:
        await query.message.delete()
    except:
        pass
        
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="🧹 **Interface cleared.**\nUse /start to open the menu again.",
        reply_markup=main_menu_buttons(is_admin),
        parse_mode='Markdown'
    )
