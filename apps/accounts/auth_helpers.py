"""Session helpers for Supabase authentication."""
from django.contrib import messages


def store_supabase_session(request, auth_response, profile=None):
    """Persist Supabase tokens and user metadata in Django session."""
    session = auth_response.session
    user = auth_response.user

    if not session or not user:
        return False

    request.session['supabase_access_token'] = session.access_token
    request.session['supabase_refresh_token'] = session.refresh_token
    request.session['supabase_user_id'] = str(user.id)
    request.session['supabase_email'] = user.email or ''
    profile_data = profile or {}
    request.session['is_staff'] = bool(
        profile_data.get('is_staff')
        or (user.app_metadata or {}).get('is_staff')
        or (user.user_metadata or {}).get('is_staff')
    )

    request.session['supabase_profile'] = {
        'full_name': profile_data.get('full_name', ''),
        'phone': profile_data.get('phone', ''),
        'address': profile_data.get('address', ''),
    }
    request.session.modified = True
    return True


def clear_supabase_session(request):
    """Remove Supabase auth data from Django session."""
    keys = [
        'supabase_access_token',
        'supabase_refresh_token',
        'supabase_user_id',
        'supabase_email',
        'supabase_profile',
        'is_staff',
    ]
    for key in keys:
        request.session.pop(key, None)
    request.session.modified = True


def merge_session_cart_on_login(request):
    """
    Ensure the cart from the anonymous session is retained after logging in.
    Since we store user info directly in the Django session, request.session['cart']
    is naturally preserved, but this guarantees it is marked modified.
    """
    if 'cart' in request.session:
        request.session.modified = True


def get_user_display_name(request):
    profile = request.session.get('supabase_profile', {})
    return profile.get('full_name') or request.session.get('supabase_email', 'Account')


def handle_supabase_auth_error(request, error):
    """Map Supabase/Gotrue errors to user-friendly messages."""
    if hasattr(error, 'response') and error.response is not None:
        try:
            detail = error.response.json()
            message = detail.get('msg') or detail.get('error_description') or str(detail)
        except Exception:
            message = str(error)
    else:
        message = str(error)
    lower = message.lower()

    if 'invalid login credentials' in lower or 'invalid credentials' in lower:
        messages.error(request, 'Invalid email or password.')
    elif 'email not confirmed' in lower:
        messages.error(
            request,
            'Please confirm your email before signing in. '
            'Check your inbox for the Supabase confirmation link.',
        )
    elif (
        'user already registered' in lower
        or 'already been registered' in lower
        or 'already registered' in lower
        or 'email address is already registered' in lower
    ):
        messages.error(
            request,
            'An account with this email already exists. Try signing in or use a different email.',
        )
    elif 'email rate limit exceeded' in lower or 'rate limit exceeded' in lower:
        messages.error(
            request,
            'Supabase email rate limit reached (too many signups in a short time). '
            'Wait about 1 hour, or in Supabase go to Authentication → Providers → Email '
            'and turn OFF "Confirm email", then try again with a new email.',
        )
    elif 'password should be at least' in lower:
        messages.error(request, 'Password does not meet Supabase security requirements.')
    elif 'certificate verify failed' in lower or 'ssl' in lower:
        messages.error(
            request,
            'Could not connect to Supabase (SSL certificate error on Windows). '
            'Add SUPABASE_SSL_VERIFY=false to your .env file, restart the server, then try again. '
            'Also run: pip install truststore certifi',
        )
    elif 'failed to establish a new connection' in lower or 'name or service not known' in lower:
        messages.error(
            request,
            'Could not reach Supabase. Check SUPABASE_URL in .env — use Project URL only, '
            'e.g. https://yourref.supabase.co (no /rest/v1).',
        )
    else:
        messages.error(request, f'Authentication error: {message}')
