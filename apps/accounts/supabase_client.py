"""
Supabase REST client for Auth and database (no supabase-py — works on Python 3.11–3.14).
"""
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Optional

import certifi
import requests
from django.conf import settings


class SupabaseConfigError(Exception):
    """Raised when required Supabase environment variables are missing."""


_SSL_BOOTSTRAPPED = False


def _bootstrap_ssl() -> None:
    """Use Windows/macOS certificate store (fixes Python 3.14 SSL on Windows)."""
    global _SSL_BOOTSTRAPPED
    if _SSL_BOOTSTRAPPED:
        return
    _SSL_BOOTSTRAPPED = True
    if not getattr(settings, 'SUPABASE_SSL_VERIFY', True):
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return
    try:
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass


def _ssl_verify():
    """What to pass to requests as verify= (False, True, or CA file path)."""
    _bootstrap_ssl()
    if not getattr(settings, 'SUPABASE_SSL_VERIFY', True):
        return False
    try:
        import truststore
        truststore.inject_into_ssl()
        return True
    except ImportError:
        pass
    try:
        return certifi.where()
    except Exception:
        return True


def _request(method: str, url: str, **kwargs) -> requests.Response:
    """HTTP request to Supabase with SSL configured for Windows dev."""
    kwargs.setdefault('timeout', 30)
    if 'verify' not in kwargs:
        kwargs['verify'] = _ssl_verify()
    return requests.request(method, url, **kwargs)


@dataclass
class SupabaseUser:
    id: str
    email: Optional[str] = None
    app_metadata: Optional[dict] = None
    user_metadata: Optional[dict] = None


@dataclass
class SupabaseSession:
    access_token: str
    refresh_token: str


@dataclass
class AuthResponse:
    user: Optional[SupabaseUser]
    session: Optional[SupabaseSession]


def _normalize_supabase_url(url: str) -> str:
    """Accept Project URL only — strip accidental /rest/v1 suffix from dashboard."""
    base = url.strip().rstrip('/')
    for suffix in ('/rest/v1', '/auth/v1'):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
    if base.endswith('.supabase.co'):
        return base
    raise SupabaseConfigError(
        'SUPABASE_URL must be your Project URL, e.g. https://abcdefgh.supabase.co '
        '(do not include /rest/v1). Find it in Project Settings → API → Project URL.'
    )


def _validate_config() -> tuple[str, str]:
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise SupabaseConfigError(
            'SUPABASE_URL and SUPABASE_ANON_KEY must be set in your .env file. '
            'Find them in Supabase Dashboard → Project Settings → API.'
        )
    return _normalize_supabase_url(settings.SUPABASE_URL), settings.SUPABASE_ANON_KEY


def _headers(api_key: str, access_token: str = '') -> dict[str, str]:
    headers = {
        'apikey': api_key,
        'Content-Type': 'application/json',
    }
    token = access_token or api_key
    headers['Authorization'] = f'Bearer {token}'
    return headers


def _parse_user(data: dict) -> SupabaseUser:
    return SupabaseUser(
        id=str(data.get('id', '')),
        email=data.get('email'),
        app_metadata=data.get('app_metadata') or {},
        user_metadata=data.get('user_metadata') or {},
    )


def _parse_auth_response(payload: dict) -> AuthResponse:
    user_data = payload.get('user')
    user = _parse_user(user_data) if user_data else None
    session = None
    access = payload.get('access_token')
    refresh = payload.get('refresh_token')
    if access and refresh:
        session = SupabaseSession(access_token=access, refresh_token=refresh)
    elif user_data and user_data.get('id') and access:
        session = SupabaseSession(
            access_token=access,
            refresh_token=refresh or access,
        )
    return AuthResponse(user=user, session=session)


class SupabaseAuthClient:
    """Thin wrapper around Supabase GoTrue REST API."""

    def __init__(self, url: str = '', anon_key: str = ''):
        base_url, key = _validate_config()
        self.base_url = url or base_url
        self.anon_key = anon_key or key
        self.auth_url = f'{self.base_url}/auth/v1'
        self.rest_url = f'{self.base_url}/rest/v1'

    def sign_up(self, payload: dict) -> AuthResponse:
        body = {
            'email': payload['email'],
            'password': payload['password'],
        }
        if payload.get('options', {}).get('data'):
            body['data'] = payload['options']['data']

        response = _request(
            'POST',
            f'{self.auth_url}/signup',
            headers=_headers(self.anon_key),
            json=body,
        )
        self._raise_for_status(response)
        return _parse_auth_response(response.json())

    def sign_in_with_password(self, payload: dict) -> AuthResponse:
        response = _request(
            'POST',
            f'{self.auth_url}/token?grant_type=password',
            headers=_headers(self.anon_key),
            json={
                'email': payload['email'],
                'password': payload['password'],
            },
        )
        self._raise_for_status(response)
        return _parse_auth_response(response.json())

    def sign_out(self, access_token: str) -> None:
        _request(
            'POST',
            f'{self.auth_url}/logout',
            headers=_headers(self.anon_key, access_token),
        )

    def get_user(self, access_token: str) -> AuthResponse:
        response = _request(
            'GET',
            f'{self.auth_url}/user',
            headers=_headers(self.anon_key, access_token),
        )
        self._raise_for_status(response)
        user = _parse_user(response.json())
        return AuthResponse(user=user, session=None)

    def table(self, name: str):
        return SupabaseTable(self, name)

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        if response.ok:
            return
        try:
            detail = response.json()
            message = (
                detail.get('msg')
                or detail.get('error_description')
                or detail.get('message')
                or str(detail)
            )
        except Exception:
            message = response.text or response.reason
        raise requests.HTTPError(message, response=response)


