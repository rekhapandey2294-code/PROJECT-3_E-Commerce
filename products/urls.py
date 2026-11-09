from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list_view, name='product_list'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist_view, name='toggle_wishlist'),
    path('wishlist/move-to-cart/<int:product_id>/', views.move_to_cart_view, name='move_to_cart'),
    path('<slug:slug>/', views.product_detail_view, name='product_detail'),
]
