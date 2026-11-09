import sqlite3
import json

conn = sqlite3.connect('data/pricewise.db')
cur = conn.cursor()
cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cur.fetchall()

info = {}
for name, sql in tables:
    if name.startswith("sqlite_"):
        continue
    cur.execute(f"SELECT count(*) FROM {name}")
    cnt = cur.fetchone()[0]
    info[name] = {"count": cnt, "sql": sql}

print(f"Total tables: {len(info)}")
for name, data in info.items():
    print(f"- {name}: {data['count']} rows")
