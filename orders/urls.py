from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('place-order/', views.place_order_view, name='place_order'),
    path('razorpay/verify/', views.razorpay_payment_verify, name='razorpay_verify'),
    path('confirmation/<str:order_number>/', views.order_confirmation_view, name='order_confirmation'),
    path('history/', views.order_history_view, name='order_history'),
    path('detail/<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('cancel/<str:order_number>/', views.order_cancel_view, name='order_cancel'),
    path('track/', views.order_track_view, name='order_track'),
    path('invoice/<str:order_number>/', views.download_invoice_view, name='download_invoice'),
]
