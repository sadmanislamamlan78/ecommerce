"""View decorators for Supabase-authenticated routes."""
from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def supabase_login_required(view_func):
    """Redirect anonymous users to login with ?next= return URL."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(request, 'supabase_user', None):
            messages.warning(request, 'Please sign in to access that page.')
            login_url = reverse('accounts:login')
            next_url = request.get_full_path()
            return redirect(f'{login_url}?{urlencode({"next": next_url})}')
        return view_func(request, *args, **kwargs)

    return wrapper


def staff_required(view_func):
    """Require staff flag in session (set during login from profiles metadata)."""

    @wraps(view_func)
    @supabase_login_required
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_staff'):
            messages.error(request, 'You do not have permission to access that area.')
            return redirect('products:home')
        return view_func(request, *args, **kwargs)

    return wrapper