class SupabaseTable:
    def __init__(self, client: SupabaseAuthClient, name: str):
        self.client = client
        self.name = name
        self._filters: list[tuple[str, str]] = []
        self._single = False
        self._payload: Optional[dict | list] = None
        self._method = 'GET'
        self._columns = '*'
        self._order: Optional[str] = None
        self._limit: Optional[int] = None

    def select(self, columns: str):
        self._columns = columns
        return self

    def eq(self, column: str, value: Any):
        self._filters.append((column, f'eq.{value}'))
        return self

    def ilike(self, column: str, pattern: str):
        self._filters.append((column, f'ilike.{pattern}'))
        return self

    def gte(self, column: str, value: Any):
        self._filters.append((column, f'gte.{value}'))
        return self

    def lte(self, column: str, value: Any):
        self._filters.append((column, f'lte.{value}'))
        return self

    def order(self, column: str, desc: bool = False):
        self._order = f'{column}.{"desc" if desc else "asc"}'
        return self

    def limit(self, count: int):
        self._limit = count
        return self

    def maybe_single(self):
        self._single = True
        return self

    def upsert(self, data: dict):
        self._method = 'UPSERT'
        self._payload = data
        return self

    def insert(self, data: dict | list):
        self._method = 'INSERT'
        self._payload = data
        return self

    def update(self, data: dict):
        self._method = 'UPDATE'
        self._payload = data
        return self

    def delete(self):
        self._method = 'DELETE'
        return self

    def in_(self, column: str, values: list):
        vals_str = ','.join(str(v) for v in values)
        self._filters.append((column, f'in.({vals_str})'))
        return self

    def execute(self):
        headers = _headers(self.client.anon_key, self._token)
        url = f'{self.client.rest_url}/{self.name}'

        if self._method == 'UPSERT':
            headers['Prefer'] = 'resolution=merge-duplicates,return=representation'
            response = _request(
                'POST',
                url,
                headers=headers,
                json=self._payload,
            )
            SupabaseAuthClient._raise_for_status(response)
            data = response.json()
            if isinstance(data, list) and data:
                data = data[0]
            return QueryResult(data)

        if self._method == 'INSERT':
            headers['Prefer'] = 'return=representation'
            response = _request(
                'POST',
                url,
                headers=headers,
                json=self._payload,
            )
            SupabaseAuthClient._raise_for_status(response)
            data = response.json()
            return QueryResult(data)

        params = {}
        if self._method == 'GET':
            params['select'] = self._columns
        for col, val in self._filters:
            params[col] = val
        if self._order:
            params['order'] = self._order
        if self._limit is not None:
            params['limit'] = str(self._limit)

        if self._method == 'UPDATE':
            headers['Prefer'] = 'return=representation'
            response = _request(
                'PATCH',
                url,
                headers=headers,
                json=self._payload,
                params=params,
            )
            SupabaseAuthClient._raise_for_status(response)
            data = response.json()
            return QueryResult(data)

        if self._method == 'DELETE':
            headers['Prefer'] = 'return=representation'
            response = _request(
                'DELETE',
                url,
                headers=headers,
                params=params,
            )
            SupabaseAuthClient._raise_for_status(response)
            data = response.json()
            return QueryResult(data)

        # GET request
        response = _request('GET', url, headers=headers, params=params)
        SupabaseAuthClient._raise_for_status(response)
        rows = response.json()
        if self._single:
            data = rows[0] if rows else None
        else:
            data = rows
        return QueryResult(data)

    @property
    def _token(self) -> str:
        return getattr(self, '_access_token', '')


@dataclass
class QueryResult:
    data: Any


class AuthenticatedClient(SupabaseAuthClient):
    def __init__(self, access_token: str, refresh_token: str = ''):
        super().__init__()
        self.access_token = access_token
        self.refresh_token = refresh_token

    def table(self, name: str):
        table = super().table(name)
        table._access_token = self.access_token
        return table


@lru_cache(maxsize=1)
def get_supabase_client() -> SupabaseAuthClient:
    return SupabaseAuthClient()


def get_authenticated_client(access_token: str, refresh_token: str = '') -> AuthenticatedClient:
    return AuthenticatedClient(access_token, refresh_token)
