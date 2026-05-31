"""Shopping cart views — session-based (Phase 3)."""
from decimal import Decimal

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.common.validators import clamp_cart_quantity

def _get_cart(request):
    return request.session.get('cart', {})


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def _get_fresh_cart_items(request):
    """
    Fetch fresh pricing and stock from Supabase for all products in the session cart.
    Updates the session cart if price or stock changes, and returns the list of items
    with totals computed.
    """
    cart = _get_cart(request)
    if not cart:
        return [], Decimal('0.00'), Decimal('0.00'), Decimal('0.00')

    from apps.accounts.supabase_client import get_supabase_client

    product_ids = []
    for pid in cart.keys():
        try:
            product_ids.append(int(pid))
        except ValueError:
            continue

    fresh_products = {}
    if product_ids:
        try:
            client = get_supabase_client()
            result = (
                client.table('products')
                .select('id,name,slug,price,image_url,stock')
                .in_('id', product_ids)
                .execute()
            )
            if result.data:
                for prod in result.data:
                    fresh_products[str(prod['id'])] = prod
        except Exception:
            # Fallback to session data if Supabase is unreachable
            pass

    cart_items = []
    subtotal = Decimal('0.00')
    cart_updated = False
    keys_to_remove = []

    for key, item in list(cart.items()):
        # Handle case where item was stored as simple integer count (backwards compatibility)
        if isinstance(item, int):
            item = {'quantity': item, 'product_id': key}

        prod_id = str(item.get('product_id') or key)
        fresh_prod = fresh_products.get(prod_id)

        # If we successfully queried Supabase but this product wasn't returned, it was deleted
        if not fresh_prod and fresh_products:
            keys_to_remove.append(key)
            cart_updated = True
            continue

        name = fresh_prod.get('name') if fresh_prod else item.get('name', 'Product')
        slug = fresh_prod.get('slug') if fresh_prod else item.get('slug', '')
        image_url = fresh_prod.get('image_url') if fresh_prod else item.get('image_url', '')

        try:
            price_str = str(fresh_prod.get('price')) if fresh_prod else str(item.get('price', 0))
            price = Decimal(price_str)
        except Exception:
            price = Decimal('0.00')

        stock = fresh_prod.get('stock', 0) if fresh_prod else item.get('stock', 99)
        if stock is None:
            stock = 0

        qty = int(item.get('quantity', 1))
        # Clamp quantity to stock
        if qty > stock:
            qty = stock
            cart_updated = True
        if qty < 1 and stock > 0:
            qty = 1
            cart_updated = True

        if stock == 0:
            qty = 0
            cart_updated = True

        item_subtotal = price * qty
        subtotal += item_subtotal

        # Update session cart content
        cart[key] = {
            'product_id': prod_id,
            'name': name,
            'slug': slug,
            'price': str(price),
            'image_url': image_url,
            'quantity': qty,
            'stock': stock,
        }

        cart_items.append({
            'product_id': prod_id,
            'name': name,
            'slug': slug,
            'price': price,
            'image_url': image_url,
            'quantity': qty,
            'stock': stock,
            'subtotal': item_subtotal,
        })

    for key in keys_to_remove:
        cart.pop(key, None)

    if cart_updated or keys_to_remove:
        request.session['cart'] = cart
        request.session.modified = True

    tax = subtotal * Decimal('0.05')  # 5% VAT
    grand_total = subtotal + tax

    return cart_items, subtotal, tax, grand_total


@require_http_methods(['GET'])
def cart_view(request):
    cart_items, subtotal, tax, grand_total = _get_fresh_cart_items(request)
    return render(request, 'cart/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'grand_total': grand_total,
    })


