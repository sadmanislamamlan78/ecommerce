"""Authentication and profile validation tests (Phase 6)."""
from django.test import Client, SimpleTestCase
from django.urls import reverse

from apps.accounts.forms import LoginForm, ProfileForm, RegisterForm


class RegisterFormTests(SimpleTestCase):
    def test_password_mismatch_shows_error(self):
        form = RegisterForm(data={
            'full_name': 'Test User',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'different123',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_password', form.errors)

    def test_invalid_name_characters(self):
        form = RegisterForm(data={
            'full_name': 'Test<script>',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('full_name', form.errors)


class ProfileFormTests(SimpleTestCase):
    def test_optional_phone_allows_blank(self):
        form = ProfileForm(data={'full_name': '', 'phone': '', 'address': ''})
        self.assertTrue(form.is_valid())

    def test_invalid_phone_rejected(self):
        form = ProfileForm(data={
            'full_name': 'User',
            'phone': 'not-a-phone',
            'address': '',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)


class LoginFormTests(SimpleTestCase):
    def test_empty_password_rejected(self):
        form = LoginForm(data={'email': 'user@example.com', 'password': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)


class AccountsViewTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_profile_requires_login(self):
        url = reverse('accounts:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
