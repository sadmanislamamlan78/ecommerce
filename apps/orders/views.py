"""Order views (Phase 4)."""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.decorators import supabase_login_required
from apps.orders.forms import CheckoutForm
from apps.common.errors import friendly_error_message
from apps.orders.services import _extract_error, place_order



@supabase_login_required
@require_http_methods(['GET', 'POST'])
def checkout_view(request):
    from apps.cart.views import _get_fresh_cart_items

    cart_items, subtotal, tax, grand_total = _get_fresh_cart_items(request)

    if not cart_items:
        messages.warning(request, 'Your cart is empty. Please add items to your cart first.')
        return redirect('products:shop')

    profile = request.session.get('supabase_profile', {})
    form = CheckoutForm(request.POST or None, initial={
        'full_name': profile.get('full_name', ''),
        'phone': profile.get('phone', ''),
        'address': profile.get('address', ''),
    })

    if request.method == 'POST' and form.is_valid():
        payment_label = dict(CheckoutForm.PAYMENT_CHOICES).get(
            form.cleaned_data['payment_method'],
            form.cleaned_data['payment_method'],
        )
        shipping_info = (
            f"Name: {form.cleaned_data['full_name']}\n"
            f"Phone: {form.cleaned_data['phone']}\n"
            f"Address: {form.cleaned_data['address']}\n"
            f"Payment: {payment_label}"
        )

        user_id = request.session.get('supabase_user_id')
        token = request.session.get('supabase_access_token')
        refresh = request.session.get('supabase_refresh_token', '')

        from apps.accounts.supabase_client import get_authenticated_client

        try:
            client = get_authenticated_client(token, refresh)
            order_id = place_order(
                client,
                user_id,
                cart_items,
                subtotal,
                tax,
                grand_total,
                shipping_info,
            )

            new_profile = {
                'full_name': form.cleaned_data['full_name'],
                'phone': form.cleaned_data['phone'],
                'address': form.cleaned_data['address'],
            }
            if new_profile != profile:
                try:
                    client.table('profiles').upsert({'id': str(user_id), **new_profile}).execute()
                    request.session['supabase_profile'] = new_profile
                    request.session.modified = True
                except Exception as exc:
                    logger_msg = _extract_error(exc)
                    messages.warning(request, f'Order saved, but profile update failed: {logger_msg}')

            request.session['cart'] = {}
            request.session.modified = True

            messages.success(request, f'Thank you! Your order #{order_id} has been placed successfully.')
            return redirect('orders:history')

        except Exception as exc:
            messages.error(request, friendly_error_message(exc, context='Checkout failed'))

    elif request.method == 'POST':
        messages.error(request, 'Please correct the errors below before placing your order.')

    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'grand_total': grand_total,
    })


@supabase_login_required
@require_http_methods(['GET'])
def order_history_view(request):
    user_id = str(request.session.get('supabase_user_id', '')).strip()
    token = request.session.get('supabase_access_token')
    refresh = request.session.get('supabase_refresh_token', '')

    from apps.accounts.supabase_client import get_authenticated_client
    from apps.orders.services import _extract_error

    orders = []
    try:
        client = get_authenticated_client(token, refresh)
        orders_result = (
            client.table('orders')
            .select('*')
            .eq('user_id', user_id)
            .order('created_at', desc=True)
            .execute()
        )
        orders = orders_result.data or []

        if orders:
            order_ids = [o['id'] for o in orders]
            items_result = (
                client.table('order_items')
                .select('id,order_id,product_id,quantity,price')
                .in_('order_id', order_ids)
                .execute()
            )
            items = items_result.data or []

            product_ids = list({it['product_id'] for it in items if it.get('product_id')})
            products_map = {}
            if product_ids:
                products_result = (
                    client.table('products')
                    .select('id,name,image_url,slug')
                    .in_('id', product_ids)
                    .execute()
                )
                if products_result.data:
                    products_map = {p['id']: p for p in products_result.data}

            from collections import defaultdict
            items_by_order = defaultdict(list)
            for it in items:
                prod = products_map.get(it['product_id']) or {}
                it['product_name'] = prod.get('name', 'Product')
                it['product_image'] = prod.get('image_url', '')
                it['product_slug'] = prod.get('slug', '')
                items_by_order[it['order_id']].append(it)

            for o in orders:
                o['items'] = items_by_order[o['id']]
                o['total_qty'] = sum(item['quantity'] for item in o['items'])

    except Exception as exc:
        messages.error(request, friendly_error_message(exc, context='Order history'))

    return render(request, 'orders/history.html', {'orders': orders})
