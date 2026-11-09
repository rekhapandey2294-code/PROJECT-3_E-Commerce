from django.db import models
from django.conf import settings
from django.utils import timezone
from products.models import Product
from decimal import Decimal


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage Discount (%)'),
        ('fixed', 'Fixed Discount Amount ($)'),
    )

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="e.g. 15 for 15% or 25 for $25")
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Caps percentage discount")
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(default=1000)
    times_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()} - {self.discount_value})"

    def is_valid(self, subtotal=0):
        now = timezone.now()
        if not self.active:
            return False, "This coupon is inactive."
        if now < self.valid_from or now > self.valid_to:
            return False, "This coupon has expired."
        if self.times_used >= self.usage_limit:
            return False, "This coupon has reached its maximum usage limit."
        if Decimal(str(subtotal)) < self.min_purchase_amount:
            return False, f"Minimum purchase amount of ${self.min_purchase_amount} required to use this coupon."
        return True, "Coupon is valid."

    def calculate_discount(self, subtotal):
        subtotal = Decimal(str(subtotal))
        valid, _ = self.is_valid(subtotal)
        if not valid:
            return Decimal('0.00')

        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / Decimal('100')
            if self.max_discount_amount and discount > self.max_discount_amount:
                discount = self.max_discount_amount
        else:
            discount = min(self.discount_value, subtotal)
        return round(discount, 2)


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart #{self.id} - {'User: ' + self.user.email if self.user else 'Session: ' + (self.session_key or 'Guest')}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.select_related('product'))

    @property
    def shipping_charge(self):
        # Free shipping if subtotal >= $50, else flat $5.00
        if self.subtotal >= Decimal('50.00') or self.subtotal == 0:
            return Decimal('0.00')
        return Decimal('5.00')

    @property
    def discount_amount(self):
        if self.coupon:
            return self.coupon.calculate_discount(self.subtotal)
        return Decimal('0.00')

    @property
    def final_total(self):
        total = self.subtotal - self.discount_amount + self.shipping_charge
        return max(Decimal('0.00'), round(total, 2))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def unit_price(self):
        return self.product.final_price

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    @property
    def total_savings(self):
        if self.product.discount_price and self.product.discount_price < self.product.price:
            return (self.product.price - self.product.discount_price) * self.quantity
        return Decimal('0.00')
