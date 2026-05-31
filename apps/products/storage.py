"""Upload product images to Supabase Storage."""
import mimetypes
import re
import uuid
from pathlib import Path

from django.conf import settings

from apps.accounts.supabase_client import _headers, _request


class StorageUploadError(Exception):
    pass


def _storage_base_url() -> str:
    url = settings.SUPABASE_URL.rstrip('/')
    for suffix in ('/rest/v1', '/auth/v1', '/storage/v1'):
        if url.endswith(suffix):
            url = url[: -len(suffix)]
    return url


def _bucket() -> str:
    return getattr(settings, 'SUPABASE_STORAGE_BUCKET', 'product-images')


def _safe_filename(name: str) -> str:
    base = Path(name).name
    base = re.sub(r'[^a-zA-Z0-9._-]', '-', base)
    return base[:80] or 'image.jpg'


def public_url(storage_path: str) -> str:
    return f'{_storage_base_url()}/storage/v1/object/public/{_bucket()}/{storage_path}'


def upload_product_image(file_obj, access_token: str, product_slug: str = '') -> str:
    """
    Upload image file to Supabase Storage. Returns public URL.
    Uses the staff user's JWT (must have storage INSERT policy).
    """
    if not file_obj:
        raise StorageUploadError('No image file provided.')

    content_type = getattr(file_obj, 'content_type', '') or mimetypes.guess_type(file_obj.name)[0]
    if not content_type or not content_type.startswith('image/'):
        raise StorageUploadError('Please upload a valid image (JPEG, PNG, WebP, or GIF).')

    ext = mimetypes.guess_extension(content_type) or '.jpg'
    if ext == '.jpe':
        ext = '.jpg'
    slug_part = re.sub(r'[^a-z0-9-]', '', (product_slug or 'product').lower())[:40]
    storage_path = f'{slug_part}/{uuid.uuid4().hex}{ext}'

    file_bytes = file_obj.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise StorageUploadError('Image must be smaller than 5 MB.')

    url = f'{_storage_base_url()}/storage/v1/object/{_bucket()}/{storage_path}'
    headers = _headers(settings.SUPABASE_ANON_KEY, access_token)
    headers['Content-Type'] = content_type
    headers['x-upsert'] = 'true'

    response = _request('POST', url, headers=headers, data=file_bytes)

    if not response.ok:
        # Retry with service role if configured (server-side only)
        if settings.SUPABASE_SERVICE_ROLE_KEY:
            headers = _headers(settings.SUPABASE_ANON_KEY, settings.SUPABASE_SERVICE_ROLE_KEY)
            headers['Content-Type'] = content_type
            headers['x-upsert'] = 'true'
            response = _request('POST', url, headers=headers, data=file_bytes)

    if not response.ok:
        try:
            detail = response.json().get('message') or response.json().get('error')
        except Exception:
            detail = response.text
        raise StorageUploadError(detail or 'Image upload failed. Create the product-images bucket in Supabase.')

    return public_url(storage_path)
