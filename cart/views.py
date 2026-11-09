from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from products.models import Product
from .models import Cart, CartItem, Coupon
from .utils import get_or_create_cart


def cart_detail_view(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product').all()

    # Calculate free shipping progress ($50 target)
    free_shipping_target = 50.00
    subtotal_float = float(cart.subtotal)
    shipping_progress = min(100, int((subtotal_float / free_shipping_target) * 100))
    amount_left_for_free_shipping = max(0.00, round(free_shipping_target - subtotal_float, 2))

    context = {
        'cart': cart,
        'items': items,
        'shipping_progress': shipping_progress,
        'amount_left_for_free_shipping': amount_left_for_free_shipping,
    }
    return render(request, 'cart/cart_detail.html', context)


@require_POST
def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = get_or_create_cart(request)

    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1

    # Check available stock
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    current_qty = 0 if created else (cart_item.quantity - quantity)
    new_total_qty = current_qty + quantity

    if product.stock < new_total_qty:
        available_can_add = max(0, product.stock - current_qty)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Only {product.stock} units available in stock. Cannot add requested quantity."
            }, status=400)
        messages.error(request, f"Sorry, only {product.stock} units of '{product.name}' are available.")
        return redirect('cart:cart_detail')

    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    # Re-evaluate coupon if subtotal fell below min
    if cart.coupon:
        valid, _ = cart.coupon.is_valid(cart.subtotal)
        if not valid:
            cart.coupon = None
            cart.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'message': f"Added {quantity} x '{product.name}' to cart!",
            'cart_count': cart.total_items,
            'cart_subtotal': str(cart.subtotal),
        })

    messages.success(request, f"Added '{product.name}' to your shopping cart!")
    return redirect('cart:cart_detail')


@require_POST
def update_cart_quantity_view(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, pk=item_id, cart=cart)

    try:
        new_quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        new_quantity = 1

    if new_quantity <= 0:
        cart_item.delete()
        item_deleted = True
    else:
        if new_quantity > cart_item.product.stock:
            return JsonResponse({
                'success': False,
                'message': f"Only {cart_item.product.stock} items currently in stock."
            }, status=400)
        cart_item.quantity = new_quantity
        cart_item.save()
        item_deleted = False

    # Check coupon validity
    coupon_warning = None
    if cart.coupon:
        valid, msg = cart.coupon.is_valid(cart.subtotal)
        if not valid:
            cart.coupon = None
            cart.save()
            coupon_warning = f"Coupon removed: {msg}"

    free_shipping_target = 50.00
    subtotal_float = float(cart.subtotal)
    shipping_progress = min(100, int((subtotal_float / free_shipping_target) * 100))
    amount_left = max(0.00, round(free_shipping_target - subtotal_float, 2))

    return JsonResponse({
        'success': True,
        'item_deleted': item_deleted,
        'item_quantity': 0 if item_deleted else cart_item.quantity,
        'item_total': '0.00' if item_deleted else f"{cart_item.total_price:.2f}",
        'cart_count': cart.total_items,
        'subtotal': f"{cart.subtotal:.2f}",
        'shipping_charge': f"{cart.shipping_charge:.2f}",
        'discount_amount': f"{cart.discount_amount:.2f}",
        'final_total': f"{cart.final_total:.2f}",
        'shipping_progress': shipping_progress,
        'amount_left': f"{amount_left:.2f}",
        'coupon_warning': coupon_warning,
    })


@require_POST
def remove_from_cart_view(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    product_name = cart_item.product.name
    cart_item.delete()

    if cart.coupon:
        valid, _ = cart.coupon.is_valid(cart.subtotal)
        if not valid:
            cart.coupon = None
            cart.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Removed '{product_name}' from cart.",
            'cart_count': cart.total_items,
            'subtotal': f"{cart.subtotal:.2f}",
            'final_total': f"{cart.final_total:.2f}",
        })

    messages.info(request, f"Removed '{product_name}' from your cart.")
    return redirect('cart:cart_detail')


@require_POST
def apply_coupon_view(request):
    code = request.POST.get('coupon_code', '').strip().upper()
    cart = get_or_create_cart(request)

    if not code:
        messages.error(request, "Please enter a valid coupon code.")
        return redirect('cart:cart_detail')

    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        messages.error(request, f"Coupon code '{code}' is invalid.")
        return redirect('cart:cart_detail')

    valid, reason = coupon.is_valid(cart.subtotal)
    if not valid:
        messages.error(request, reason)
        return redirect('cart:cart_detail')

    cart.coupon = coupon
    cart.save()
    messages.success(request, f"Coupon '{coupon.code}' applied! You saved ${cart.discount_amount:.2f}.")
    return redirect('cart:cart_detail')


def remove_coupon_view(request):
    cart = get_or_create_cart(request)
    if cart.coupon:
        code = cart.coupon.code
        cart.coupon = None
        cart.save()
        messages.info(request, f"Coupon '{code}' removed.")
    return redirect('cart:cart_detail')
