from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.db import transaction
import hmac
import hashlib

from cart.utils import get_or_create_cart
from accounts.models import Address
from products.models import Product
from .models import Order, OrderItem
from .invoice_generator import generate_pdf_invoice

# Optional Razorpay SDK
try:
    import razorpay
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
except Exception:
    razorpay_client = None


@login_required
def checkout_view(request):
    cart = get_or_create_cart(request)
    if cart.total_items == 0:
        messages.warning(request, "Your shopping cart is empty. Add products before checking out.")
        return redirect('products:product_list')

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default_shipping=True).first() or addresses.first()

    context = {
        'cart': cart,
        'addresses': addresses,
        'default_address': default_address,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
@require_POST
def place_order_view(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product').all()
    if not items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('products:product_list')

    # Stock re-validation check before placing order
    for item in items:
        if item.quantity > item.product.stock:
            messages.error(
                request,
                f"Sorry, '{item.product.name}' only has {item.product.stock} units left. Please adjust your cart quantity."
            )
            return redirect('cart:cart_detail')

    # Resolve shipping address
    address_id = request.POST.get('address_id')
    if address_id and address_id != 'new':
        address = get_object_or_404(Address, id=address_id, user=request.user)
        full_name = address.full_name
        phone = address.phone_number
        line1 = address.address_line_1
        line2 = address.address_line_2 or ''
        city = address.city
        state = address.state
        postal_code = address.postal_code
        country = address.country
    else:
        # User entered a new address on checkout form
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        line1 = request.POST.get('address_line_1', '').strip()
        line2 = request.POST.get('address_line_2', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', 'India').strip()
        save_address = request.POST.get('save_address') == 'on'

        if not all([full_name, phone, line1, city, state, postal_code]):
            messages.error(request, "Please fill in all required shipping address fields.")
            return redirect('orders:checkout')

        if save_address:
            Address.objects.create(
                user=request.user,
                full_name=full_name,
                phone_number=phone,
                address_line_1=line1,
                address_line_2=line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country
            )

    payment_method = request.POST.get('payment_method', 'COD')
    order_note = request.POST.get('order_note', '')

    with transaction.atomic():
        # Create Order record
        order = Order.objects.create(
            user=request.user,
            shipping_full_name=full_name,
            shipping_phone=phone,
            shipping_address_line1=line1,
            shipping_address_line2=line2,
            shipping_city=city,
            shipping_state=state,
            shipping_postal_code=postal_code,
            shipping_country=country,
            payment_method=payment_method,
            subtotal=cart.subtotal,
            shipping_charge=cart.shipping_charge,
            discount_amount=cart.discount_amount,
            coupon_code=cart.coupon.code if cart.coupon else None,
            total_amount=cart.final_total,
            order_note=order_note,
            order_status='Pending',
            payment_status='Pending'
        )

        # Create Order Items and decrease product stock
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_image_url=item.product.display_image,
                unit_price=item.unit_price,
                quantity=item.quantity,
                total_price=item.total_price
            )
            # Reduce inventory
            Product.objects.filter(pk=item.product.pk).update(stock=item.product.stock - item.quantity)

        # Increment coupon usage count
        if cart.coupon:
            cart.coupon.times_used += 1
            cart.coupon.save()

    # Route based on payment method
    if payment_method == 'COD':
        order.order_status = 'Confirmed'
        order.save()
        # Empty cart
        cart.items.all().delete()
        cart.coupon = None
        cart.save()
        messages.success(request, f"Order #{order.order_number} confirmed with Cash on Delivery!")
        return redirect('orders:order_confirmation', order_number=order.order_number)

    elif payment_method == 'Razorpay':
        # Initiate Razorpay order
        amount_in_paise = int(order.total_amount * 100)
        razorpay_order_id = f"order_{order.order_number}"

        try:
            if razorpay_client:
                rzp_order = razorpay_client.order.create({
                    'amount': amount_in_paise,
                    'currency': 'INR',
                    'receipt': order.order_number,
                    'notes': {'user_email': request.user.email}
                })
                razorpay_order_id = rzp_order['id']
        except Exception:
            # Fallback mock order ID for demo/test sandbox
            razorpay_order_id = f"rzp_mock_{order.order_number}"

        order.razorpay_order_id = razorpay_order_id
        order.save()

        context = {
            'order': order,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount_in_paise': amount_in_paise,
            'user': request.user,
        }
        return render(request, 'orders/razorpay_payment.html', context)

    else:
        messages.error(request, "Invalid payment method selected.")
        return redirect('orders:checkout')


@require_POST
def razorpay_payment_verify(request):
    order_number = request.POST.get('order_number')
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_order_id = request.POST.get('razorpay_order_id', '')
    razorpay_signature = request.POST.get('razorpay_signature', '')

    order = get_object_or_404(Order, order_number=order_number)

    # Signature verification
    verified = False
    if razorpay_client and razorpay_signature:
        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            razorpay_client.utility.verify_payment_signature(params_dict)
            verified = True
        except Exception:
            verified = False
    else:
        # Test mode verification fallback
        if razorpay_payment_id:
            verified = True

    if verified:
        order.order_status = 'Confirmed'
        order.payment_status = 'Paid'
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
        order.save()

        # Clear cart
        cart = get_or_create_cart(request)
        cart.items.all().delete()
        cart.coupon = None
        cart.save()

        messages.success(request, f"Payment successful! Order #{order.order_number} confirmed.")
        return redirect('orders:order_confirmation', order_number=order.order_number)
    else:
        order.payment_status = 'Failed'
        order.save()
        messages.error(request, "Payment verification could not be validated. Please retry or contact support.")
        return redirect('orders:order_detail', order_number=order.order_number)


@login_required
def order_confirmation_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})


