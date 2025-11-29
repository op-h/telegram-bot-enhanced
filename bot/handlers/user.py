from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import ADMIN_USERNAME
from bot.utils import path_to_string, safe_edit_message, add_back_button, main_menu_buttons, build_folder_buttons, get_breadcrumbs, get_file_icon, get_string
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
    text = f"{breadcrumbs}\n\n👇 **{get_string('welcome_body').split('👇')[1].strip()}**"
    
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
        f"{get_string('folder_content', folders=folder_count, files=file_count)}\n"
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
            file_count = len(folder_data.get('files', {}))
            folder_count = len(folder_data.get('subfolders', {}))
            text = f"{breadcrumbs}\n──────────────────\n{get_string('folder_content', folders=folder_count, files=file_count)}"
            await safe_edit_message(query, text, add_back_button(buttons))
        else:
            # Back to root
            folder_data = db.get_folder_structure('/')
            buttons = build_folder_buttons(folder_data, is_admin=is_admin)
            breadcrumbs = get_breadcrumbs([])
            text = f"{breadcrumbs}\n\n👇 **{get_string('welcome_body').split('👇')[1].strip()}**"
            await safe_edit_message(query, text, add_back_button(buttons))
    else:
        # Back to main menu
        welcome_text = get_string('welcome_header', name=user.first_name) + "\n\n" + get_string('welcome_body')
        await safe_edit_message(query, welcome_text, main_menu_buttons(is_admin))

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
            caption = get_string('file_caption', icon=icon, filename=filename)
            await query.message.reply_document(file_id, caption=caption, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"❌ Error sending file {filename}: {e}")
            await query.answer("❌ Error downloading file", show_alert=True)
    else:
        await query.answer("❌ File not found", show_alert=True)

async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['awaiting_search'] = True
    await safe_edit_message(query, get_string('search_prompt'), add_back_button([]))

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_search'):
        return
        
    query_text = update.message.text
    db = context.bot_data.get('db')
    results = db.search_files(query_text)
    
    if not results:
        await update.message.reply_text(get_string('search_no_results'))
        context.user_data['awaiting_search'] = False
        return
        
    buttons = []
    for res in results:
        icon = get_file_icon(res['filename'])
        display_name = f"{res['filename']} ({res['folder_path']})"
        buttons.append([InlineKeyboardButton(f"{icon} {display_name[:50]}", callback_data=f"download_id|{res['file_id']}")])
        
    await update.message.reply_text(
        get_string('search_results', count=len(results), query=query_text),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='Markdown'
    )
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
        text=get_string('interface_cleared'),
        reply_markup=main_menu_buttons(is_admin),
        parse_mode='Markdown'
    )
