import sqlite3
db_path = "base_cgrf.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT id, cnf, nome FROM cidadaos LIMIT 10")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
