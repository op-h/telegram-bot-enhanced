import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

# ===== ICONS & FORMATTING =====
ICONS = {
    'folder': '📂',
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
    'unknown': '📄',
    'close': '❌',
    'clear': '🧹'
}

# ===== TRANSLATIONS (ARABIC) =====
STRINGS = {
    'welcome_header': "👋 **مرحباً بك يا {name}**",
    'welcome_body': (
        "🔐 **بوابة الأمن السيبراني**\n"
        "مكتبتك الشاملة للمحاضرات والمصادر التعليمية.\n\n"
        "👇 **اختر من القائمة أدناه:**"
    ),
    'btn_browse': "تصفح المحاضرات",
    'btn_search': "بحث في الملفات",
    'btn_admin': "لوحة التحكم",
    'btn_close': "إغلاق القائمة",
    'btn_back': "رجوع",
    'btn_clear': "تنظيف الواجهة",
    'root_name': "الرئيسية",
    'folder_header': "📂 **{name}**",
    'folder_content': "📊 **المحتويات:** {folders} مجلدات | {files} ملفات",
    'search_prompt': "🔍 **البحث المتقدم**\n\nفضلاً، أرسل اسم الملف أو الكلمة المفتاحية للبحث عنها...",
    'search_no_results': "❌ **عذراً، لم يتم العثور على نتائج.**\nحاول البحث بكلمة أخرى.",
    'search_results': "🔍 **نتائج البحث:** وجدنا {count} ملفات",
    'file_caption': "{icon} **{filename}**\n\n✅ تفضل ملفك.",
    'error_db': "❌ **خطأ في النظام**: تعذر الاتصال بقاعدة البيانات.\nيرجى التواصل مع المسؤول.",
    'interface_cleared': "🧹 **تم تنظيف الواجهة.**\nاستخدم /start للبدء من جديد.",
    'admin_panel': "⚙️ **لوحة التحكم**",
    'admin_stats': "📊 الإحصائيات",
    'admin_broadcast': "📢 إذاعة رسالة",
    'admin_manage': "إدارة المجلد الحالي",
    'back_to_root': "العودة للرئيسية"
}

def get_string(key: str, **kwargs) -> str:
    """Get translated string with formatting"""
    text = STRINGS.get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

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
    root_name = STRINGS['root_name']
    if not path_list:
        return f"{ICONS['root']} **{root_name}**"
    
    crumbs = [f"{ICONS['root']} {root_name}"]
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
    # RTL: Back button usually on the right or left? 
    # In Telegram inline keys, left is first. 
    # For Arabic, "Back" (Right) -> "Clear" (Left) might feel more natural if we consider flow?
    # But usually Back is primary navigation.
    # Let's keep standard layout but translate.
    buttons.append([
        InlineKeyboardButton(f"{ICONS['back']} {STRINGS['btn_back']}", callback_data="back"),
        InlineKeyboardButton(f"{ICONS['clear']} {STRINGS['btn_clear']}", callback_data="clear_interface")
    ])
    return InlineKeyboardMarkup(buttons)

def main_menu_buttons(is_admin: bool) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(f"{ICONS['folder']} {STRINGS['btn_browse']}", callback_data="browse_folders")],
        # Use switch_inline_query_current_chat to trigger real-time search
        [InlineKeyboardButton(f"{ICONS['search']} {STRINGS['btn_search']}", switch_inline_query_current_chat="")]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton(f"{ICONS['admin']} {STRINGS['btn_admin']}", callback_data="admin_main")])
    
    keyboard.append([InlineKeyboardButton(f"{ICONS['close']} {STRINGS['btn_close']}", callback_data="close_interface")])
    return InlineKeyboardMarkup(keyboard)

def build_folder_buttons(folder_data: dict, is_admin=False):
    """Build folder navigation buttons"""
    buttons = []
    
    # Add subfolder buttons (2 per row)
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
    
    # Add file buttons (1 per row)
    for filename in sorted(folder_data.get("files", {})):
        if filename and len(filename.strip()) > 0:
            icon = get_file_icon(filename)
            display_name = filename[:50] + "..." if len(filename) > 50 else filename
            buttons.append([InlineKeyboardButton(f"{icon} {display_name}", callback_data=f"download|{filename}")])
    
    if is_admin:
        buttons.append([InlineKeyboardButton(f"{ICONS['admin']} {STRINGS['admin_manage']}", callback_data="admin_current")])
    
    return buttons
