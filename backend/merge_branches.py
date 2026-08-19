import sqlite3

def merge_branches(db_path='backend/dataset.db'):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    r1 = cur.execute("UPDATE dataset SET branch = 'BEKASI' WHERE UPPER(branch) LIKE '%KARAWANG%' OR UPPER(branch) IN ('KRW');").rowcount
    r2 = cur.execute("UPDATE dataset SET branch = 'PONTIANAK' WHERE UPPER(branch) LIKE '%SINGKAWANG%' OR UPPER(branch) IN ('SKW');").rowcount
    r3 = cur.execute("UPDATE dataset SET branch = 'SURABAYA 2 /BERBEK' WHERE UPPER(branch) LIKE '%SURABAYA 3%' OR UPPER(branch) LIKE '%SURABAYA3%' OR UPPER(branch) LIKE '%SBY 3%';").rowcount

    conn.commit()
    conn.close()
    print(f"BRANCH MERGE SUCCESS! Updated Karawang->Bekasi: {r1:,} rows | Singkawang->Pontianak: {r2:,} rows | Surabaya 3->Surabaya 2 /BERBEK: {r3:,} rows")

if __name__ == '__main__':
    merge_branches()
