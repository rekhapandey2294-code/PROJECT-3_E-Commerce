from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import CustomUser, Address
from .forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm,
    ChangePasswordForm, AddressForm, ForgotPasswordForm
)
from cart.utils import merge_carts_on_login
from orders.models import Order


def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f"Welcome to ShopSphere, {user.first_name or user.username}! Your account has been created.")
            login(request, user)
            merge_carts_on_login(request, user)
            return redirect('core:home')
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    next_url = request.GET.get('next', 'core:home')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['login_identifier'].strip()
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            # Support login by email OR username
            user = None
            if '@' in identifier:
                try:
                    user_obj = CustomUser.objects.get(email__iexact=identifier)
                    user = authenticate(request, username=user_obj.email, password=password)
                except CustomUser.DoesNotExist:
                    pass
            else:
                user = authenticate(request, username=identifier, password=password)
                if not user:
                    try:
                        user_obj = CustomUser.objects.get(username__iexact=identifier)
                        user = authenticate(request, username=user_obj.email, password=password)
                    except CustomUser.DoesNotExist:
                        pass

            if user is not None:
                if user.is_active:
                    login(request, user)
                    if not remember_me:
                        # Session expires when browser closes
                        request.session.set_expiry(0)
                    else:
                        # 30 days
                        request.session.set_expiry(30 * 24 * 3600)
                    
                    merge_carts_on_login(request, user)
                    messages.success(request, f"Welcome back, {user.full_name}!")
                    
                    # Prevent open redirect
                    if next_url and next_url.startswith('/'):
                        return redirect(next_url)
                    return redirect('core:home')
                else:
                    messages.error(request, "Your account has been deactivated. Please contact support.")
            else:
                messages.error(request, "Invalid email/username or password.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out securely. See you again soon!")
    return redirect('core:home')


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Error updating profile. Please check the fields.")
    else:
        form = UserProfileForm(instance=user)

    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    addresses = Address.objects.filter(user=user)

    context = {
        'form': form,
        'user': user,
        'recent_orders': recent_orders,
        'addresses': addresses,
        'active_tab': 'profile',
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Your password has been changed successfully!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form, 'active_tab': 'password'})


@login_required
def address_list_view(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/addresses.html', {'addresses': addresses, 'active_tab': 'addresses'})


@login_required
def address_create_view(request):
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            # If this is the user's first address, make it default
            if not Address.objects.filter(user=request.user).exists():
                address.is_default_shipping = True
                address.is_default_billing = True
            address.save()
            messages.success(request, "New address saved successfully!")
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('accounts:addresses')
    else:
        form = AddressForm()

    return render(request, 'accounts/address_form.html', {'form': form, 'action_title': 'Add New Address', 'next': next_url})


@login_required
def address_edit_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully!")
            return redirect('accounts:addresses')
    else:
        form = AddressForm(instance=address)

    return render(request, 'accounts/address_form.html', {'form': form, 'action_title': 'Edit Address', 'address': address})


@login_required
def address_delete_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, "Address deleted successfully.")
    return redirect('accounts:addresses')


@login_required
def address_set_default_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.is_default_shipping = True
    address.save()
    messages.success(request, f"'{address.full_name}' address set as your default shipping destination.")
    return redirect('accounts:addresses')


def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # For security and standard UX, display success even if user not found
            messages.success(
                request,
                f"If an account is associated with {email}, a password reset link has been dispatched to your inbox. (Demo mode: reset link simulated)."
            )
            return redirect('accounts:login')
    else:
        form = ForgotPasswordForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})
