import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

from build_dataset_db_v2 import build_db

def build_sqlite_db(xlsx_path=None, db_path=None):
    build_db(xlsx_path=xlsx_path, db_path=db_path)

if __name__ == "__main__":
    build_sqlite_db()

