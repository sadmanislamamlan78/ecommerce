"""Fetch products and categories from Supabase."""
import logging
from decimal import Decimal, InvalidOperation

from apps.accounts.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# Simple select — no embed (embed often breaks PostgREST if FK not exposed)
PRODUCT_SELECT = 'id,name,slug,description,price,category_id,image_url,stock,created_at'

_last_fetch_error: str | None = None


def get_last_fetch_error() -> str | None:
    return _last_fetch_error


def _categories_map() -> dict:
    """Map category id (int and str) → category row."""
    result = {}
    for c in get_categories():
        cid = c.get('id')
        if cid is not None:
            result[cid] = c
            result[str(cid)] = c
    return result


def _normalize_product(row: dict, categories_by_id: dict | None = None) -> dict:
    if not row:
        return row
    product = dict(row)
    cat_id = product.get('category_id')
    category = {}
    if categories_by_id and cat_id is not None:
        category = categories_by_id.get(cat_id, {})
    product.pop('categories', None)
    product['category_name'] = category.get('name', '')
    product['category_slug'] = category.get('slug', '')
    try:
        product['price'] = Decimal(str(product.get('price', 0)))
    except (InvalidOperation, TypeError):
        product['price'] = Decimal('0')
    return product


def _run_product_query(client, query_builder):
    """Execute query; return rows list or raise."""
    result = query_builder.execute()
    data = result.data
    if data is None:
        return []
    if isinstance(data, dict):
        return [data]
    return data


def get_categories() -> list[dict]:
    global _last_fetch_error
    try:
        client = get_supabase_client()
        result = (
            client.table('categories')
            .select('id,name,slug,description')
            .order('name')
            .execute()
        )
        return result.data or []
    except Exception as exc:
        _last_fetch_error = str(exc)
        logger.error('Failed to fetch categories: %s', exc)
        return []


def get_category_by_slug(slug: str) -> dict | None:
    try:
        client = get_supabase_client()
        result = (
            client.table('categories')
            .select('id,name,slug')
            .eq('slug', slug)
            .maybe_single()
            .execute()
        )
        return result.data
    except Exception as exc:
        logger.error('Failed to fetch category %s: %s', slug, exc)
        return None


def get_products(
    search: str = '',
    category_slug: str = '',
    min_price: str | None = None,
    max_price: str | None = None,
) -> list[dict]:
    global _last_fetch_error
    _last_fetch_error = None
    categories_by_id = _categories_map()

    try:
        client = get_supabase_client()

        def build_query(with_order: bool = True):
            query = client.table('products').select(PRODUCT_SELECT)
            if with_order:
                query = query.order('created_at', desc=True)

            if category_slug:
                category = get_category_by_slug(category_slug)
                if category:
                    query = query.eq('category_id', int(category['id']))
                else:
                    return []

            if search:
                query = query.ilike('name', f'*{search.strip()}*')

            min_val = _parse_price(min_price)
            max_val = _parse_price(max_price)
            if min_val is not None:
                query = query.gte('price', min_val)
            if max_val is not None:
                query = query.lte('price', max_val)
            return query

        rows = []
        for with_order in (True, False):
            try:
                query = build_query(with_order=with_order)
                if query is None:
                    return []
                rows = _run_product_query(client, query)
                break
            except Exception as inner:
                if not with_order:
                    raise inner
                logger.warning('Product query with order failed, retrying: %s', inner)

        return [_normalize_product(row, categories_by_id) for row in rows]

    except Exception as exc:
        _last_fetch_error = str(exc)
        logger.error('Failed to fetch products: %s', exc)
        return []


def get_product_by_slug(slug: str) -> dict | None:
    global _last_fetch_error
    categories_by_id = _categories_map()
    try:
        client = get_supabase_client()
        result = (
            client.table('products')
            .select(PRODUCT_SELECT)
            .eq('slug', slug)
            .maybe_single()
            .execute()
        )
        if result.data:
            return _normalize_product(result.data, categories_by_id)
        return None
    except Exception as exc:
        _last_fetch_error = str(exc)
        logger.error('Failed to fetch product %s: %s', slug, exc)
        return None


def get_featured_products(limit: int = 4) -> list[dict]:
    return get_products()[:limit] if limit else get_products()


def get_price_range() -> tuple[int, int]:
    products = get_products()
    if not products:
        return 0, 5000
    prices = [float(p['price']) for p in products]
    return int(min(prices)), int(max(prices))


def _parse_price(value: str | None) -> float | None:
    if value is None or value == '':
        return None
    try:
        price = float(value)
        return price if price >= 0 else None
    except (ValueError, TypeError):
        return None
