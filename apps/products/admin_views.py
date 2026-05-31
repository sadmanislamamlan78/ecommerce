"""Staff-only product admin dashboard (Phase 5)."""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.decorators import staff_required
from apps.products.admin_services import (
    create_product,
    delete_product,
    get_product_by_id,
    list_all_products,
    slugify,
    update_product,
)
from apps.products.forms import ProductAdminForm
from apps.common.errors import friendly_error_message
from apps.products.storage import StorageUploadError, upload_product_image


def _get_admin_client_session(request):
    return request.session.get('supabase_access_token', '')


@staff_required
@require_http_methods(['GET'])
def admin_dashboard_view(request):
    products = list_all_products(request)
    return render(request, 'products/admin/dashboard.html', {
        'products': products,
        'product_count': len(products),
    })


@staff_required
@require_http_methods(['GET', 'POST'])
def admin_product_create_view(request):
    form = ProductAdminForm(request.POST or None, request.FILES or None, is_edit=False)

    if request.method == 'POST' and form.is_valid():
        try:
            image_url = form.cleaned_data.get('image_url') or ''
            if form.cleaned_data.get('image_file'):
                image_url = upload_product_image(
                    form.cleaned_data['image_file'],
                    _get_admin_client_session(request),
                    form.cleaned_data.get('slug') or slugify(form.cleaned_data['name']),
                )
            product = create_product(request, {
                'name': form.cleaned_data['name'],
                'slug': form.cleaned_data.get('slug'),
                'description': form.cleaned_data['description'],
                'price': form.cleaned_data['price'],
                'category_id': form.cleaned_data['category_id'],
                'stock': form.cleaned_data['stock'],
                'image_url': image_url,
            })
            messages.success(request, f'Product "{product["name"]}" created successfully.')
            return redirect('products:admin_dashboard')
        except StorageUploadError as exc:
            messages.error(request, str(exc))
        except Exception as exc:
            messages.error(request, friendly_error_message(exc, context='Could not create product'))

    return render(request, 'products/admin/product_form.html', {
        'form': form,
        'title': 'Add New Product',
        'submit_label': 'Create Product',
        'is_edit': False,
    })


@staff_required
@require_http_methods(['GET', 'POST'])
def admin_product_edit_view(request, product_id):
    product = get_product_by_id(request, product_id)
    if not product:
        messages.error(request, 'Product not found.')
        return redirect('products:admin_dashboard')

    initial = {
        'name': product['name'],
        'slug': product['slug'],
        'description': product.get('description', ''),
        'price': product['price'],
        'category_id': str(product.get('category_id', '')),
        'stock': product.get('stock', 0),
        'image_url': product.get('image_url', ''),
    }
    form = ProductAdminForm(
        request.POST or None,
        request.FILES or None,
        initial=initial,
        is_edit=True,
    )

    if request.method == 'POST' and form.is_valid():
        try:
            image_url = form.cleaned_data.get('image_url') or product.get('image_url', '')
            if form.cleaned_data.get('image_file'):
                image_url = upload_product_image(
                    form.cleaned_data['image_file'],
                    _get_admin_client_session(request),
                    form.cleaned_data.get('slug') or slugify(form.cleaned_data['name']),
                )
            update_product(request, product_id, {
                'name': form.cleaned_data['name'],
                'slug': form.cleaned_data.get('slug'),
                'description': form.cleaned_data['description'],
                'price': form.cleaned_data['price'],
                'category_id': form.cleaned_data['category_id'],
                'stock': form.cleaned_data['stock'],
                'image_url': image_url,
            })
            messages.success(request, f'Product "{form.cleaned_data["name"]}" updated.')
            return redirect('products:admin_dashboard')
        except StorageUploadError as exc:
            messages.error(request, str(exc))
        except Exception as exc:
            messages.error(request, friendly_error_message(exc, context='Could not update product'))

    return render(request, 'products/admin/product_form.html', {
        'form': form,
        'product': product,
        'title': f'Edit: {product["name"]}',
        'submit_label': 'Save Changes',
        'is_edit': True,
    })


@staff_required
@require_http_methods(['GET', 'POST'])
def admin_product_delete_view(request, product_id):
    product = get_product_by_id(request, product_id)
    if not product:
        messages.error(request, 'Product not found.')
        return redirect('products:admin_dashboard')

    if request.method == 'POST':
        try:
            delete_product(request, product_id)
            messages.success(request, f'Product "{product["name"]}" deleted.')
            return redirect('products:admin_dashboard')
        except Exception as exc:
            messages.error(request, friendly_error_message(exc, context='Could not delete product'))

    return render(request, 'products/admin/product_confirm_delete.html', {
        'product': product,
    })
