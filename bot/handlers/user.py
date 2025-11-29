from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import ADMIN_USERNAME
from bot.utils import path_to_string, safe_edit_message, add_back_button, main_menu_buttons, build_folder_buttons
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
    await safe_edit_message(query, "📂 Root Folders:", add_back_button(buttons))

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
    await safe_edit_message(query, f"📂 {folder_name}:", add_back_button(buttons))

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
            path_display = " > ".join(path)
            await safe_edit_message(query, f"📂 Current Folder: {path_display}", add_back_button(buttons))
        else:
            # Back to root
            folder_data = db.get_folder_structure('/')
            buttons = build_folder_buttons(folder_data, is_admin=is_admin)
            await safe_edit_message(query, "📂 Root Folders:", add_back_button(buttons))
    else:
        # Back to main menu
        await safe_edit_message(query, "📁 Main Menu", main_menu_buttons(is_admin))

async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = context.bot_data.get('db')
    
    filename = query.data.split("|", 1)[1]
    path = context.user_data.get('current_path', [])
    current_path = path_to_string(path)
    
    file_id = db.get_file_id(current_path, filename)
    
    if file_id:
        try:
            await query.message.reply_document(file_id, caption=f"📄 {filename}")
        except Exception as e:
            logger.error(f"❌ Error sending file {filename}: {e}")
            await query.answer("❌ Error downloading file", show_alert=True)
    else:
        await query.answer("❌ File not found", show_alert=True)

async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['awaiting_search'] = True
    await safe_edit_message(query, "🔍 Send me the file name you want to search for:", add_back_button([]))

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_search'):
        return
        
    query_text = update.message.text
    db = context.bot_data.get('db')
    results = db.search_files(query_text)
    
    if not results:
        await update.message.reply_text("❌ No files found matching your query.")
        context.user_data['awaiting_search'] = False
        return
        
    buttons = []
    for res in results:
        # We need a way to download directly or jump to folder. 
        # For simplicity, let's allow direct download if unique, or show path.
        # But download requires knowing the full path context if we use the existing download logic?
        # Actually download_file uses current_path. We need a way to download by ID or set path.
        # Let's create a special callback for search results: "dl_search|file_id|filename"
        # Or just "dl_id|file_id"
        
        # Wait, the existing download uses filename + current path. 
        # I should add a method to download by ID directly or change download handler.
        # Let's use a new callback "download_id|file_id"
        
        display_name = f"{res['filename']} ({res['folder_path']})"
        buttons.append([InlineKeyboardButton(f"📄 {display_name[:50]}", callback_data=f"download_id|{res['file_id']}")])
        
    await update.message.reply_text(f"🔍 Found {len(results)} files:", reply_markup=InlineKeyboardMarkup(buttons))
    context.user_data['awaiting_search'] = False

async def download_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    file_id = query.data.split("|", 1)[1]
    
    try:
        await query.message.reply_document(file_id, caption="📄 Search Result")
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
        text="🧹 Interface cleared.",
        reply_markup=main_menu_buttons(is_admin)
    )
