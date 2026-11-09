from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, F
from django.utils import timezone
import json
import datetime

from orders.models import Order, OrderItem
from products.models import Product, Category
from accounts.models import CustomUser


def is_staff_or_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_staff_or_admin, login_url='accounts:login')
def admin_dashboard_view(request):
    # Quick Status Update via POST
    if request.method == 'POST' and 'update_order_id' in request.POST:
        order_id = request.POST.get('update_order_id')
        new_status = request.POST.get('new_status')
        order = get_object_or_404(Order, id=order_id)
        if new_status in dict(Order.ORDER_STATUS_CHOICES):
            order.order_status = new_status
            if new_status == 'Delivered' and order.payment_method == 'COD':
                order.payment_status = 'Paid'
            order.save()
            messages.success(request, f"Order #{order.order_number} status updated to '{new_status}'.")
        return redirect('analytics:dashboard')

    total_revenue = Order.objects.exclude(order_status='Cancelled').aggregate(rev=Sum('total_amount'))['rev'] or 0
    total_orders = Order.objects.count()
    total_customers = CustomUser.objects.filter(is_staff=False).count()
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(stock__lte=5, is_active=True).count()

    # Recent Orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:8]

    # Chart 1: Last 6 Months Revenue Trend
    months_labels = []
    revenue_data = []
    now = timezone.now()
    for i in range(5, -1, -1):
        # Calculate month date window
        month_dt = now - datetime.timedelta(days=i * 30)
        label = month_dt.strftime('%b %Y')
        months_labels.append(label)
        
        month_start = datetime.datetime(month_dt.year, month_dt.month, 1, tzinfo=datetime.timezone.utc)
        if month_dt.month == 12:
            month_end = datetime.datetime(month_dt.year + 1, 1, 1, tzinfo=datetime.timezone.utc)
        else:
            month_end = datetime.datetime(month_dt.year, month_dt.month + 1, 1, tzinfo=datetime.timezone.utc)

        rev = Order.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).exclude(order_status='Cancelled').aggregate(total=Sum('total_amount'))['total'] or 0
        revenue_data.append(float(rev))

    # Chart 2: Order Status Distribution
    status_counts = Order.objects.values('order_status').annotate(count=Count('id')).order_by('order_status')
    status_labels = [sc['order_status'] for sc in status_counts]
    status_values = [sc['count'] for sc in status_counts]

    # Chart 3: Category Product Distribution
    cat_distribution = Category.objects.annotate(prod_count=Count('products')).values('name', 'prod_count')
    category_labels = [c['name'] for c in cat_distribution]
    category_values = [c['prod_count'] for c in cat_distribution]

    # Top Selling Products
    top_products = OrderItem.objects.values(
        'product_name'
    ).annotate(
        total_sold=Sum('quantity'),
        total_earned=Sum('total_price')
    ).order_by('-total_sold')[:5]

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'order_status_choices': Order.ORDER_STATUS_CHOICES,
        
        # JSON strings for Chart.js
        'months_labels_json': json.dumps(months_labels),
        'revenue_data_json': json.dumps(revenue_data),
        'status_labels_json': json.dumps(status_labels),
        'status_values_json': json.dumps(status_values),
        'category_labels_json': json.dumps(category_labels),
        'category_values_json': json.dumps(category_values),
    }
    return render(request, 'analytics/dashboard.html', context)
