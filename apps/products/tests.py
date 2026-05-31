"""Catalog and admin validation tests (Phase 6)."""
from unittest.mock import patch

from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from apps.orders.forms import CheckoutForm
from apps.products.forms import ProductAdminForm


class CheckoutFormValidationTests(SimpleTestCase):
    def test_short_address_rejected(self):
        form = CheckoutForm(data={
            'full_name': 'Nafis Imran',
            'phone': '01712345678',
            'address': 'Dhaka',
            'payment_method': 'cod',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('address', form.errors)


class ProductAdminFormTests(SimpleTestCase):
    @patch('apps.products.forms.get_categories')
    def test_create_requires_image(self, mock_categories):
        mock_categories.return_value = [{'id': 1, 'name': 'Men', 'slug': 'men'}]
        form = ProductAdminForm(data={
            'name': 'New Shirt',
            'slug': '',
            'description': '',
            'price': '999.00',
            'category_id': '1',
            'stock': '10',
            'image_url': '',
        }, is_edit=False)
        self.assertFalse(form.is_valid())
        self.assertIn('image_file', form.errors)


class StaffAdminAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.manage_url = reverse('products:admin_dashboard')

    def test_anonymous_user_redirected_from_manage(self):
        response = self.client.get(self.manage_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_non_staff_session_redirected_from_manage(self):
        session = self.client.session
        session['supabase_access_token'] = 'fake'
        session['supabase_refresh_token'] = 'fake'
        session['supabase_user_id'] = 'user-1'
        session['supabase_email'] = 'user@example.com'
        session['is_staff'] = False
        session.save()

        with patch('apps.accounts.middleware.get_supabase_client') as mock_client:
            mock_user = type('User', (), {'id': 'user-1', 'email': 'user@example.com'})()
            mock_client.return_value.get_user.return_value.user = mock_user
            response = self.client.get(self.manage_url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('products:home'))
