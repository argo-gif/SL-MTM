import sqlite3
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "dataset.db")

print(f"Migrating schema for {db_path}...")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cols = [info[1] for info in cur.execute("PRAGMA table_info(dataset);").fetchall()]
print("Current columns:", cols)

if 'year' not in cols:
    print("Adding 'year' column...")
    cur.execute("ALTER TABLE dataset ADD COLUMN year INTEGER;")
if 'month_num' not in cols:
    print("Adding 'month_num' column...")
    cur.execute("ALTER TABLE dataset ADD COLUMN month_num INTEGER;")

print("Updating year & month_num values...")
cur.execute("UPDATE dataset SET year = CAST(substr(month, 1, 4) AS INTEGER), month_num = CAST(substr(month, 6, 2) AS INTEGER) WHERE (year IS NULL OR year = 0) AND length(month) >= 7;")

print("Creating indexes idx_month, idx_year, idx_month_num...")
cur.execute("CREATE INDEX IF NOT EXISTS idx_month ON dataset(month);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_year ON dataset(year);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_month_num ON dataset(month_num);")

conn.commit()
print(f"Migration completed! Total rows in dataset: {cur.execute('SELECT COUNT(*) FROM dataset;').fetchone()[0]:,}")
conn.close()
