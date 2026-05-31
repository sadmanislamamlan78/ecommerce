"""Admin CRUD operations for products in Supabase."""
import logging
import re

from apps.accounts.supabase_client import get_authenticated_client
from apps.products.services import PRODUCT_SELECT, _normalize_product

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')[:80]


def _admin_client(request):
    token = request.session['supabase_access_token']
    refresh = request.session.get('supabase_refresh_token', '')
    return get_authenticated_client(token, refresh)


def list_all_products(request) -> list[dict]:
    try:
        client = _admin_client(request)
        result = (
            client.table('products')
            .select(PRODUCT_SELECT)
            .order('created_at', desc=True)
            .execute()
        )
        rows = result.data or []
        from apps.products.services import _categories_map
        cats = _categories_map()
        return [_normalize_product(r, cats) for r in rows]
    except Exception as exc:
        logger.error('Admin list products failed: %s', exc)
        return []


def get_product_by_id(request, product_id: int) -> dict | None:
    try:
        client = _admin_client(request)
        result = (
            client.table('products')
            .select(PRODUCT_SELECT)
            .eq('id', int(product_id))
            .maybe_single()
            .execute()
        )
        if result.data:
            from apps.products.services import _categories_map
            return _normalize_product(result.data, _categories_map())
        return None
    except Exception as exc:
        logger.error('Admin get product %s failed: %s', product_id, exc)
        return None


def _unique_slug(client, base_slug: str, exclude_id: int | None = None) -> str:
    slug = base_slug or 'product'
    candidate = slug
    n = 1
    while True:
        query = client.table('products').select('id').eq('slug', candidate)
        result = query.maybe_single().execute()
        existing = result.data
        if not existing or (exclude_id and existing.get('id') == exclude_id):
            return candidate
        n += 1
        candidate = f'{slug}-{n}'


def create_product(request, data: dict) -> dict:
    client = _admin_client(request)
    slug = data.get('slug') or slugify(data['name'])
    slug = _unique_slug(client, slug)
    payload = {
        'name': data['name'],
        'slug': slug,
        'description': data.get('description', ''),
        'price': float(data['price']),
        'category_id': int(data['category_id']),
        'image_url': data.get('image_url') or '',
        'stock': int(data.get('stock', 0)),
    }
    result = client.table('products').insert(payload).execute()
    rows = result.data
    if isinstance(rows, list) and rows:
        from apps.products.services import _categories_map
        return _normalize_product(rows[0], _categories_map())
    raise ValueError('Product could not be created. Check staff permissions (phase5_admin.sql).')


def update_product(request, product_id: int, data: dict) -> dict:
    client = _admin_client(request)
    slug = data.get('slug') or slugify(data['name'])
    slug = _unique_slug(client, slug, exclude_id=int(product_id))
    payload = {
        'name': data['name'],
        'slug': slug,
        'description': data.get('description', ''),
        'price': float(data['price']),
        'category_id': int(data['category_id']),
        'image_url': data.get('image_url') or '',
        'stock': int(data.get('stock', 0)),
    }
    result = (
        client.table('products')
        .update(payload)
        .eq('id', int(product_id))
        .execute()
    )
    rows = result.data
    if isinstance(rows, list) and rows:
        from apps.products.services import _categories_map
        return _normalize_product(rows[0], _categories_map())
    if isinstance(rows, dict):
        from apps.products.services import _categories_map
        return _normalize_product(rows, _categories_map())
    raise ValueError('Product could not be updated.')


def delete_product(request, product_id: int) -> None:
    client = _admin_client(request)
    client.table('products').delete().eq('id', int(product_id)).execute()