@login_required
def order_history_view(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(order_status=status_filter)

    context = {
        'orders': orders,
        'status_filter': status_filter,
        'active_tab': 'orders',
    }
    return render(request, 'orders/order_history.html', context)


@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    timeline = order.get_tracking_timeline()
    return render(request, 'orders/order_detail.html', {'order': order, 'timeline': timeline})


@login_required
@require_POST
def order_cancel_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if not order.can_be_cancelled:
        messages.error(request, f"Order #{order.order_number} cannot be cancelled as it is already '{order.order_status}'.")
        return redirect('orders:order_detail', order_number=order.order_number)

    # Restock inventory
    with transaction.atomic():
        for item in order.items.all():
            if item.product:
                Product.objects.filter(pk=item.product.pk).update(stock=item.product.stock + item.quantity)
        
        order.order_status = 'Cancelled'
        order.save()

    messages.info(request, f"Order #{order.order_number} has been cancelled and products restocked.")
    return redirect('orders:order_detail', order_number=order.order_number)


def order_track_view(request):
    """
    Public tracking view: user inputs Order Number and Email to view real-time shipping status.
    """
    order = None
    searched = False
    error_message = None

    if request.method == 'GET' and ('order_number' in request.GET or 'tracking_number' in request.GET):
        searched = True
        order_num = request.GET.get('order_number', '').strip()
        trk_num = request.GET.get('tracking_number', '').strip()
        email = request.GET.get('email', '').strip().lower()

        if order_num or trk_num:
            query = Order.objects.all()
            if order_num:
                query = query.filter(order_number__iexact=order_num)
            if trk_num:
                query = query.filter(tracking_number__iexact=trk_num)
            if email:
                query = query.filter(user__email__iexact=email)

            order = query.first()
            if not order:
                error_message = "No matching order found. Please verify your order number and registered email address."
        else:
            error_message = "Please provide an Order ID or Tracking Number."

    timeline = order.get_tracking_timeline() if order else None
    return render(request, 'orders/order_track.html', {
        'order': order,
        'timeline': timeline,
        'searched': searched,
        'error_message': error_message,
    })


@login_required
def download_invoice_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    pdf_buffer = generate_pdf_invoice(order)
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{order.order_number}.pdf"'
    return response
