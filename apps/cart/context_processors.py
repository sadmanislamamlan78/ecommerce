"""Expose cart item count to all templates."""


def cart_context(request):
    cart = request.session.get('cart', {})
    count = 0
    for item in cart.values():
        if isinstance(item, dict):
            count += item.get('quantity', 0)
        elif isinstance(item, int):
            count += item
    return {'cart_count': count}
