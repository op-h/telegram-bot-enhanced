from telegram import Update, InlineQueryResultDocument, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
from bot.utils import get_file_icon, get_string
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline queries"""
    query = update.inline_query.query
    db = context.bot_data.get('db')
    
    if not query:
        return

    results = []
    
    # Search in DB
    files = db.search_files(query)
    
    for file in files:
        file_id = file['file_id']
        filename = file['filename']
        folder = file['folder_path']
        icon = get_file_icon(filename)
        
        # Create result object
        results.append(
            InlineQueryResultDocument(
                id=str(uuid4()),
                title=f"{icon} {filename}",
                document_url=file_id, # Telegram allows file_id here for cached files
                mime_type="application/pdf", # Default to PDF, but doesn't matter much for cached
                description=f"📂 {folder}",
                caption=get_string('file_caption', icon=icon, filename=filename),
                parse_mode='Markdown'
            )
        )
        
    # If no results, show a tip
    if not results:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=get_string('search_no_results').split('\n')[0],
                input_message_content=InputTextMessageContent(
                    message_text=f"🔍 No results found for: {query}"
                ),
                description="Try typing a different keyword."
            )
        )

    await update.inline_query.answer(results, cache_time=0)
