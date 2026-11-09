from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Avg, F
from products.models import Product, Category, Review, Wishlist
from .models import ContactMessage, NewsletterSubscriber
from .forms import ContactForm, NewsletterForm


def home_view(request):
    featured_categories = Category.objects.filter(is_featured=True)[:6]
    if not featured_categories.exists():
        featured_categories = Category.objects.all()[:6]

    # Deals of the Day: Products with active discount, sorted by discount percentage
    deals_of_the_day = Product.objects.filter(
        is_active=True,
        discount_price__isnull=False,
        stock__gt=0
    ).order_by('-views_count')[:6]

    # Featured Products
    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True,
        stock__gt=0
    )[:8]
    if not featured_products.exists():
        featured_products = Product.objects.filter(is_active=True)[:8]

    # Best Sellers
    best_sellers = Product.objects.filter(
        is_active=True,
        is_bestseller=True
    )[:8]
    if not best_sellers.exists():
        best_sellers = Product.objects.filter(is_active=True).order_by('-views_count')[:8]

    # New Arrivals
    new_arrivals = Product.objects.filter(
        is_active=True,
        is_new_arrival=True
    ).order_by('-created_at')[:8]
    if not new_arrivals.exists():
        new_arrivals = Product.objects.filter(is_active=True).order_by('-created_at')[:8]

    # Testimonials / Verified Customer Reviews
    testimonials = Review.objects.select_related('user', 'product').filter(
        rating__gte=4,
        is_verified_purchase=True
    )[:6]

    # User wishlist ids
    wishlist_ids = set()
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist_ids = set(wishlist.products.values_list('id', flat=True))
        except Wishlist.DoesNotExist:
            pass

    context = {
        'featured_categories': featured_categories,
        'deals_of_the_day': deals_of_the_day,
        'featured_products': featured_products,
        'best_sellers': best_sellers,
        'new_arrivals': new_arrivals,
        'testimonials': testimonials,
        'wishlist_ids': wishlist_ids,
    }
    return render(request, 'core/home.html', context)


def about_view(request):
    return render(request, 'core/about.html')


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for reaching out! Our support team will get back to you within 24 hours.")
            return redirect('core:contact')
        else:
            messages.error(request, "Please check the contact form for any missing details.")
    else:
        form = ContactForm()

    return render(request, 'core/contact.html', {'form': form})


@require_POST
def newsletter_subscribe_view(request):
    email = request.POST.get('email', '').strip().lower()
    if not email:
        return JsonResponse({'success': False, 'message': 'Please provide an email address.'}, status=400)

    sub, created = NewsletterSubscriber.objects.get_or_create(email=email)
    if created:
        msg = "Welcome to ShopSphere VIP Club! Use code WELCOME10 for 10% off your first purchase."
    else:
        msg = "You are already subscribed with this email address. Thank you for being with us!"

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('format') == 'json':
        return JsonResponse({'success': True, 'message': msg})

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


def search_suggestions_api(request):
    """
    Live autocomplete API for the top search bar.
    """
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    products = Product.objects.filter(
        is_active=True,
        name__icontains=query
    )[:6]

    results = []
    for p in products:
        results.append({
            'name': p.name,
            'category': p.category.name,
            'price': f"${p.final_price:.2f}",
            'image': p.display_image,
            'url': f"/products/{p.slug}/",
        })

    return JsonResponse({'results': results})
