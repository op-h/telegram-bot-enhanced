import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

def path_to_string(path_list):
    """Convert path list to string"""
    if not path_list:
        return '/'
    return '/' + '/'.join(path_list)

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes is None:
        size_bytes = 0
    size_bytes = float(size_bytes)
    
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

async def safe_edit_message(query, text, reply_markup=None):
    """Safely edit message with error handling for 'Message is not modified' error"""
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        if "Message is not modified" in str(e):
            await query.answer("✅ Already up to date!")
        elif "Message can't be edited" in str(e):
            await query.message.reply_text(text, reply_markup=reply_markup)
        else:
            logger.error(f"❌ Error editing message: {e}")
            await query.answer("❌ Error updating interface", show_alert=True)

def add_back_button(buttons: list) -> InlineKeyboardMarkup:
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    buttons.append([InlineKeyboardButton("🧹 Clear Interface", callback_data="clear_interface")])
    return InlineKeyboardMarkup(buttons)

def main_menu_buttons(is_admin: bool) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📂 Browse Folders", callback_data="browse_folders")],
        [InlineKeyboardButton("🔍 Search Files", callback_data="search_start")]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_main")])
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_interface")])
    keyboard.append([InlineKeyboardButton("🧹 Clear Interface", callback_data="clear_interface")])
    return InlineKeyboardMarkup(keyboard)

def build_folder_buttons(folder_data: dict, is_admin=False):
    """Build folder navigation buttons"""
    buttons = []
    
    # Add subfolder buttons
    for name in sorted(folder_data.get("subfolders", {})):
        if name and len(name.strip()) > 0:
            buttons.append([InlineKeyboardButton(f"📁 {name[:50]}", callback_data=f"open_folder|{name}")])
    
    # Add file buttons
    for filename in sorted(folder_data.get("files", {})):
        if filename and len(filename.strip()) > 0:
            display_name = filename[:50] + "..." if len(filename) > 50 else filename
            buttons.append([InlineKeyboardButton(f"📄 {display_name}", callback_data=f"download|{filename}")])
    
    if is_admin:
        buttons.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_current")])
    
    return buttons
