"""
Validate Supabase JWT on each request and attach user to request.supabase_user.
Protects configured URL prefixes for logged-in users only.
"""
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

from apps.accounts.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class SupabaseAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_prefixes = getattr(
            settings,
            'SUPABASE_PROTECTED_URL_PREFIXES',
            (),
        )

    def __call__(self, request):
        request.supabase_user = None
        request.supabase_profile = None

        access_token = request.session.get('supabase_access_token')
        refresh_token = request.session.get('supabase_refresh_token')

        if access_token:
            self._load_user(request, access_token, refresh_token)

        if self._is_protected(request.path) and not request.supabase_user:
            login_url = reverse(settings.LOGIN_URL)
            next_param = urlencode({'next': request.get_full_path()})
            return redirect(f'{login_url}?{next_param}')

        return self.get_response(request)

    def _load_user(self, request, access_token, refresh_token):
        client = get_supabase_client()
        try:
            user_response = client.get_user(access_token)
            user = user_response.user
            if user:
                request.supabase_user = user
                request.supabase_profile = request.session.get('supabase_profile', {})
                return
        except Exception as exc:
            logger.warning('Supabase token validation failed: %s', exc)

        request.session.flush()

    def _is_protected(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.protected_prefixes)
