"""Checkout and order helpers for Supabase."""
import logging

from apps.common.errors import extract_error_message, friendly_error_message

logger = logging.getLogger(__name__)


def _extract_error(exc: Exception) -> str:
    return extract_error_message(exc)


def _friendly_error(exc: Exception, *, context: str = '') -> str:
    return friendly_error_message(exc, context=context)


def place_order(client, user_id: str, cart_items, subtotal, tax, grand_total, shipping_info: str) -> int:
    """
    Create order + order_items in Supabase. Returns order id.
    Stock updates are best-effort (checkout still succeeds if stock update fails).
    """
    user_id = str(user_id).strip()
    if not user_id:
        raise ValueError('You must be logged in to place an order.')

    order_payload = {
        'user_id': user_id,
        'total_amount': float(grand_total),
        'shipping_address': shipping_info,
        'status': 'pending',
    }

    order_result = client.table('orders').insert(order_payload).execute()
    if not order_result.data:
        raise ValueError('Order could not be saved. Check Supabase RLS policies for orders table.')

    order_data = order_result.data
    if isinstance(order_data, list):
        if not order_data:
            raise ValueError('Order insert returned no data.')
        order_id = order_data[0]['id']
    else:
        order_id = order_data['id']

    order_items_payload = [
        {
            'order_id': order_id,
            'product_id': int(item['product_id']),
            'quantity': int(item['quantity']),
            'price': float(item['price']),
        }
        for item in cart_items
    ]

    try:
        client.table('order_items').insert(order_items_payload).execute()
    except Exception as exc:
        logger.error('Bulk order_items insert failed, retrying one-by-one: %s', exc)
        for row in order_items_payload:
            client.table('order_items').insert(row).execute()

    for item in cart_items:
        try:
            client.rpc(
                'decrement_product_stock',
                {
                    'p_product_id': int(item['product_id']),
                    'p_quantity': int(item['quantity']),
                },
            ).execute()
        except Exception as exc:
            logger.warning(
                'Stock update failed for product %s: %s',
                item.get('product_id'),
                _friendly_error(exc, context='Stock update'),
            )

    return order_id
