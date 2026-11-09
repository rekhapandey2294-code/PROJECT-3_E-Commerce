from .models import Cart, CartItem


def get_or_create_cart(request):
    """
    Retrieves or creates a cart for the logged-in user or anonymous session.
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # Check if there is an anonymous session cart to merge
        session_key = request.session.session_key
        if session_key:
            guest_cart = Cart.objects.filter(session_key=session_key).exclude(id=cart.id).first()
            if guest_cart:
                for item in guest_cart.items.all():
                    cart_item, created = CartItem.objects.get_or_create(
                        cart=cart,
                        product=item.product,
                        defaults={'quantity': item.quantity}
                    )
                    if not created:
                        cart_item.quantity += item.quantity
                        cart_item.save()
                guest_cart.delete()
        return cart
    else:
        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
        return cart


def merge_carts_on_login(request, user):
    """
    Called upon user login to merge anonymous session cart items to user's cart.
    """
    session_key = request.session.session_key
    if not session_key:
        return
    user_cart, _ = Cart.objects.get_or_create(user=user)
    guest_cart = Cart.objects.filter(session_key=session_key).exclude(id=user_cart.id).first()
    if guest_cart:
        for item in guest_cart.items.all():
            cart_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                product=item.product,
                defaults={'quantity': item.quantity}
            )
            if not created:
                cart_item.quantity += item.quantity
                cart_item.save()
        guest_cart.delete()
