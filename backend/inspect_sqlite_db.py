import sqlite3
import os

def inspect_db(db_path="backend/dataset.db"):
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM dataset;")
    total_rows = cur.fetchone()[0]
    print(f"Total Database Rows: {total_rows:,}")

    cur.execute("SELECT DISTINCT month FROM dataset ORDER BY month;")
    months = [r[0] for r in cur.fetchall()]
    print("Unique Months:", months)

    cur.execute("SELECT DISTINCT mtm_type FROM dataset ORDER BY mtm_type;")
    mtm_types = [r[0] for r in cur.fetchall()]
    print("Unique MTM Types:", mtm_types)

    cur.execute("SELECT COUNT(DISTINCT branch) FROM dataset;")
    branch_cnt = cur.fetchone()[0]
    print(f"Total Unique Branches: {branch_cnt}")

    cur.execute("SELECT COUNT(DISTINCT mtm_alias) FROM dataset;")
    alias_cnt = cur.fetchone()[0]
    print(f"Total Unique MTM Aliases: {alias_cnt}")

    cur.execute("SELECT COUNT(DISTINCT brand_group) FROM dataset;")
    bg_cnt = cur.fetchone()[0]
    print(f"Total Unique Brand Groups: {bg_cnt}")

    cur.execute("SELECT COUNT(DISTINCT item_name) FROM dataset;")
    item_cnt = cur.fetchone()[0]
    print(f"Total Unique Items: {item_cnt}")

    conn.close()

if __name__ == "__main__":
    inspect_db()
