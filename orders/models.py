from django.db import models
from django.conf import settings
from products.models import Product
from decimal import Decimal
import uuid
import datetime


class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('COD', 'Cash on Delivery (COD)'),
        ('Razorpay', 'Online Payment (Razorpay / UPI / Cards)'),
    )

    order_number = models.CharField(max_length=64, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')

    # Shipping Address Snapshot
    shipping_full_name = models.CharField(max_length=150)
    shipping_phone = models.CharField(max_length=20)
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default='India')

    # Statuses
    order_status = models.CharField(max_length=30, choices=ORDER_STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='COD')

    # Razorpay info
    razorpay_order_id = models.CharField(max_length=120, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=120, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    # Financials
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Tracking & metadata
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    order_note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            date_str = datetime.date.today().strftime('%Y%m%d')
            unique_part = uuid.uuid4().hex[:6].upper()
            self.order_number = f"SPH-{date_str}-{unique_part}"
        if not self.tracking_number:
            self.tracking_number = f"TRK{uuid.uuid4().hex[:10].upper()}"
        if not self.estimated_delivery:
            self.estimated_delivery = datetime.date.today() + datetime.timedelta(days=4)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.user.email} (${self.total_amount})"

    @property
    def can_be_cancelled(self):
        return self.order_status in ['Pending', 'Confirmed']

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def status_badge_class(self):
        mapping = {
            'Pending': 'bg-warning text-dark',
            'Confirmed': 'bg-info text-dark',
            'Processing': 'bg-primary text-white',
            'Shipped': 'bg-purple text-white',
            'Delivered': 'bg-success text-white',
            'Cancelled': 'bg-danger text-white',
        }
        return mapping.get(self.order_status, 'bg-secondary text-white')

    @property
    def payment_badge_class(self):
        mapping = {
            'Paid': 'bg-success text-white',
            'Pending': 'bg-warning text-dark',
            'Failed': 'bg-danger text-white',
            'Refunded': 'bg-secondary text-white',
        }
        return mapping.get(self.payment_status, 'bg-secondary text-white')

    def get_tracking_timeline(self):
        stages = [
            ('Pending', 'Order Placed', 'Your order has been recorded in our system.'),
            ('Confirmed', 'Order Confirmed', 'The seller has confirmed your order.'),
            ('Processing', 'Processing & Packed', 'Your package is inspected and packaged.'),
            ('Shipped', 'Shipped & Out for Delivery', 'Your parcel is on the way with tracking.'),
            ('Delivered', 'Delivered', 'The shipment was delivered successfully.'),
        ]
        
        status_order = ['Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered']
        
        if self.order_status == 'Cancelled':
            return [
                {
                    'status': 'Cancelled',
                    'title': 'Order Cancelled',
                    'desc': 'This order was cancelled.',
                    'state': 'cancelled',
                    'icon': 'bi-x-circle-fill'
                }
            ]

        try:
            current_index = status_order.index(self.order_status)
        except ValueError:
            current_index = 0

        timeline = []
        for idx, (code, title, desc) in enumerate(stages):
            if idx < current_index:
                state = 'completed'
                icon = 'bi-check-circle-fill'
            elif idx == current_index:
                state = 'current'
                icon = 'bi-arrow-right-circle-fill'
            else:
                state = 'upcoming'
                icon = 'bi-circle'

            timeline.append({
                'code': code,
                'title': title,
                'desc': desc,
                'state': state,
                'icon': icon
            })
        return timeline


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    product_name = models.CharField(max_length=255)
    product_image_url = models.URLField(max_length=500, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
