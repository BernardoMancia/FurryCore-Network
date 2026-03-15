import sqlite3
import os

dbs = [
    "apps/cgrf/database/base_cgrf.db",
    "apps/pawsteps/database/pawsteps.db",
    "apps/pawsteps/database.db",
    "apps/shop/database/shop.db"
]

def check_db(path):
    print(f"\n--- Checking: {path} ---")
    if not os.path.exists(path):
        print("Status: NOT FOUND")
        return
    
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Status: FOUND | Tables: {tables}")
        conn.close()
    except Exception as e:
        print(f"Status: ERROR | {e}")

if __name__ == "__main__":
    for db in dbs:
        check_db(db)
