import os
import logging

# ===== LOGGING SETUP =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== CONFIG =====
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
DATABASE_URL = os.environ.get("DATABASE_URL")

# If no DATABASE_URL, construct from Railway/DO environment variables
if not DATABASE_URL:
    PGHOST = os.environ.get("PGHOST")
    PGPORT = os.environ.get("PGPORT", "5432")
    PGDATABASE = os.environ.get("PGDATABASE")
    PGUSER = os.environ.get("PGUSER")
    PGPASSWORD = os.environ.get("PGPASSWORD")
    
    if all([PGHOST, PGDATABASE, PGUSER, PGPASSWORD]):
        DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"

# Platform detection
PLATFORM = "🚂 Railway" if "railway" in os.environ.get("RAILWAY_ENVIRONMENT_NAME", "").lower() else \
           "🌊 DigitalOcean" if os.environ.get("DIGITALOCEAN_APP_URL") else \
           "☁️ Cloud"
