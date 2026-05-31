"""Reusable input validation helpers (Phase 6)."""
import re
from decimal import Decimal, InvalidOperation

NAME_PATTERN = re.compile(r"^[\w\s\-\.']+$", re.UNICODE)
PHONE_PATTERN = re.compile(r'^[\d\+\-\s\(\)]{7,20}$')
SLUG_PATTERN = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

MAX_SEARCH_LEN = 100
MAX_ADDRESS_LEN = 500
MAX_DESCRIPTION_LEN = 5000
MAX_IMAGE_BYTES = 5 * 1024 * 1024
CART_QTY_MIN = 1
CART_QTY_MAX = 99


def validate_person_name(name: str, *, field_label: str = 'Name') -> str:
    name = (name or '').strip()
    if len(name) < 2:
        raise ValueError(f'{field_label} must be at least 2 characters.')
    if len(name) > 120:
        raise ValueError(f'{field_label} is too long (max 120 characters).')
    if not NAME_PATTERN.match(name):
        raise ValueError(f'{field_label} contains invalid characters.')
    return name


def validate_phone(phone: str, *, required: bool = False) -> str:
    phone = (phone or '').strip()
    if not phone:
        if required:
            raise ValueError('Phone number is required.')
        return ''
    if not PHONE_PATTERN.match(phone):
        raise ValueError('Enter a valid phone number (7–20 digits).')
    return phone


def validate_address(address: str, *, required: bool = False) -> str:
    address = (address or '').strip()
    if not address:
        if required:
            raise ValueError('Shipping address is required.')
        return ''
    if len(address) < 10:
        raise ValueError('Please enter a complete delivery address (at least 10 characters).')
    if len(address) > MAX_ADDRESS_LEN:
        raise ValueError(f'Address is too long (max {MAX_ADDRESS_LEN} characters).')
    return address


def validate_search_query(query: str) -> str:
    query = (query or '').strip()
    if len(query) > MAX_SEARCH_LEN:
        query = query[:MAX_SEARCH_LEN]
    return query


def validate_category_slug(slug: str, allowed: set[str] | None = None) -> str:
    slug = (slug or '').strip().lower()
    if not slug:
        return ''
    if not SLUG_PATTERN.match(slug):
        return ''
    if allowed is not None and slug not in allowed:
        return ''
    return slug


def parse_price_filter(value: str | None) -> int | None:
    if value is None or str(value).strip() == '':
        return None
    try:
        price = int(Decimal(str(value).strip()))
    except (InvalidOperation, ValueError):
        return None
    return max(0, min(price, 9_999_999))


def clamp_cart_quantity(raw, *, default: int = 1) -> int:
    try:
        qty = int(raw)
    except (TypeError, ValueError):
        qty = default
    return max(CART_QTY_MIN, min(qty, CART_QTY_MAX))


def validate_image_upload(file_obj) -> None:
    if not file_obj:
        return
    content_type = getattr(file_obj, 'content_type', '') or ''
    if content_type and not content_type.startswith('image/'):
        raise ValueError('Please upload a valid image (JPEG, PNG, WebP, or GIF).')
    size = getattr(file_obj, 'size', None)
    if size is None and hasattr(file_obj, 'seek') and hasattr(file_obj, 'tell'):
        pos = file_obj.tell()
        file_obj.seek(0, 2)
        size = file_obj.tell()
        file_obj.seek(pos)
    if size is not None and size > MAX_IMAGE_BYTES:
        raise ValueError('Image must be smaller than 5 MB.')
