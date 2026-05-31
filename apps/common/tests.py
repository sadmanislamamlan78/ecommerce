"""Unit tests for shared validators and error helpers (Phase 6)."""
from django.test import SimpleTestCase

from apps.common.errors import friendly_error_message
from apps.common.validators import (
    clamp_cart_quantity,
    parse_price_filter,
    validate_address,
    validate_category_slug,
    validate_search_query,
)


class ValidatorTests(SimpleTestCase):
    def test_validate_address_requires_minimum_length(self):
        with self.assertRaises(ValueError):
            validate_address('Short', required=True)

    def test_validate_search_query_truncates_long_input(self):
        long_q = 'x' * 150
        self.assertEqual(len(validate_search_query(long_q)), 100)

    def test_parse_price_filter_rejects_invalid(self):
        self.assertIsNone(parse_price_filter('not-a-price'))
        self.assertEqual(parse_price_filter('599'), 599)

    def test_validate_category_slug_rejects_invalid(self):
        self.assertEqual(validate_category_slug('men!', {'men'}), '')
        self.assertEqual(validate_category_slug('men', {'men'}), 'men')

    def test_clamp_cart_quantity_bounds(self):
        self.assertEqual(clamp_cart_quantity(0), 1)
        self.assertEqual(clamp_cart_quantity(500), 99)
        self.assertEqual(clamp_cart_quantity('abc', default=2), 2)


class FriendlyErrorTests(SimpleTestCase):
    def test_sequence_permission_message(self):
        exc = Exception('permission denied for sequence products_id_seq')
        msg = friendly_error_message(exc)
        self.assertIn('phase5_fix_product_insert', msg)

    def test_rls_message(self):
        exc = Exception('new row violates row-level security policy')
        msg = friendly_error_message(exc)
        self.assertIn('phase6_rls_security', msg)
