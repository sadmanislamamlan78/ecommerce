"""User-friendly error messages for Supabase and Django (Phase 6)."""
from __future__ import annotations


def extract_error_message(exc: Exception) -> str:
    """Return the best available message from an API or Python exception."""
    if hasattr(exc, 'response') and exc.response is not None:
        try:
            detail = exc.response.json()
            if isinstance(detail, dict):
                return (
                    detail.get('message')
                    or detail.get('msg')
                    or detail.get('hint')
                    or detail.get('details')
                    or detail.get('error_description')
                    or str(detail)
                )
        except Exception:
            return exc.response.text or str(exc)
    return str(exc).strip() or 'An unexpected error occurred.'


def friendly_error_message(exc: Exception, *, context: str = '') -> str:
    """
    Map low-level database/API errors to messages suitable for end users.
    """
    raw = extract_error_message(exc)
    lower = raw.lower()
    prefix = f'{context}: ' if context else ''

    if 'permission denied for sequence' in lower and 'products_id_seq' in lower:
        return (
            f'{prefix}Could not save product (database permissions). '
            'Run supabase/phase5_fix_product_insert.sql in Supabase SQL Editor.'
        ).strip()
    if 'permission denied for sequence' in lower:
        return (
            f'{prefix}Database sequence permission denied. '
            'Run supabase/phase6_rls_security.sql in Supabase SQL Editor.'
        ).strip()
    if 'row-level security' in lower or 'rls' in lower or 'violates row-level security' in lower:
        return (
            f'{prefix}Action blocked by security rules. '
            'Run supabase/phase6_rls_security.sql, then sign out and sign in again.'
        ).strip()
    if 'duplicate key' in lower or 'unique constraint' in lower:
        if 'slug' in lower:
            return f'{prefix}A product with this URL slug already exists. Choose a different slug.'
        return f'{prefix}This record already exists. Please use different values.'
    if 'jwt expired' in lower or 'invalid jwt' in lower:
        return f'{prefix}Your session expired. Please sign in again.'
    if 'foreign key' in lower:
        return f'{prefix}Invalid category or related data. Refresh the page and try again.'
    if 'certificate verify failed' in lower or 'ssl' in lower:
        return (
            f'{prefix}Could not connect to Supabase (SSL). '
            'Set SUPABASE_SSL_VERIFY=false in .env when DEBUG=True.'
        ).strip()
    if 'failed to establish' in lower or 'name or service not known' in lower:
        return f'{prefix}Could not reach Supabase. Check SUPABASE_URL in .env.'

    if prefix:
        return f'{prefix}{raw}'
    return raw
