import sqlite3

def sample():
    conn = sqlite3.connect("backend/dataset.db")
    cur = conn.cursor()
    cur.execute("SELECT delivery_date, month, mtm_type, branch, mtm_alias, brand_group, item_name, reason_final, idr_kirim FROM dataset LIMIT 5;")
    rows = cur.fetchall()
    print("Sample Rows from SQLite DB:")
    for r in rows:
        print(" ", r)
    conn.close()

if __name__ == "__main__":
    sample()
