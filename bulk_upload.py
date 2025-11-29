import os
import asyncio
import logging
import psycopg2
from telegram import Bot
from telegram.error import RetryAfter
import time

# ===== CONFIGURATION =====
# You will be asked to enter these when running the script
print("--- CONFIGURATION ---")
DATABASE_URL = input("1. Enter your DigitalOcean DATABASE_URL: ").strip()
BOT_TOKEN = input("2. Enter your BOT_TOKEN: ").strip()
ADMIN_ID = input("3. Enter your Telegram User ID (numbers only): ").strip()
SOURCE_FOLDER = input("4. Enter the full path to the folder you want to upload: ").strip()

# Remove quotes if user added them
if SOURCE_FOLDER.startswith('"') and SOURCE_FOLDER.endswith('"'):
    SOURCE_FOLDER = SOURCE_FOLDER[1:-1]

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database Connection
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

async def upload_file(bot, chat_id, file_path):
    """Upload file to Telegram and get file_id"""
    retries = 3
    for i in range(retries):
        try:
            with open(file_path, 'rb') as f:
                logger.info(f"📤 Uploading: {os.path.basename(file_path)}...")
                message = await bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    caption=f"🗄 Backup: {os.path.basename(file_path)}"
                )
                return message.document.file_id, message.document.file_unique_id, message.document.file_size
        except RetryAfter as e:
            logger.warning(f"⏳ Flood limit exceeded. Sleeping for {e.retry_after} seconds...")
            await asyncio.sleep(e.retry_after)
        except Exception as e:
            logger.error(f"❌ Error uploading {file_path}: {e}")
            if i == retries - 1:
                return None, None, None
            await asyncio.sleep(5)

def create_folder_in_db(cursor, path):
    """Ensure folder exists in DB"""
    parent = os.path.dirname(path).replace('\\', '/')
    name = os.path.basename(path)
    
    if parent == '': parent = '/'
    if not parent.startswith('/'): parent = '/' + parent
    
    full_path = path.replace('\\', '/')
    if not full_path.startswith('/'): full_path = '/' + full_path
    
    # Check if exists
    cursor.execute("SELECT id FROM folders WHERE path = %s", (full_path,))
    if cursor.fetchone():
        return

    # Create parent if needed
    if parent != '/':
        create_folder_in_db(cursor, parent)

    logger.info(f"mw Creating folder: {full_path}")
    cursor.execute(
        "INSERT INTO folders (path, name, parent_path) VALUES (%s, %s, %s) ON CONFLICT (path) DO NOTHING",
        (full_path, name, parent)
    )

def ensure_schema(cursor):
    """Ensure the database schema is up to date"""
    try:
        # Check if file_unique_id column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='files' AND column_name='file_unique_id'
        """)
        if not cursor.fetchone():
            logger.info("🔧 Migrating database: Adding file_unique_id column...")
            cursor.execute("ALTER TABLE files ADD COLUMN file_unique_id TEXT")
            cursor.execute("UPDATE files SET file_unique_id = 'unknown' WHERE file_unique_id IS NULL")
            logger.info("✅ Schema updated.")
    except Exception as e:
        logger.warning(f"⚠️ Schema check failed (might be fine): {e}")

async def main():
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Fix schema if needed
    ensure_schema(cursor)
    
    bot = Bot(token=BOT_TOKEN)

    if not os.path.exists(SOURCE_FOLDER):
        logger.error(f"❌ Folder not found: {SOURCE_FOLDER}")
        return

    logger.info(f"📂 Scanning folder: {SOURCE_FOLDER}")
    
    file_count = 0
    for _, _, files in os.walk(SOURCE_FOLDER):
        file_count += len(files)
    
    logger.info(f"📊 Found {file_count} files to process.")
    
    if file_count == 0:
        logger.warning("⚠️ The folder appears to be empty!")
        return

    # Walk through the source folder
    for root, dirs, files in os.walk(SOURCE_FOLDER):
        # Calculate relative path for DB
        rel_path = os.path.relpath(root, SOURCE_FOLDER)
        if rel_path == '.':
            db_path = '/'
        else:
            db_path = '/' + rel_path.replace('\\', '/')
        
        # Create folder in DB
        if db_path != '/':
            create_folder_in_db(cursor, db_path)
        
        for file in files:
            file_path = os.path.join(root, file)
            filename = file
            
            # Check if file already exists
            cursor.execute(
                "SELECT id FROM files WHERE folder_path = %s AND filename = %s",
                (db_path, filename)
            )
            if cursor.fetchone():
                logger.info(f"⏭️ Skipping {filename} (already exists)")
                continue
            
            # Upload
            file_id, file_unique_id, file_size = await upload_file(bot, ADMIN_ID, file_path)
            
            if file_id:
                cursor.execute(
                    """
                    INSERT INTO files (file_id, file_unique_id, filename, file_size, file_type, folder_path)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (file_id, file_unique_id, filename, file_size, 'document', db_path)
                )
                logger.info(f"✅ Saved {filename} to DB")
            
            # Sleep to avoid hitting limits too hard
            await asyncio.sleep(2)

    logger.info("🎉 Upload Complete!")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
