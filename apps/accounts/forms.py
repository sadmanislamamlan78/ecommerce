"""Authentication forms with server-side validation."""
from django import forms

from apps.common.validators import validate_address, validate_person_name, validate_phone


class RegisterForm(forms.Form):
    full_name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Full name',
            'autocomplete': 'name',
        }),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email address',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password (min. 8 characters)',
            'autocomplete': 'new-password',
        }),
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password',
        }),
    )

    def clean_full_name(self):
        try:
            return validate_person_name(self.cleaned_data['full_name'], field_label='Full name')
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email address',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        min_length=1,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        }),
    )

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if not password:
            raise forms.ValidationError('Password is required.')
        return password


class ProfileForm(forms.Form):
    full_name = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full name'}),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone number'}),
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input form-textarea',
            'placeholder': 'Shipping address',
            'rows': 3,
        }),
    )

    def clean_full_name(self):
        value = self.cleaned_data.get('full_name', '')
        if not value:
            return ''
        try:
            return validate_person_name(value, field_label='Full name')
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

    def clean_phone(self):
        try:
            return validate_phone(self.cleaned_data.get('phone', ''), required=False)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

    def clean_address(self):
        value = self.cleaned_data.get('address', '')
        if not value:
            return ''
        try:
            return validate_address(value, required=False)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc
