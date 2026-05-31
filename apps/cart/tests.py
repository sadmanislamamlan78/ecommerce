from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.test import TestCase, Client
from django.urls import reverse

class CartTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.add_url = reverse('cart:add', args=[1])
        self.update_url = reverse('cart:update', args=[1])
        self.remove_url = reverse('cart:remove', args=[1])
        self.view_url = reverse('cart:cart')

        self.mock_product = {
            'id': 1,
            'name': 'Premium Cotton Shirt',
            'slug': 'premium-cotton-shirt',
            'price': '1000.00',
            'image_url': 'http://example.com/shirt.jpg',
            'stock': 10
        }

    @patch('apps.accounts.supabase_client.get_supabase_client')
    def test_add_to_cart_redirect(self, mock_get_client):
        """Test adding item to cart via standard form POST redirects to cart page."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table().select().eq().maybe_single().execute.return_value.data = self.mock_product

        response = self.client.post(self.add_url, {'quantity': 2})
        self.assertRedirects(response, '/cart/')

        # Verify item added to session
        cart = self.client.session.get('cart', {})
        self.assertIn('1', cart)
        self.assertEqual(cart['1']['quantity'], 2)
        self.assertEqual(cart['1']['name'], 'Premium Cotton Shirt')
        self.assertEqual(cart['1']['price'], '1000.00')

    @patch('apps.accounts.supabase_client.get_supabase_client')
    def test_add_to_cart_ajax(self, mock_get_client):
        """Test adding item to cart via AJAX returns JSON with updated count."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table().select().eq().maybe_single().execute.return_value.data = self.mock_product

        response = self.client.post(
            self.add_url,
            {'quantity': 3},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 3)
        self.assertIn('Added Premium Cotton Shirt to cart.', data['message'])

    @patch('apps.accounts.supabase_client.get_supabase_client')
    def test_add_to_cart_out_of_stock(self, mock_get_client):
        """Test that adding quantity exceeding stock returns error."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table().select().eq().maybe_single().execute.return_value.data = self.mock_product

        # Stock is 10, try to add 12
        response = self.client.post(
            self.add_url,
            {'quantity': 12},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Only 10 items available in stock.')

    @patch('apps.accounts.supabase_client.get_supabase_client')
    def test_update_cart_ajax(self, mock_get_client):
        """Test updating cart quantity via AJAX recalculates subtotals and VAT."""
        # Initialize session cart
        session = self.client.session
        session['cart'] = {
            '1': {
                'product_id': 1,
                'name': 'Premium Cotton Shirt',
                'slug': 'premium-cotton-shirt',
                'price': '1000.00',
                'image_url': 'http://example.com/shirt.jpg',
                'quantity': 2,
                'stock': 10
            }
        }
        session.save()

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock product stock check (which update_cart_view performs)
        mock_client.table().select().eq().maybe_single().execute.return_value.data = self.mock_product
        
        # Mock products batch fetch (which _get_fresh_cart_items performs)
        mock_client.table().select().in_().execute.return_value.data = [self.mock_product]

        # Request update to 5 items
        response = self.client.post(
            self.update_url,
            {'quantity': 5},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['quantity'], 5)
        self.assertEqual(data['cart_count'], 5)
        self.assertEqual(data['item_subtotal'], '5000.00')
        self.assertEqual(data['subtotal'], '5000.00')
        # VAT is 5% -> 250.00
        self.assertEqual(data['tax'], '250.00')
        # Grand total -> 5250.00
        self.assertEqual(data['grand_total'], '5250.00')

    @patch('apps.accounts.supabase_client.get_supabase_client')
    def test_remove_from_cart_ajax(self, mock_get_client):
        """Test removing item from cart via AJAX updates counts and resets totals."""
        session = self.client.session
        session['cart'] = {
            '1': {
                'product_id': 1,
                'name': 'Premium Cotton Shirt',
                'slug': 'premium-cotton-shirt',
                'price': '1000.00',
                'image_url': 'http://example.com/shirt.jpg',
                'quantity': 2,
                'stock': 10
            }
        }
        session.save()

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table().select().in_().execute.return_value.data = []

        response = self.client.post(
            self.remove_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 0)
        self.assertEqual(data['subtotal'], '0.00')
        self.assertEqual(data['tax'], '0.00')
        self.assertEqual(data['grand_total'], '0.00')

        # Verify session cart is empty
        cart = self.client.session.get('cart', {})
        self.assertNotIn('1', cart)
