from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg, Count, Case, When, F, DecimalField
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, SubCategory, Product, Review, Wishlist
from .forms import ReviewForm
from cart.utils import get_or_create_cart
from cart.models import CartItem


def product_list_view(request):
    products = Product.objects.filter(is_active=True).select_related('category', 'subcategory')

    # Search keyword
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(subcategory__name__icontains=query)
        )

    # Category filter
    category_slug = request.GET.get('category', '').strip()
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    # Subcategory filter
    subcategory_slug = request.GET.get('subcategory', '').strip()
    selected_subcategory = None
    if subcategory_slug:
        selected_subcategory = get_object_or_404(SubCategory, slug=subcategory_slug)
        products = products.filter(subcategory=selected_subcategory)

    # Price range filter
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # In-stock filter
    in_stock_only = request.GET.get('in_stock', '') == '1'
    if in_stock_only:
        products = products.filter(stock__gt=0)

    # Annotate with effective price for accurate sorting
    products = products.annotate(
        effective_price=Case(
            When(discount_price__isnull=False, discount_price__lt=F('price'), then=F('discount_price')),
            default=F('price'),
            output_field=DecimalField()
        ),
        avg_rating=Avg('reviews__rating')
    )

    # Rating filter
    rating_filter = request.GET.get('rating', '').strip()
    if rating_filter:
        try:
            r_val = float(rating_filter)
            products = products.filter(avg_rating__gte=r_val)
        except ValueError:
            pass

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_asc':
        products = products.order_by('effective_price')
    elif sort_by == 'price_desc':
        products = products.order_by('-effective_price')
    elif sort_by == 'rating':
        products = products.order_by('-avg_rating', '-created_at')
    elif sort_by == 'popular':
        products = products.order_by('-views_count', '-created_at')
    else:  # newest
        products = products.order_by('-created_at')

    # Categories list for sidebar
    categories = Category.objects.annotate(product_count=Count('products')).filter(product_count__gt=0)

    # User Wishlist product ids for fast heart active states
    wishlist_product_ids = set()
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist_product_ids = set(wishlist.products.values_list('id', flat=True))
        except Wishlist.DoesNotExist:
            pass

    # Pagination: 12 products per page
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    context = {
        'products': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'selected_subcategory': selected_subcategory,
        'query': query,
        'sort_by': sort_by,
        'min_price': min_price,
        'max_price': max_price,
        'rating_filter': rating_filter,
        'in_stock_only': in_stock_only,
        'total_count': paginator.count,
        'wishlist_product_ids': wishlist_product_ids,
    }
    return render(request, 'products/product_list.html', context)


def product_detail_view(request, slug):
    product = get_object_or_404(Product.objects.select_related('category', 'subcategory'), slug=slug, is_active=True)

    # Increment view counter
    Product.objects.filter(pk=product.pk).update(views_count=F('views_count') + 1)

    gallery_images = product.gallery_images.all()
    reviews = product.reviews.select_related('user').all()

    # Review breakdown percentages (5★ down to 1★)
    total_reviews = reviews.count()
    breakdown = []
    for star in range(5, 0, -1):
        count = reviews.filter(rating=star).count()
        pct = int((count / total_reviews) * 100) if total_reviews > 0 else 0
        breakdown.append({'star': star, 'count': count, 'pct': pct})

    # Related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(pk=product.pk).order_by('-views_count')[:4]

    # Wishlist check
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, products=product).exists()

    # Review Form
    review_form = ReviewForm()
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = reviews.filter(user=request.user).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        if user_has_reviewed:
            messages.warning(request, "You have already submitted a review for this product.")
            return redirect('products:product_detail', slug=product.slug)

        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Thank you! Your verified review has been published.")
            return redirect('products:product_detail', slug=product.slug)

    context = {
        'product': product,
        'gallery_images': gallery_images,
        'reviews': reviews,
        'total_reviews': total_reviews,
        'breakdown': breakdown,
        'related_products': related_products,
        'in_wishlist': in_wishlist,
        'review_form': review_form,
        'user_has_reviewed': user_has_reviewed,
    }
    return render(request, 'products/product_detail.html', context)


@login_required
def wishlist_view(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    products = wishlist.products.filter(is_active=True)
    return render(request, 'products/wishlist.html', {'products': products})


@login_required
def toggle_wishlist_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

    if wishlist.products.filter(pk=product.pk).exists():
        wishlist.products.remove(product)
        added = False
        message = f"Removed '{product.name}' from your wishlist."
    else:
        wishlist.products.add(product)
        added = True
        message = f"Added '{product.name}' to your wishlist!"

    total_count = wishlist.products.count()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'added': added,
            'total_count': total_count,
            'message': message,
        })

    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'products:wishlist'))


@login_required
def move_to_cart_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    
    if wishlist.products.filter(pk=product.pk).exists():
        wishlist.products.remove(product)

    if product.stock <= 0:
        messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
        return redirect('products:wishlist')

    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"'{product.name}' moved to your shopping cart!")
    return redirect('cart:cart_detail')