@require_http_methods(['POST'])
def add_to_cart_view(request, product_id):
    quantity = clamp_cart_quantity(request.POST.get('quantity', 1))
    next_url = request.POST.get('next', '/cart/')

    from apps.accounts.supabase_client import get_supabase_client

    try:
        client = get_supabase_client()
        result = (
            client.table('products')
            .select('id,name,slug,price,image_url,stock')
            .eq('id', product_id)
            .maybe_single()
            .execute()
        )
        product = result.data
    except Exception:
        product = None

    if not product:
        msg = 'Product not found.'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
            return JsonResponse({'success': False, 'message': msg}, status=404)
        messages.error(request, msg)
        return redirect('products:shop')

    stock = product.get('stock', 0) or 0
    if stock < quantity:
        msg = f'Only {stock} items available in stock.'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(next_url if next_url.startswith('/') else 'products:shop')

    cart = _get_cart(request)
    key = str(product_id)
    existing = cart.get(key, {})
    if isinstance(existing, dict):
        new_qty = existing.get('quantity', 0) + quantity
    else:
        new_qty = (existing if isinstance(existing, int) else 0) + quantity

    new_qty = min(new_qty, stock)
    cart[key] = {
        'product_id': product_id,
        'name': product.get('name', ''),
        'slug': product.get('slug', ''),
        'price': str(product.get('price', 0)),
        'image_url': product.get('image_url', ''),
        'quantity': new_qty,
        'stock': stock,
    }
    _save_cart(request, cart)

    cart_count = sum(item.get('quantity', 0) if isinstance(item, dict) else item for item in cart.values())
    msg = f'Added {product.get("name")} to cart.'

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'message': msg,
            'cart_count': cart_count,
        })

    messages.success(request, msg)
    return redirect(next_url if next_url.startswith('/') else '/cart/')


@require_http_methods(['POST'])
def update_cart_view(request, product_id):
    quantity = clamp_cart_quantity(request.POST.get('quantity', 1))

    from apps.accounts.supabase_client import get_supabase_client

    try:
        client = get_supabase_client()
        result = (
            client.table('products')
            .select('id,name,stock,price')
            .eq('id', product_id)
            .maybe_single()
            .execute()
        )
        product = result.data
    except Exception:
        product = None

    if not product:
        msg = 'Product not found.'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=404)
        messages.error(request, msg)
        return redirect('cart:cart')

    stock = product.get('stock', 0) or 0
    warning_msg = None
    if quantity > stock:
        quantity = stock
        warning_msg = f'Only {stock} items available in stock.'

    cart = _get_cart(request)
    key = str(product_id)
    if key in cart:
        if isinstance(cart[key], dict):
            cart[key]['quantity'] = quantity
        else:
            cart[key] = quantity
        _save_cart(request, cart)
        if warning_msg:
            messages.warning(request, warning_msg)
        else:
            messages.success(request, 'Cart updated.')

    cart_items, subtotal, tax, grand_total = _get_fresh_cart_items(request)
    cart_count = sum(item['quantity'] for item in cart_items)

    item_subtotal = Decimal('0.00')
    for item in cart_items:
        if str(item['product_id']) == str(product_id):
            item_subtotal = item['subtotal']
            break

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': warning_msg or 'Cart updated.',
            'cart_count': cart_count,
            'quantity': quantity,
            'item_subtotal': f"{item_subtotal:.2f}",
            'subtotal': f"{subtotal:.2f}",
            'tax': f"{tax:.2f}",
            'grand_total': f"{grand_total:.2f}",
            'warning': bool(warning_msg)
        })

    return redirect('cart:cart')


@require_http_methods(['POST'])
def remove_from_cart_view(request, product_id):
    cart = _get_cart(request)
    key = str(product_id)
    removed_name = 'Item'
    if key in cart:
        item = cart.pop(key)
        if isinstance(item, dict):
            removed_name = item.get('name', 'Item')
        _save_cart(request, cart)
        messages.success(request, f'Removed {removed_name} from cart.')

    cart_items, subtotal, tax, grand_total = _get_fresh_cart_items(request)
    cart_count = sum(item['quantity'] for item in cart_items)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Removed {removed_name} from cart.',
            'cart_count': cart_count,
            'subtotal': f"{subtotal:.2f}",
            'tax': f"{tax:.2f}",
            'grand_total': f"{grand_total:.2f}",
        })

    return redirect('cart:cart')
