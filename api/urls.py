from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='api-products')

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name='api-categories'),
    path('cart/', views.CartAPIView.as_view(), name='api-cart'),
    path('orders/', views.OrderListAPIView.as_view(), name='api-orders'),
    path('', include(router.urls)),
]
