from django.urls import path

from apps.cart import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_view, name='cart'),
    path('add/<int:product_id>/', views.add_to_cart_view, name='add'),
    path('update/<int:product_id>/', views.update_cart_view, name='update'),
    path('remove/<int:product_id>/', views.remove_from_cart_view, name='remove'),
]
