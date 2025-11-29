from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import ADMIN_USERNAME, PLATFORM
from bot.utils import path_to_string, safe_edit_message, add_back_button, format_file_size
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def check_admin(update: Update):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        if update.callback_query:
            await update.callback_query.answer("⛔ Admin access required", show_alert=True)
        else:
            await update.message.reply_text("⛔ Admin access required")
        return False
    return True

async def admin_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await check_admin(update): return
    
    buttons = [
        [InlineKeyboardButton("📂 Browse & Manage", callback_data="browse_folders")],
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="broadcast_start")]
    ]
    await safe_edit_message(query, "⚙️ Admin Main Panel", add_back_button(buttons))

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await check_admin(update): return
    
    db = context.bot_data.get('db')
    folder_count, file_count, total_size, user_count = db.get_stats()
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    stats_text = (
        f"📊 **Bot Statistics** (Updated: {timestamp}):\n\n"
        f"📁 Total Folders: **{folder_count}**\n"
        f"📄 Total Files: **{file_count}**\n"
        f"👥 Total Users: **{user_count}**\n"
        f"💾 Total Size: **{format_file_size(total_size)}**\n"
        f"🗄️ Database: **PostgreSQL (Persistent)**\n"
        f"🌐 Platform: **{PLATFORM}**"
    )
    
    buttons = [[InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")]]
    await safe_edit_message(query, stats_text, add_back_button(buttons))

async def admin_current(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await check_admin(update): return
    
    path = context.user_data.get('current_path', [])
    path_display = " > ".join(path) if path else "Root"
    
    buttons = [
        [InlineKeyboardButton("📁 Create Folder", callback_data="create_folder_current")],
        [InlineKeyboardButton("📤 Upload File", callback_data="upload_current")],
        [InlineKeyboardButton("❌ Delete Folder", callback_data="delete_folder_current")],
        [InlineKeyboardButton("🗑️ Delete File", callback_data="delete_file_current")]
    ]
    await safe_edit_message(query, f"⚙️ Admin Panel\n📍 Current: {path_display}", add_back_button(buttons))

async def create_folder_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await check_admin(update): return
    
    context.user_data["awaiting_folder_name"] = True
    await safe_edit_message(query, "✏️ Send the name for the new folder:")

async def handle_folder_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_folder_name"): return
    if not await check_admin(update): return
    
    name = update.message.text.strip()
    db = context.bot_data.get('db')
    path = context.user_data.get('current_path', [])
    parent_path = path_to_string(path)
    
    if db.create_folder(parent_path, name):
        await update.message.reply_text(f"✅ Folder '{name}' created successfully.")
    else:
        await update.message.reply_text("⚠️ Folder already exists or error occurred.")
            
    context.user_data["awaiting_folder_name"] = False

async def upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await check_admin(update): return
    
    context.user_data["awaiting_upload"] = True
    await safe_edit_message(query, "📤 Now send the file(s) to upload into this folder.")

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_upload"): return
    if not await check_admin(update): return
    
    db = context.bot_data.get('db')
    path = context.user_data.get('current_path', [])
    folder_path = path_to_string(path)
    
    # ... (File handling logic similar to original, simplified)
    try:
        filename = None
        file_id = None
        file_type = "document"
        file_size = 0
        
        if update.message.document:
            file = update.message.document
            filename = file.file_name or f"document_{file.file_unique_id}"
            file_id = file.file_id
            file_size = file.file_size or 0
        elif update.message.photo:
            photo = update.message.photo[-1]
            filename = f"photo_{photo.file_unique_id}.jpg"
            file_id = photo.file_id
            file_type = "photo"
            file_size = photo.file_size or 0
        elif update.message.video:
            video = update.message.video
            filename = f"video_{video.file_unique_id}.mp4"
            file_id = video.file_id
            file_type = "video"
            file_size = video.file_size or 0
        elif update.message.audio:
            audio = update.message.audio
            filename = audio.file_name or f"audio_{audio.file_unique_id}.mp3"
            file_id = audio.file_id
            file_type = "audio"
            file_size = audio.file_size or 0
        else:
            await update.message.reply_text("❌ Unsupported file type.")
            return

        if db.add_file(folder_path, filename, file_id, file_type, file_size):
            await update.message.reply_text(f"✅ Uploaded: {filename}")
        else:
            await update.message.reply_text("❌ Error uploading file.")
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        await update.message.reply_text("❌ Error processing upload.")

async def delete_folder_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await check_admin(update): return
    
    db = context.bot_data.get('db')
    path = context.user_data.get('current_path', [])
    current_path = path_to_string(path)
    
    folder_data = db.get_folder_structure(current_path)
    subfolders = folder_data.get("subfolders", {})
    
    buttons = []
    for name in sorted(subfolders.keys()):
        buttons.append([InlineKeyboardButton(f"🗑️ {name}", callback_data=f"delete_folder_confirm|{name}")])
        
    await safe_edit_message(query, "🗑️ Select a folder to delete:", add_back_button(buttons))

async def delete_folder_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await check_admin(update): return
    
    folder_name = query.data.split("|", 1)[1]
    db = context.bot_data.get('db')
    path = context.user_data.get('current_path', [])
    current_path = path_to_string(path)
    
    if db.delete_folder(current_path, folder_name):
        await safe_edit_message(query, f"✅ Folder '{folder_name}' deleted.", add_back_button([]))
    else:
        await safe_edit_message(query, "❌ Error deleting folder.", add_back_button([]))

async def delete_file_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await check_admin(update): return
    
    db = context.bot_data.get('db')
    path = context.user_data.get('current_path', [])
    current_path = path_to_string(path)
    
    folder_data = db.get_folder_structure(current_path)
    files = folder_data.get("files", {})
    
    buttons = []
    for filename in sorted(files.keys()):
        buttons.append([InlineKeyboardButton(f"🗑️ {filename}", callback_data=f"delete_file_confirm|{filename}")])
        
    await safe_edit_message(query, "🗑️ Select a file to delete:", add_back_button(buttons))

async def delete_file_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await check_admin(update): return
    
    filename = query.data.split("|", 1)[1]
    db = context.bot_data.get('db')
    path = context.user_data.get('current_path', [])
    current_path = path_to_string(path)
    
    if db.delete_file(current_path, filename):
        await safe_edit_message(query, f"✅ File '{filename}' deleted.", add_back_button([]))
    else:
        await safe_edit_message(query, "❌ Error deleting file.", add_back_button([]))

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await check_admin(update): return
    
    context.user_data["awaiting_broadcast"] = True
    await safe_edit_message(query, "📢 Send the message you want to broadcast to all users:", add_back_button([]))

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_broadcast"): return
    if not await check_admin(update): return
    
    message = update.message.text
    db = context.bot_data.get('db')
    users = db.get_all_users()
    
    sent_count = 0
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"📢 **Announcement**\n\n{message}", parse_mode='Markdown')
            sent_count += 1
        except Exception:
            pass # User blocked bot or other error
            
    await update.message.reply_text(f"✅ Broadcast sent to {sent_count} users.")
    context.user_data["awaiting_broadcast"] = False
