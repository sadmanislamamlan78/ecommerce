"""Product admin forms."""
from django import forms

from apps.common.validators import MAX_DESCRIPTION_LEN, validate_image_upload
from apps.products.services import get_categories


class ProductAdminForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Product name'}),
    )
    slug = forms.SlugField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'auto-generated-from-name (optional)',
        }),
        help_text='Leave blank to generate from the product name.',
    )
    description = forms.CharField(
        required=False,
        max_length=MAX_DESCRIPTION_LEN,
        widget=forms.Textarea(attrs={
            'class': 'form-input form-textarea',
            'rows': 4,
            'placeholder': 'Product description',
        }),
    )
    price = forms.DecimalField(
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00'}),
    )
    category_id = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    stock = forms.IntegerField(
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0'}),
    )
    image_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-input',
            'placeholder': 'https://... (optional if uploading a file)',
        }),
        help_text='Or paste an external image URL.',
    )
    image_file = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-input-file', 'accept': 'image/*'}),
        help_text='Upload to Supabase Storage (max 5 MB).',
    )

    def __init__(self, *args, **kwargs):
        self.is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)
        categories = get_categories()
        choices = [(str(c['id']), c['name']) for c in categories]
        if not choices:
            choices = [('', 'No categories — run phase2_catalog.sql')]
        self.fields['category_id'].choices = choices

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Product name must be at least 2 characters.')
        return name

    def clean_category_id(self):
        value = self.cleaned_data.get('category_id')
        if not value:
            raise forms.ValidationError('Please select a category.')
        try:
            int(value)
        except (TypeError, ValueError) as exc:
            raise forms.ValidationError('Invalid category selected.') from exc
        return value

    def clean_image_file(self):
        file_obj = self.cleaned_data.get('image_file')
        if not file_obj:
            return file_obj
        try:
            validate_image_upload(file_obj)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc
        return file_obj

    def clean(self):
        cleaned = super().clean()
        has_image = cleaned.get('image_file') or cleaned.get('image_url')
        if not has_image and not self.is_edit:
            self.add_error(
                'image_file',
                'Upload an image or provide an image URL.',
            )
        return cleaned
