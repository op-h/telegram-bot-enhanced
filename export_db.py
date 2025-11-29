import os
import json
import pg8000.native
from urllib.parse import urlparse
from datetime import datetime

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

def export_data(db_url):
    try:
        # Parse URL
        # Format: postgresql://user:password@host:port/database
        if 'sslmode' not in db_url and '?' not in db_url:
             db_url += '?sslmode=require'
             
        parsed = urlparse(db_url)
        username = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432
        database = parsed.path.lstrip('/')
        
        print(f"🔌 Connecting to {host}:{port} as {username}...")
        
        # Connect using pg8000
        con = pg8000.native.Connection(
            user=username,
            password=password,
            host=host,
            port=port,
            database=database,
            ssl_context=True # Force SSL
        )
        
        data = {}
        
        # Export Folders
        print("Exporting folders...")
        # pg8000 native returns list of rows, need to map to dict if we want same format
        # But for migration, list of dicts is best.
        
        # Helper to convert rows to dicts
        def query_to_dict(query):
            results = []
            for row in con.run(query):
                columns = [c['name'] for c in con.columns]
                results.append(dict(zip(columns, row)))
            return results

        data['folders'] = query_to_dict("SELECT * FROM folders")
        
        # Export Files
        print("Exporting files...")
        data['files'] = query_to_dict("SELECT * FROM files")
        
        # Export Users
        try:
            print("Exporting users...")
            data['users'] = query_to_dict("SELECT * FROM users")
        except:
            print("Users table not found (skipping)")
            data['users'] = []
            
        con.close()
        
        # Save to file
        filename = 'railway_backup.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=DateTimeEncoder, indent=2)
            
        print(f"✅ Data exported successfully to {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")
        return False

if __name__ == "__main__":
    url = input("Enter your Railway DATABASE_URL: ").strip()
    if url:
        export_data(url)
    else:
        print("URL is required.")
