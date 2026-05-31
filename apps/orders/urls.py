from django.urls import path

from apps.orders import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_history_view, name='history'),
    path('checkout/', views.checkout_view, name='checkout'),
]
