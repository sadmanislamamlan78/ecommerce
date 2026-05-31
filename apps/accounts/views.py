"""Authentication views using Supabase Auth."""
import logging

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.accounts.auth_helpers import (
    clear_supabase_session,
    handle_supabase_auth_error,
    merge_session_cart_on_login,
    store_supabase_session,
)
from apps.accounts.decorators import supabase_login_required
from apps.accounts.forms import LoginForm, ProfileForm, RegisterForm
from apps.accounts.supabase_client import (
    SupabaseConfigError,
    get_authenticated_client,
    get_supabase_client,
)

logger = logging.getLogger(__name__)


def _safe_redirect(request, default_name='products:home'):
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect(default_name)


def _fetch_profile(client, user_id):
    try:
        result = (
            client.table('profiles')
            .select('full_name, phone, address, is_staff')
            .eq('id', user_id)
            .maybe_single()
            .execute()
        )
        return result.data or {}
    except Exception as exc:
        logger.info('Profile fetch skipped (table may not exist yet): %s', exc)
        return {}


def _upsert_profile(client, user_id, full_name='', phone='', address=''):
    try:
        client.table('profiles').upsert({
            'id': user_id,
            'full_name': full_name,
            'phone': phone,
            'address': address,
        }).execute()
        return True
    except Exception as exc:
        logger.warning('Could not save profile: %s', exc)
        return False


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.supabase_user:
        messages.info(
            request,
            'You are already signed in. Sign out first if you want to create a different account.',
        )
        return redirect('accounts:profile')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        try:
            client = get_supabase_client()
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            full_name = form.cleaned_data['full_name']

            auth_response = client.sign_up({
                'email': email,
                'password': password,
                'options': {
                    'data': {'full_name': full_name},
                },
            })

            user = auth_response.user
            session = auth_response.session

            if user and session:
                authed = get_authenticated_client(
                    session.access_token,
                    session.refresh_token,
                )
                _upsert_profile(authed, str(user.id), full_name=full_name)
                profile = _fetch_profile(authed, str(user.id))
                store_supabase_session(request, auth_response, profile)
                merge_session_cart_on_login(request)
                messages.success(request, f'Welcome, {full_name}! Your account is ready.')
                return _safe_redirect(request, 'accounts:profile')

            if user and not session:
                messages.info(
                    request,
                    'Account created! Check your email to confirm your address, '
                    'then sign in.',
                )
                return redirect('accounts:login')

            messages.error(request, 'Registration failed. Please try again.')

        except SupabaseConfigError as exc:
            messages.error(request, str(exc))
        except Exception as exc:
            handle_supabase_auth_error(request, exc)

    return render(request, 'accounts/register.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.supabase_user:
        messages.info(request, 'You are already signed in.')
        return redirect('accounts:profile')

    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        try:
            client = get_supabase_client()
            auth_response = client.sign_in_with_password({
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password'],
            })

            user = auth_response.user
            session = auth_response.session
            if user and session:
                authed = get_authenticated_client(
                    session.access_token,
                    session.refresh_token,
                )
                profile = _fetch_profile(authed, str(user.id))
                if store_supabase_session(request, auth_response, profile):
                    merge_session_cart_on_login(request)
                    name = profile.get('full_name') or request.session.get('supabase_email')
                    messages.success(request, f'Welcome back, {name}!')
                    return _safe_redirect(request, 'accounts:profile')

            messages.error(request, 'Login failed. Please check your credentials.')

        except SupabaseConfigError as exc:
            messages.error(request, str(exc))
        except Exception as exc:
            handle_supabase_auth_error(request, exc)

    return render(request, 'accounts/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


@require_http_methods(['GET', 'POST'])
def logout_view(request):
    token = request.session.get('supabase_access_token')
    if token:
        try:
            client = get_supabase_client()
            refresh = request.session.get('supabase_refresh_token', '')
            client.sign_out(token)
        except Exception as exc:
            logger.warning('Supabase sign_out error: %s', exc)

    clear_supabase_session(request)
    messages.info(request, 'You have been signed out.')
    return redirect('accounts:login')


@supabase_login_required
@require_http_methods(['GET', 'POST'])
def profile_view(request):
    profile = request.session.get('supabase_profile', {})
    form = ProfileForm(request.POST or None, initial=profile)

    if request.method == 'POST' and form.is_valid():
        try:
            token = request.session['supabase_access_token']
            refresh = request.session.get('supabase_refresh_token', '')
            client = get_authenticated_client(token, refresh)
            user_id = request.session['supabase_user_id']
            data = {
                'full_name': form.cleaned_data['full_name'],
                'phone': form.cleaned_data['phone'],
                'address': form.cleaned_data['address'],
            }
            if _upsert_profile(client, user_id, **data):
                request.session['supabase_profile'] = data
                request.session.modified = True
                messages.success(request, 'Profile updated successfully.')
            else:
                messages.warning(
                    request,
                    'Could not save to Supabase yet. Run the profiles SQL in Supabase first.',
                )
            return redirect('accounts:profile')

        except Exception as exc:
            messages.error(request, f'Could not update profile: {exc}')

    return render(request, 'accounts/profile.html', {
        'form': form,
        'email': request.session.get('supabase_email', ''),
    })
