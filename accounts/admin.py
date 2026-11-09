from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Address


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'phone_number', 'is_staff', 'is_active', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')
    ordering = ('-created_at',)
    fieldsets = UserAdmin.fieldsets + (
        ('ShopSphere Profile', {'fields': ('phone_number', 'profile_picture', 'is_email_verified')}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'state', 'postal_code', 'is_default_shipping', 'is_default_billing')
    search_fields = ('user__email', 'full_name', 'city', 'postal_code')
    list_filter = ('is_default_shipping', 'is_default_billing', 'state', 'address_type')
