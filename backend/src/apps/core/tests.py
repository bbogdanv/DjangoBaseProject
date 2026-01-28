"""
Tests for core app.
"""

from django.test import Client, TestCase


class HealthCheckTestCase(TestCase):
    """Tests for health check endpoints"""

    def setUp(self):
        self.client = Client()

    def test_health_check(self):
        """Test health endpoint"""
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_readiness_check(self):
        """Test readiness endpoint"""
        response = self.client.get("/readiness/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")
