"""Product catalog views — Supabase-backed shop, search, and filters."""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from apps.common.validators import (
    parse_price_filter,
    validate_category_slug,
    validate_search_query,
)
from apps.products.services import (
    get_categories,
    get_featured_products,
    get_last_fetch_error,
    get_price_range,
    get_product_by_slug,
    get_products,
)


def home_view(request):
    categories = get_categories()
    featured_products = get_featured_products(limit=4)
    return render(request, 'products/home.html', {
        'featured_products': featured_products,
        'categories': categories,
    })


@require_GET
def shop_view(request):
    categories = get_categories()
    allowed_slugs = {c['slug'] for c in categories if c.get('slug')}

    search = validate_search_query(request.GET.get('q', ''))
    category = validate_category_slug(request.GET.get('category', ''), allowed_slugs or None)

    # Only apply price filter after user clicks "Apply Filters" (not on category links)
    apply_price = request.GET.get('filter') == '1'
    min_parsed = parse_price_filter(request.GET.get('min_price')) if apply_price else None
    max_parsed = parse_price_filter(request.GET.get('max_price')) if apply_price else None
    if apply_price and min_parsed is not None and max_parsed is not None and min_parsed > max_parsed:
        min_parsed, max_parsed = max_parsed, min_parsed
        messages.info(request, 'Minimum price was greater than maximum — values were swapped.')

    min_price = str(min_parsed) if min_parsed is not None else ''
    max_price = str(max_parsed) if max_parsed is not None else ''

    products = get_products(
        search=search,
        category_slug=category,
        min_price=min_price or None,
        max_price=max_price or None,
    )
    price_min, price_max = get_price_range()

    slider_min = min_parsed if min_parsed is not None else price_min
    slider_max = max_parsed if max_parsed is not None else price_max
    slider_min = max(price_min, min(slider_min, price_max))
    slider_max = max(slider_min, min(slider_max, price_max))

    if not products and categories:
        err = get_last_fetch_error()
        if err:
            messages.warning(
                request,
                f'Could not load products from Supabase: {err}. '
                'Run supabase/phase4_fix_catalog_and_orders.sql in SQL Editor.',
            )
        elif not apply_price and not search and not category:
            messages.info(
                request,
                'No products in database. Run phase2_catalog.sql or add products in Supabase Table Editor.',
            )
        else:
            messages.info(request, 'No products match your filters. Try clearing filters.')

    return render(request, 'products/shop.html', {
        'products': products,
        'categories': categories,
        'search': search,
        'active_category': category,
        'min_price': min_price,
        'max_price': max_price,
        'price_min': price_min,
        'price_max': price_max,
        'slider_min': slider_min,
        'slider_max': slider_max,
        'result_count': len(products),
    })


@require_GET
def product_detail_view(request, slug):
    product = get_product_by_slug(slug)
    if not product:
        messages.error(request, 'Product not found.')
        return redirect('products:shop')

    related = [
        p for p in get_products(category_slug=product.get('category_slug', ''))
        if p.get('slug') != slug
    ][:4]

    return render(request, 'products/detail.html', {
        'product': product,
        'related_products': related,
    })
