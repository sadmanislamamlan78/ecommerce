from django.urls import path

from apps.products import admin_views, views

app_name = 'products'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('shop/', views.shop_view, name='shop'),
    path('product/<slug:slug>/', views.product_detail_view, name='detail'),
    # Staff product admin (Phase 5) — /manage/ avoids Django's /admin/
    path('manage/', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('manage/add/', admin_views.admin_product_create_view, name='admin_product_create'),
    path('manage/<int:product_id>/edit/', admin_views.admin_product_edit_view, name='admin_product_edit'),
    path('manage/<int:product_id>/delete/', admin_views.admin_product_delete_view, name='admin_product_delete'),
]