from unittest.mock import MagicMock, patch
from django.test import TestCase, Client
from django.urls import reverse

class OrderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.checkout_url = reverse('orders:checkout')
        self.history_url = reverse('orders:history')

        self.mock_product = {
            'id': 1,
            'name': 'Premium Shirt',
            'slug': 'premium-shirt',
            'price': '1000.00',
            'image_url': 'http://example.com/shirt.jpg',
            'stock': 10
        }

    def test_anonymous_access_protection(self):
        """Verify anonymous users cannot checkout or view order history."""
        response = self.client.get(self.checkout_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    @patch('apps.accounts.middleware.get_supabase_client')
    @patch('apps.accounts.supabase_client.get_supabase_client')
    def test_checkout_prefills_profile_data(self, mock_get_client, mock_middleware_client):
        """Verify checkout form pre-fills with logged-in user profile details."""
        session = self.client.session
        session['supabase_access_token'] = 'fake_token'
        session['supabase_refresh_token'] = 'fake_refresh'
        session['supabase_user_id'] = 'user_uuid_123'
        session['supabase_email'] = 'test@example.com'
        session['supabase_profile'] = {
            'full_name': 'Nafis Imran',
            'phone': '01712345678',
            'address': 'Dhaka, Bangladesh'
        }
        session['cart'] = {
            '1': {
                'product_id': 1,
                'name': 'Premium Shirt',
                'slug': 'premium-shirt',
                'price': '1000.00',
                'image_url': 'http://example.com/shirt.jpg',
                'quantity': 2,
                'stock': 10
            }
        }
        session.save()

        # Mock user response for middleware validation
        mock_user = MagicMock()
        mock_user.id = 'user_uuid_123'
        mock_user.email = 'test@example.com'
        mock_get_client.return_value.get_user.return_value.user = mock_user
        mock_middleware_client.return_value.get_user.return_value.user = mock_user

        # Mock batch product fetch inside cart views
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table().select().in_().execute().data = [self.mock_product]

        response = self.client.get(self.checkout_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Secure Checkout')
        # Value of name input should be pre-filled
        self.assertContains(response, 'value="Nafis Imran"')
        self.assertContains(response, 'value="01712345678"')
        self.assertContains(response, 'Dhaka, Bangladesh')

    @patch('apps.accounts.middleware.get_supabase_client')
    @patch('apps.accounts.supabase_client.get_supabase_client')
    @patch('apps.accounts.supabase_client.get_authenticated_client')
    def test_checkout_submission_success(self, mock_get_auth_client, mock_get_client, mock_middleware_client):
        """Verify successful order submission saves records, decrements stock, updates profile, and clears cart."""
        session = self.client.session
        session['supabase_access_token'] = 'fake_token'
        session['supabase_refresh_token'] = 'fake_refresh'
        session['supabase_user_id'] = 'user_uuid_123'
        session['supabase_email'] = 'test@example.com'
        session['supabase_profile'] = {
            'full_name': 'Nafis Imran',
            'phone': '01712345678',
            'address': 'Dhaka, Bangladesh'
        }
        session['cart'] = {
            '1': {
                'product_id': '1',
                'name': 'Premium Shirt',
                'slug': 'premium-shirt',
                'price': '1000.00',
                'image_url': 'http://example.com/shirt.jpg',
                'quantity': 2,
                'stock': 10
            }
        }
        session.save()

        # Mock user
        mock_user = MagicMock()
        mock_user.id = 'user_uuid_123'
        mock_user.email = 'test@example.com'
        mock_get_client.return_value.get_user.return_value.user = mock_user
        mock_middleware_client.return_value.get_user.return_value.user = mock_user

        # Mock batch product fetch inside cart views
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table().select().in_().execute().data = [self.mock_product]

        # Mock authenticated client database inserts/updates
        mock_auth_client = MagicMock()
        mock_get_auth_client.return_value = mock_auth_client

        # Mock tables return values
        mock_orders_table = MagicMock()
        mock_orders_table.insert.return_value = mock_orders_table
        mock_orders_table.execute.return_value.data = [{'id': 42}]

        mock_items_table = MagicMock()
        mock_items_table.insert.return_value = mock_items_table
        mock_items_table.execute.return_value.data = [{'id': 100}]

        mock_products_table = MagicMock()
        mock_products_table.update.return_value = mock_products_table
        mock_products_table.eq.return_value = mock_products_table
        mock_products_table.execute.return_value.data = [{'id': 1}]

        mock_profiles_table = MagicMock()
        mock_profiles_table.upsert.return_value = mock_profiles_table
        mock_profiles_table.execute.return_value.data = [{'id': 'user_uuid_123'}]

        def side_effect(table_name):
            if table_name == 'orders':
                return mock_orders_table
            elif table_name == 'order_items':
                return mock_items_table
            elif table_name == 'products':
                return mock_products_table
            elif table_name == 'profiles':
                return mock_profiles_table
            return MagicMock()

        mock_auth_client.table.side_effect = side_effect

        post_data = {
            'full_name': 'Nafis New Name',
            'phone': '01999999999',
            'address': 'Sylhet, Bangladesh',
            'payment_method': 'cod'
        }

        response = self.client.post(self.checkout_url, post_data)
        self.assertRedirects(response, self.history_url)

        # Cart should be empty in session
        cart = self.client.session.get('cart', {})
        self.assertEqual(cart, {})

        # Profile session should update
        profile = self.client.session.get('supabase_profile', {})
        self.assertEqual(profile['full_name'], 'Nafis New Name')
        self.assertEqual(profile['phone'], '01999999999')
        self.assertEqual(profile['address'], 'Sylhet, Bangladesh')
