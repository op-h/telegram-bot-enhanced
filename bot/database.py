import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from bot.config import DATABASE_URL

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            # Railway/DigitalOcean require SSL
            self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            self.conn.autocommit = True
            logger.info("✅ Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            # Fallback: try without SSL for local development
            try:
                self.conn = psycopg2.connect(DATABASE_URL)
                self.conn.autocommit = True
                logger.info("✅ Connected to PostgreSQL database (no SSL)")
            except Exception as e2:
                logger.error(f"❌ Database connection failed completely: {e2}")
                raise

    def create_tables(self):
        """Create tables if they don't exist"""
        try:
            with self.conn.cursor() as cur:
                # Table for folder structure
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS folders (
                        id SERIAL PRIMARY KEY,
                        path TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        parent_path TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Table for files
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS files (
                        id SERIAL PRIMARY KEY,
                        filename TEXT NOT NULL,
                        folder_path TEXT NOT NULL,
                        file_id TEXT NOT NULL,
                        file_type TEXT DEFAULT 'document',
                        file_size BIGINT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(filename, folder_path)
                    )
                ''')

                # Table for users (NEW)
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Indexes
                cur.execute('CREATE INDEX IF NOT EXISTS idx_folders_parent_path ON folders(parent_path)')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_files_folder_path ON files(folder_path)')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_files_filename ON files(filename)') # For search
                
                # Root folder
                cur.execute('''
                    INSERT INTO folders (path, name, parent_path) 
                    VALUES ('/', 'Root', NULL) 
                    ON CONFLICT (path) DO NOTHING
                ''')
                
                logger.info("✅ Database tables created/verified successfully")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            raise

    def get_folder_structure(self, path='/'):
        """Get folder structure from database"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT name FROM folders WHERE parent_path = %s ORDER BY name', (path,))
                subfolders = {row['name']: {} for row in cur.fetchall()}
                
                cur.execute('SELECT filename, file_id FROM files WHERE folder_path = %s ORDER BY filename', (path,))
                files = {row['filename']: row['file_id'] for row in cur.fetchall()}
                
                return {'subfolders': subfolders, 'files': files}
        except Exception as e:
            logger.error(f"❌ Error getting folder structure: {e}")
            return {'subfolders': {}, 'files': {}}

    def create_folder(self, parent_path, folder_name):
        """Create a new folder"""
        try:
            new_path = f"{parent_path.rstrip('/')}/{folder_name}"
            if parent_path == '/':
                new_path = f"/{folder_name}"
                
            with self.conn.cursor() as cur:
                cur.execute('INSERT INTO folders (path, name, parent_path) VALUES (%s, %s, %s)', 
                           (new_path, folder_name, parent_path))
                logger.info(f"✅ Created folder: {new_path}")
                return True
        except psycopg2.IntegrityError:
            return False
        except Exception as e:
            logger.error(f"❌ Error creating folder: {e}")
            return False

    def delete_folder(self, parent_path, folder_name):
        """Delete a folder and all its contents"""
        try:
            folder_path = f"{parent_path.rstrip('/')}/{folder_name}"
            if parent_path == '/':
                folder_path = f"/{folder_name}"
                
            with self.conn.cursor() as cur:
                cur.execute('DELETE FROM files WHERE folder_path LIKE %s', (f"{folder_path}%",))
                cur.execute('DELETE FROM folders WHERE path LIKE %s', (f"{folder_path}%",))
                logger.info(f"✅ Deleted folder and contents: {folder_path}")
                return True
        except Exception as e:
            logger.error(f"❌ Error deleting folder: {e}")
            return False

    def add_file(self, folder_path, filename, file_id, file_type='document', file_size=0):
        """Add a file to the database"""
        try:
            with self.conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO files (filename, folder_path, file_id, file_type, file_size) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (filename, folder_path) 
                    DO UPDATE SET 
                        file_id = EXCLUDED.file_id, 
                        file_type = EXCLUDED.file_type,
                        file_size = EXCLUDED.file_size,
                        created_at = CURRENT_TIMESTAMP
                ''', (filename, folder_path, file_id, file_type, file_size))
                logger.info(f"✅ Added file: {filename} to {folder_path}")
                return True
        except Exception as e:
            logger.error(f"❌ Error adding file: {e}")
            return False

    def delete_file(self, folder_path, filename):
        """Delete a file"""
        try:
            with self.conn.cursor() as cur:
                cur.execute('DELETE FROM files WHERE filename = %s AND folder_path = %s', (filename, folder_path))
                logger.info(f"✅ Deleted file: {filename} from {folder_path}")
                return True
        except Exception as e:
            logger.error(f"❌ Error deleting file: {e}")
            return False

    def get_file_id(self, folder_path, filename):
        """Get file ID for download"""
        try:
            with self.conn.cursor() as cur:
                cur.execute('SELECT file_id FROM files WHERE filename = %s AND folder_path = %s', (filename, folder_path))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Error getting file ID: {e}")
            return None

    def get_stats(self):
        """Get database statistics"""
        try:
            with self.conn.cursor() as cur:
                cur.execute('SELECT COUNT(*) FROM folders WHERE path != %s', ('/',))
                folder_count = cur.fetchone()[0]
                
                cur.execute('SELECT COUNT(*) FROM files')
                file_count = cur.fetchone()[0]
                
                cur.execute('SELECT COALESCE(SUM(file_size), 0)::BIGINT FROM files')
                total_size = int(cur.fetchone()[0])
                
                cur.execute('SELECT COUNT(*) FROM users')
                user_count = cur.fetchone()[0]
                
                return folder_count, file_count, total_size, user_count
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return 0, 0, 0, 0

    def add_user(self, user_id, username):
        """Add or update user"""
        try:
            with self.conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO users (user_id, username) VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET 
                        username = EXCLUDED.username,
                        last_seen = CURRENT_TIMESTAMP
                ''', (user_id, username))
        except Exception as e:
            logger.error(f"❌ Error adding user: {e}")

    def search_files(self, query):
        """Search for files by name"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('''
                    SELECT filename, folder_path, file_id 
                    FROM files 
                    WHERE filename ILIKE %s 
                    LIMIT 20
                ''', (f'%{query}%',))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"❌ Error searching files: {e}")
            return []

    def get_all_users(self):
        """Get all user IDs for broadcast"""
        try:
            with self.conn.cursor() as cur:
                cur.execute('SELECT user_id FROM users')
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"❌ Error getting users: {e}")
            return []

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("🔐 Database connection closed")
