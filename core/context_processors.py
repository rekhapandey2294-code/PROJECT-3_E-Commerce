from products.models import Category
from cart.models import Cart
from products.models import Wishlist
import datetime


def global_shop_context(request):
    """
    Supplies global shop data to all templates:
    Cart count, Wishlist count, Navigation Categories, and Store Metadata.
    """
    categories = Category.objects.prefetch_related('subcategories').all()
    
    # Cart item count
    cart_count = 0
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key
            if session_key:
                cart = Cart.objects.filter(session_key=session_key).first()
            else:
                cart = None
        
        if cart:
            cart_count = cart.total_items
    except Exception:
        cart_count = 0

    # Wishlist count
    wishlist_count = 0
    try:
        if request.user.is_authenticated:
            wishlist = Wishlist.objects.filter(user=request.user).first()
            if wishlist:
                wishlist_count = wishlist.products.count()
    except Exception:
        wishlist_count = 0

    return {
        'SITE_NAME': 'ShopSphere',
        'SITE_TAGLINE': 'Elevate Your Everyday Shopping',
        'header_categories': categories,
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
        'current_year': datetime.datetime.now().year,
    }
