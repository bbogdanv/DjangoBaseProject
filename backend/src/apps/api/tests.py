"""
Tests for API app.
"""
from django.test import Client, TestCase


class APIRootTestCase(TestCase):
    """Tests for API root endpoint"""

    def setUp(self):
        self.client = Client()

    def test_api_root(self):
        """Test API root endpoint"""
        response = self.client.get('/api/v1/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('version', data)
        self.assertEqual(data['version'], 'v1')
