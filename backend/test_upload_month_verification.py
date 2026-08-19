import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from build_dataset_db_v2 import ingest_month_data

class TestUploadMonthVerification(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.test_excel = os.path.join(self.base_dir, "uploaded_active_dataset.xlsx")
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.db")

    def test_mismatched_month_rejection(self):
        """Uploading file with mismatched target month (e.g. 2026-09 when file has 2026-08) should fail verification"""
        print("\n1. Testing mismatched target month (2026-09 vs file data 2026-08)...")
        res = ingest_month_data(self.test_excel, target_month="2026-09", db_path=self.db_path)
        self.assertEqual(res.get("status"), "error")
        self.assertIn("Verifikasi Gagal", res.get("message", ""))
        print("PASS: Mismatched month correctly rejected ->", res["message"])

    def test_matching_month_ingestion(self):
        """Uploading file with matching target month (2026-07) should succeed and update database"""
        print("\n2. Testing matching target month (2026-07)...")
        res = ingest_month_data(self.test_excel, target_month="2026-07", db_path=self.db_path)
        self.assertEqual(res.get("status"), "success")
        self.assertGreater(res.get("inserted_count", 0), 0)
        print("PASS: Matching month correctly ingested ->", res["message"])

if __name__ == "__main__":
    unittest.main()
