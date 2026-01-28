"""
Tests for users app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


class UserModelTestCase(TestCase):
    """Tests for User model"""

    def setUp(self):
        self.User = get_user_model()

    def test_create_user_with_email(self):
        """Test creating user with email"""
        user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIsNotNone(user.username)  # Username должен быть автогенерирован
    
    def test_username_autogeneration(self):
        """Test username autogeneration"""
        user = self.User.objects.create_user(
            email='autogen@example.com',
            password='testpass123'
        )
        self.assertIsNotNone(user.username)
        self.assertIn('autogen', user.username.lower())
    
    def test_create_superuser(self):
        """Test creating superuser"""
        user = self.User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
    
    def test_email_unique(self):
        """Test email uniqueness"""
        self.User.objects.create_user(
            email='unique@example.com',
            password='testpass123'
        )
        with self.assertRaises(Exception):
            self.User.objects.create_user(
                email='unique@example.com',
                password='testpass123'
            )
