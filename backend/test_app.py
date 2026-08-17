import sys
import os
import unittest
import json

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

class TestSLMTMBackendAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_01_health(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'ok')

    def test_02_login_success(self):
        # Admin Login
        res_admin = self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'konimex123'})
        self.assertEqual(res_admin.status_code, 200)
        self.assertTrue(res_admin.get_json()['user']['can_upload'])

        # Konimex User Login
        res_user = self.client.post('/api/auth/login', json={'username': 'konimex', 'password': 'konimex123'})
        self.assertEqual(res_user.status_code, 200)
        self.assertFalse(res_user.get_json()['user']['can_upload'])

    def test_03_login_failed(self):
        res = self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'wrongpassword'})
        self.assertEqual(res.status_code, 401)

    def test_04_get_filters(self):
        res = self.client.get('/api/data/filters')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')

    def test_05_kpi_scorecard(self):
        res = self.client.post('/api/analytics/kpi', json={'metric_type': 'idr'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('sl_kirim', data['data'])
        self.assertIn('sl_realisasi', data['data'])

    def test_06_pareto_alasan(self):
        res = self.client.post('/api/analytics/pareto', json={'dimension': 'alasan', 'metric_type': 'idr'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['dimension'], 'alasan')

    def test_07_grid_data(self):
        res = self.client.post('/api/analytics/grid', json={'limit': 10})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('data', data)

if __name__ == '__main__':
    unittest.main()
