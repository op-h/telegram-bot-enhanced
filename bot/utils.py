import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

# ===== ICONS & FORMATTING =====
ICONS = {
    'folder': '📁',
    'root': '🏠',
    'back': '🔙',
    'search': '🔍',
    'admin': '⚙️',
    'upload': '📤',
    'delete': '🗑️',
    'file': '📄',
    'photo': '🖼️',
    'video': '🎥',
    'audio': '🎵',
    'archive': '📦',
    'code': '💻',
    'unknown': '📄'
}

def get_file_icon(filename: str) -> str:
    """Get icon based on file extension"""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']: return ICONS['photo']
    if ext in ['mp4', 'mov', 'avi', 'mkv']: return ICONS['video']
    if ext in ['mp3', 'wav', 'ogg', 'm4a']: return ICONS['audio']
    if ext in ['zip', 'rar', '7z', 'tar', 'gz']: return ICONS['archive']
    if ext in ['py', 'js', 'html', 'css', 'json', 'cpp', 'c', 'java']: return ICONS['code']
    return ICONS['file']

def path_to_string(path_list):
    """Convert path list to string"""
    if not path_list:
        return '/'
    return '/' + '/'.join(path_list)

def get_breadcrumbs(path_list):
    """Generate navigation breadcrumbs"""
    if not path_list:
        return f"{ICONS['root']} **Root**"
    
    crumbs = [f"{ICONS['root']} Root"]
    for i, folder in enumerate(path_list):
        if i == len(path_list) - 1:
            # Current folder (bold)
            crumbs.append(f"📂 **{folder}**")
        else:
            # Parent folders
            crumbs.append(f"📂 {folder}")
            
    return " › ".join(crumbs)

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
    """Safely edit message with error handling"""
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        if "Message is not modified" in str(e):
            await query.answer("✅ Already up to date!")
        elif "Message can't be edited" in str(e):
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            logger.error(f"❌ Error editing message: {e}")
            await query.answer("❌ Error updating interface", show_alert=True)

def add_back_button(buttons: list) -> InlineKeyboardMarkup:
    buttons.append([InlineKeyboardButton(f"{ICONS['back']} Back", callback_data="back")])
    buttons.append([InlineKeyboardButton("🧹 Close", callback_data="clear_interface")])
    return InlineKeyboardMarkup(buttons)

def main_menu_buttons(is_admin: bool) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(f"{ICONS['folder']} Browse Lectures", callback_data="browse_folders")],
        [InlineKeyboardButton(f"{ICONS['search']} Search Files", callback_data="search_start")]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton(f"{ICONS['admin']} Admin Dashboard", callback_data="admin_main")])
    
    keyboard.append([InlineKeyboardButton("❌ Close Menu", callback_data="close_interface")])
    return InlineKeyboardMarkup(keyboard)

def build_folder_buttons(folder_data: dict, is_admin=False):
    """Build folder navigation buttons"""
    buttons = []
    
    # Add subfolder buttons (2 per row for better look)
    subfolders = sorted(folder_data.get("subfolders", {}))
    folder_rows = []
    for i in range(0, len(subfolders), 2):
        row = []
        name1 = subfolders[i]
        row.append(InlineKeyboardButton(f"{ICONS['folder']} {name1[:30]}", callback_data=f"open_folder|{name1}"))
        
        if i + 1 < len(subfolders):
            name2 = subfolders[i+1]
            row.append(InlineKeyboardButton(f"{ICONS['folder']} {name2[:30]}", callback_data=f"open_folder|{name2}"))
        folder_rows.append(row)
    
    buttons.extend(folder_rows)
    
    # Add file buttons (1 per row for readability)
    for filename in sorted(folder_data.get("files", {})):
        if filename and len(filename.strip()) > 0:
            icon = get_file_icon(filename)
            display_name = filename[:50] + "..." if len(filename) > 50 else filename
            buttons.append([InlineKeyboardButton(f"{icon} {display_name}", callback_data=f"download|{filename}")])
    
    if is_admin:
        buttons.append([InlineKeyboardButton(f"{ICONS['admin']} Manage This Folder", callback_data="admin_current")])
    
    return buttons
