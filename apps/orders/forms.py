from django import forms

from apps.common.validators import validate_address, validate_person_name, validate_phone


class CheckoutForm(forms.Form):
    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('card', 'Card Payment (Mock)'),
    ]

    full_name = forms.CharField(
        label='Full Name',
        max_length=120,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your full name',
            'class': 'form-input',
            'autocomplete': 'name',
        }),
    )
    phone = forms.CharField(
        label='Phone Number',
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 017XXXXXXXX',
            'class': 'form-input',
            'autocomplete': 'tel',
        }),
    )
    address = forms.CharField(
        label='Shipping Address',
        max_length=500,
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter your full delivery address',
            'class': 'form-input form-textarea',
            'rows': 3,
            'autocomplete': 'street-address',
        }),
    )
    payment_method = forms.ChoiceField(
        label='Payment Method',
        choices=PAYMENT_CHOICES,
        initial='cod',
        widget=forms.RadioSelect(attrs={'class': 'payment-radio'}),
    )

    def clean_full_name(self):
        try:
            return validate_person_name(self.cleaned_data['full_name'], field_label='Full name')
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

    def clean_phone(self):
        try:
            return validate_phone(self.cleaned_data['phone'], required=True)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

    def clean_address(self):
        try:
            return validate_address(self.cleaned_data['address'], required=True)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

    def clean_payment_method(self):
        value = self.cleaned_data['payment_method']
        valid = {choice[0] for choice in self.PAYMENT_CHOICES}
        if value not in valid:
            raise forms.ValidationError('Please select a valid payment method.')
        return value

