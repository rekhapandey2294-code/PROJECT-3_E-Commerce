from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import datetime

from accounts.models import CustomUser, Address
from products.models import Category, SubCategory, Product, ProductImage, Review
from cart.models import Coupon
from orders.models import Order, OrderItem


class Command(BaseCommand):
    help = 'Seeds database with realistic, production-grade ShopSphere demo data.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing ShopSphere comprehensive data seeding..."))

        # 1. Superuser & Demo User
        admin_user, created = CustomUser.objects.get_or_create(
            email='admin@shopsphere.com',
            defaults={
                'username': 'admin',
                'first_name': 'ShopSphere',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
                'is_email_verified': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created Superuser: admin@shopsphere.com / admin123"))

        customer_user, created = CustomUser.objects.get_or_create(
            email='customer@shopsphere.com',
            defaults={
                'username': 'johndoe',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone_number': '+1 555-0199',
                'is_email_verified': True,
            }
        )
        if created:
            customer_user.set_password('customer123')
            customer_user.save()
            self.stdout.write(self.style.SUCCESS("Created Demo Customer: customer@shopsphere.com / customer123"))

        reviewer_user, _ = CustomUser.objects.get_or_create(
            email='sarah.connor@example.com',
            defaults={
                'username': 'sarah_c',
                'first_name': 'Sarah',
                'last_name': 'Connor',
                'is_email_verified': True,
            }
        )
        reviewer_user.set_password('password123')
        reviewer_user.save()

        # 2. Demo Address for Customer
        Address.objects.get_or_create(
            user=customer_user,
            is_default_shipping=True,
            defaults={
                'full_name': 'John Doe',
                'phone_number': '+1 555-0199',
                'address_line_1': '742 Evergreen Terrace',
                'address_line_2': 'Apt 4B',
                'city': 'Springfield',
                'state': 'Oregon',
                'postal_code': '97477',
                'country': 'United States',
                'address_type': 'home',
                'is_default_billing': True,
            }
        )

        # 3. Categories & Subcategories
        categories_data = [
            {
                'name': 'Electronics & Gadgets',
                'icon': 'bi-laptop',
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80',
                'subcategories': ['Smartphones & Tablets', 'Laptops & Computers', 'Audio & Headphones', 'Wearable Technology', 'Photography & Drones']
            },
            {
                'name': 'Fashion & Apparel',
                'icon': 'bi-bag',
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=800&auto=format&fit=crop&q=80',
                'subcategories': ["Men's Wear", "Women's Collection", "Footwear & Sneakers", "Watches & Jewelry", "Luxury Bags"]
            },
            {
                'name': 'Home & Living',
                'icon': 'bi-house-door',
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?w=800&auto=format&fit=crop&q=80',
                'subcategories': ['Smart Home Devices', 'Ergonomic Furniture', 'Kitchen & Dining', 'Interior Lighting', 'Home Decor']
            },
            {
                'name': 'Beauty & Wellness',
                'icon': 'bi-heart-pulse',
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=800&auto=format&fit=crop&q=80',
                'subcategories': ['Organic Skincare', 'Luxury Fragrances', 'Hair & Body Care', 'Wellness & Vitamins']
            },
            {
                'name': 'Sports & Fitness',
                'icon': 'bi-bicycle',
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=800&auto=format&fit=crop&q=80',
                'subcategories': ['Gym Equipment', 'Activewear', 'Outdoor & Camping', 'Yoga & Cardio']
            },
            {
                'name': 'Books & Hobbies',
                'icon': 'bi-book',
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&auto=format&fit=crop&q=80',
                'subcategories': ['Bestselling Fiction', 'Tech & Business', 'Art & Design', 'Board Games']
            }
        ]

        cat_objs = {}
        subcat_objs = {}

        for c_data in categories_data:
            cat, _ = Category.objects.get_or_create(
                name=c_data['name'],
                defaults={
                    'icon': c_data['icon'],
                    'is_featured': c_data['is_featured'],
                    'image_url': c_data['image_url'],
                    'description': f"Explore our premium curated collection of {c_data['name']} with exclusive guarantees and swift shipping."
                }
            )
            cat_objs[c_data['name']] = cat
            for sc_name in c_data['subcategories']:
                sc, _ = SubCategory.objects.get_or_create(category=cat, name=sc_name)
                subcat_objs[sc_name] = sc

        # 4. Realistic Products
        products_data = [
            {
                'name': 'SonicMax Pro Wireless Noise-Cancelling Headphones',
                'brand': 'AuraSound',
                'category': 'Electronics & Gadgets',
                'subcategory': 'Audio & Headphones',
                'price': Decimal('299.99'),
                'discount_price': Decimal('229.99'),
                'stock': 45,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': False,
                'short_description': 'Industry-leading active noise cancellation with 40-hour battery life and spatial audio.',
                'description': 'Engineered for audio purists and daily commuters alike, the SonicMax Pro delivers studio-grade clarity, deep responsive bass, and supreme ultra-plush comfort. Featuring adaptive ambient listening mode and dual quick-charge microphones for crystalline calls.',
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80',
                'specs': {'Battery Life': '40 Hours', 'Connectivity': 'Bluetooth 5.3 + 3.5mm Aux', 'Weight': '250g', 'Warranty': '2 Years Official'},
                'gallery': [
                    'https://images.unsplash.com/photo-1484704849700-f032a568e944?w=800&auto=format&fit=crop&q=80',
                    'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=800&auto=format&fit=crop&q=80'
                ]
            },
            {
                'name': 'Titan Aero 15 Ultralight Carbon Laptop',
                'brand': 'TitanTech',
                'category': 'Electronics & Gadgets',
                'subcategory': 'Laptops & Computers',
                'price': Decimal('1499.00'),
                'discount_price': Decimal('1299.00'),
                'stock': 18,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': True,
                'short_description': 'Next-gen 12-core processor, 32GB DDR5 RAM, 1TB NVMe Gen4 SSD and 4K OLED HDR display.',
                'description': 'Housed in an aerospace-grade forged carbon chassis weighing just 1.1kg, Titan Aero 15 provides uncompromising performance for software developers, creative pros, and digital power users.',
                'image_url': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&auto=format&fit=crop&q=80',
                'specs': {'CPU': 'Intel Core i9 14th Gen', 'RAM': '32GB LPDDR5', 'Storage': '1TB NVMe SSD', 'Display': '15.6" 4K 120Hz OLED'},
                'gallery': [
                    'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&auto=format&fit=crop&q=80',
                    'https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=800&auto=format&fit=crop&q=80'
                ]
            },
            {
                'name': 'Horizon Ultra Smartwatch Series 8',
                'brand': 'Chronos',
                'category': 'Electronics & Gadgets',
                'subcategory': 'Wearable Technology',
                'price': Decimal('349.00'),
                'discount_price': Decimal('279.00'),
                'stock': 60,
                'is_featured': True,
                'is_bestseller': False,
                'is_new_arrival': True,
                'short_description': 'Sapphire crystal glass, titanium frame, ECG health monitor, and 100m water resistance.',
                'description': 'Track every heartbeat, run, and night of sleep with precision medical-grade sensors. Features Always-on LTPO display, cellular connectivity, and 5-day battery endurance.',
                'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop&q=80',
                'specs': {'Case Size': '45mm Titanium', 'Waterproof': '10 ATM (100m)', 'Sensors': 'ECG, SpO2, Heart Rate, GPS', 'Battery': 'Up to 5 Days'},
                'gallery': [
                    'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=800&auto=format&fit=crop&q=80'
                ]
            },
            {
                'name': 'Vanguard Mirrorless 4K Cinema Camera',
                'brand': 'Lumix Pro',
                'category': 'Electronics & Gadgets',
                'subcategory': 'Photography & Drones',
                'price': Decimal('1899.99'),
                'discount_price': Decimal('1699.99'),
                'stock': 8,
                'is_featured': False,
                'is_bestseller': False,
                'is_new_arrival': True,
                'short_description': 'Full-frame 45MP BSI CMOS sensor with 8K RAW video capture and in-body 5-axis stabilization.',
                'description': 'Designed for cinematographers and high-end commercial photographers who demand breathtaking dynamic range, 10-bit color science, and hyper-fast AI subject tracking autofocus.',
                'image_url': 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=800&auto=format&fit=crop&q=80',
                'specs': {'Resolution': '45 Megapixels', 'Video': '8K 30fps / 4K 120fps', 'Mount': 'Universal E-Mount', 'ISO': '50 - 102,400'},
                'gallery': []
            },
            {
                'name': 'Italian Tailored Wool Blazer Coat',
                'brand': 'Atelier Sartoria',
                'category': 'Fashion & Apparel',
                'subcategory': "Men's Wear",
                'price': Decimal('289.00'),
                'discount_price': Decimal('199.00'),
                'stock': 25,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': False,
                'short_description': '100% fine Merino wool cut in a slim contemporary silhouette with notched lapels.',
                'description': 'An indispensable classic crafted in Biella, Italy. The breathable weave transitions seamlessly from executive boardrooms to weekend evening galas.',
                'image_url': 'https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=800&auto=format&fit=crop&q=80',
                'specs': {'Material': '100% Italian Merino Wool', 'Fit': 'Modern Slim Fit', 'Lining': 'Cupro Silk Blend', 'Care': 'Dry Clean Only'},
                'gallery': []
            },
            {
                'name': 'Elysian Silk Evening Gown',
                'brand': 'Maison Privée',
                'category': 'Fashion & Apparel',
                'subcategory': "Women's Collection",
                'price': Decimal('349.50'),
                'discount_price': Decimal('249.00'),
                'stock': 14,
                'is_featured': True,
                'is_bestseller': False,
                'is_new_arrival': True,
                'short_description': 'Pure Mulberry silk maxi gown featuring a delicate drape and sculpted empire waistline.',
                'description': 'Effortless elegance personified. The flowing liquid silk silhouette moves with ethereal grace, complemented by subtle hand-stitched detailing.',
                'image_url': 'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=800&auto=format&fit=crop&q=80',
                'specs': {'Fabric': '100% Mulberry Silk', 'Length': 'Floor Length', 'Closure': 'Concealed Side Zipper'},
                'gallery': []
            },
            {
                'name': 'CloudRunner Boost Leather Sneakers',
                'brand': 'Strata',
                'category': 'Fashion & Apparel',
                'subcategory': 'Footwear & Sneakers',
                'price': Decimal('160.00'),
                'discount_price': Decimal('119.00'),
                'stock': 50,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': False,
                'short_description': 'Full-grain Italian calfskin leather with shock-absorbing ergonomic boost midsole.',
                'description': 'Combines minimalist Scandinavian aesthetics with responsive athletic footwear engineering for all-day city walks without fatigue.',
                'image_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&auto=format&fit=crop&q=80',
                'specs': {'Upper': 'Full-Grain Calfskin', 'Outsole': 'Vibram Non-Slip Rubber', 'Insole': 'Memory Foam Arch Support'},
                'gallery': []
            },
            {
                'name': 'Minimalist Ergonomic Executive Mesh Chair',
                'brand': 'Zenith Living',
                'category': 'Home & Living',
                'subcategory': 'Ergonomic Furniture',
                'price': Decimal('499.00'),
                'discount_price': Decimal('389.00'),
                'stock': 12,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': False,
                'short_description': 'Adjustable dynamic lumbar support, 4D armrests, and high-tensile breathable mesh.',
                'description': 'Engineered to support 10+ hours of continuous posture-aligned sitting. Certified BIFMA standard with synchro-tilt mechanism and aluminum five-star base.',
                'image_url': 'https://images.unsplash.com/photo-1580481077195-c3a821a58875?w=800&auto=format&fit=crop&q=80',
                'specs': {'Max Load': '330 lbs (150 kg)', 'Tilt Range': '90° - 135°', 'Mechanism': 'Multi-function Wire Control'},
                'gallery': []
            },
            {
                'name': 'Artisan Barista Espresso Machine with Steam Wand',
                'brand': 'CaféCraft',
                'category': 'Home & Living',
                'subcategory': 'Kitchen & Dining',
                'price': Decimal('699.00'),
                'discount_price': Decimal('549.00'),
                'stock': 20,
                'is_featured': True,
                'is_bestseller': False,
                'is_new_arrival': True,
                'short_description': '15-bar Italian pump with PID digital temperature control and microfoam milk texturing wand.',
                'description': 'Bring third-wave specialty coffee directly into your home kitchen. Extract rich golden crema shots and create velvety latte art effortlessly.',
                'image_url': 'https://images.unsplash.com/photo-1570968915860-54d5c301fa9f?w=800&auto=format&fit=crop&q=80',
                'specs': {'Pump Pressure': '15 Bar Italian ULKA', 'Water Tank': '2.0 Liters', 'Heating': 'Dual Thermo-Block System'},
                'gallery': []
            },
            {
                'name': 'Atmosphere Smart Ambient Floor Lamp',
                'brand': 'Lumina Pro',
                'category': 'Home & Living',
                'subcategory': 'Interior Lighting',
                'price': Decimal('149.00'),
                'discount_price': Decimal('99.00'),
                'stock': 35,
                'is_featured': False,
                'is_bestseller': True,
                'is_new_arrival': True,
                'short_description': '16 Million RGBIC dynamic lighting scenes with Alexa, Google Home & Music Sync.',
                'description': 'Cast immersive gradient illumination across your living room or study. Reacts dynamically to your gaming, music, or evening reading atmosphere.',
                'image_url': 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800&auto=format&fit=crop&q=80',
                'specs': {'Height': '145cm (57 inches)', 'Brightness': '1800 Lumens', 'Connectivity': 'Wi-Fi 2.4GHz + Bluetooth'},
                'gallery': []
            },
            {
                'name': 'Botanical Peptide Restorative Night Elixir',
                'brand': 'AuraCare',
                'category': 'Beauty & Wellness',
                'subcategory': 'Organic Skincare',
                'price': Decimal('85.00'),
                'discount_price': Decimal('68.00'),
                'stock': 80,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': False,
                'short_description': 'Infused with multi-peptides, cold-pressed marula oil, and hyaluronic acid for cellular renewal.',
                'description': 'Transform skin firmness and moisture barrier overnight. 100% clean, vegan, cruelty-free, and formulated without synthetic fragrances or parabens.',
                'image_url': 'https://images.unsplash.com/photo-1608248597359-0a67e2a9699a?w=800&auto=format&fit=crop&q=80',
                'specs': {'Volume': '50ml (1.7 fl oz)', 'Skin Type': 'All Skin Types', 'Key Ingredients': 'Copper Peptides, Marula, Squalane'},
                'gallery': []
            },
            {
                'name': 'Noir Santal Luxury Extrait de Parfum',
                'brand': 'Santal & Co.',
                'category': 'Beauty & Wellness',
                'subcategory': 'Luxury Fragrances',
                'price': Decimal('195.00'),
                'discount_price': None,
                'stock': 30,
                'is_featured': False,
                'is_bestseller': False,
                'is_new_arrival': True,
                'short_description': 'An intoxicating blend of Australian sandalwood, cardamom, violet, and smoky leather.',
                'description': 'A masterwork of niche perfumery with 30% oil concentration for magnetic 14-hour longevity. Sophisticated, alluring, and timeless.',
                'image_url': 'https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=800&auto=format&fit=crop&q=80',
                'specs': {'Concentration': 'Extrait de Parfum (30%)', 'Size': '100ml / 3.4 oz', 'Notes': 'Sandalwood, Amber, Cardamom'},
                'gallery': []
            }
        ]

        created_products = []
        for p_data in products_data:
            cat = cat_objs[p_data['category']]
            subcat = subcat_objs.get(p_data['subcategory'])
            prod, _ = Product.objects.get_or_create(
                name=p_data['name'],
                defaults={
                    'category': cat,
                    'subcategory': subcat,
                    'brand': p_data['brand'],
                    'price': p_data['price'],
                    'discount_price': p_data['discount_price'],
                    'stock': p_data['stock'],
                    'is_featured': p_data['is_featured'],
                    'is_bestseller': p_data['is_bestseller'],
                    'is_new_arrival': p_data['is_new_arrival'],
                    'short_description': p_data['short_description'],
                    'description': p_data['description'],
                    'specifications': p_data['specs'],
                    'featured_image_url': p_data['image_url'],
                    'views_count': 142
                }
            )
            created_products.append(prod)

            for g_url in p_data.get('gallery', []):
                ProductImage.objects.get_or_create(product=prod, image_url=g_url)

        # 5. Customer Reviews
        reviews_data = [
            (created_products[0], customer_user, 5, "Exceeded all expectations!", "The active noise cancellation is astonishing. I wear them on daily flights and long coding sessions without any ear fatigue."),
            (created_products[0], reviewer_user, 5, "Pure perfection", "Bass is punchy without muddying the mids. Build quality feels like a $500 set."),
            (created_products[1], customer_user, 5, "Lightest laptop I have ever owned", "Compiling Django and React applications takes seconds. Battery easily powers an 8-hour workday."),
            (created_products[2], reviewer_user, 4, "Sleek and accurate health tracking", "The titanium body looks stunning on formal wear and gym outfits alike. Battery lasts about 4 days on heavy use."),
            (created_products[7], customer_user, 5, "Saved my lower back!", "Working from home 9 hours a day used to give me terrible stiffness. This chair provides exact lumbar positioning."),
            (created_products[8], reviewer_user, 5, "Barista quality at home", "Extracts rich, syrupy espresso with thick golden crema. Steaming microfoam is super fast."),
        ]

        for prod, usr, rating, title, comment in reviews_data:
            Review.objects.get_or_create(
                product=prod,
                user=usr,
                defaults={
                    'rating': rating,
                    'title': title,
                    'comment': comment,
                    'is_verified_purchase': True
                }
            )

        # 6. Active Coupons
        coupons = [
            {'code': 'SPHERE20', 'discount_type': 'percentage', 'discount_value': Decimal('20.00'), 'min_purchase_amount': Decimal('100.00'), 'max_discount_amount': Decimal('80.00')},
            {'code': 'WELCOME50', 'discount_type': 'fixed', 'discount_value': Decimal('50.00'), 'min_purchase_amount': Decimal('250.00')},
            {'code': 'FESTIVE15', 'discount_type': 'percentage', 'discount_value': Decimal('15.00'), 'min_purchase_amount': Decimal('50.00')},
            {'code': 'SAVE10', 'discount_type': 'fixed', 'discount_value': Decimal('10.00'), 'min_purchase_amount': Decimal('30.00')},
        ]

        now = timezone.now()
        one_year_later = now + datetime.timedelta(days=365)
        for c in coupons:
            Coupon.objects.get_or_create(
                code=c['code'],
                defaults={
                    'discount_type': c['discount_type'],
                    'discount_value': c['discount_value'],
                    'min_purchase_amount': c.get('min_purchase_amount', Decimal('0.00')),
                    'max_discount_amount': c.get('max_discount_amount'),
                    'valid_from': now - datetime.timedelta(days=1),
                    'valid_to': one_year_later,
                    'active': True,
                    'usage_limit': 500,
                }
            )

        # 7. Sample Orders for customer to view history & tracking right away!
        if not Order.objects.filter(user=customer_user).exists():
            # Delivered Order
            o1 = Order.objects.create(
                user=customer_user,
                shipping_full_name='John Doe',
                shipping_phone='+1 555-0199',
                shipping_address_line1='742 Evergreen Terrace',
                shipping_address_line2='Apt 4B',
                shipping_city='Springfield',
                shipping_state='Oregon',
                shipping_postal_code='97477',
                shipping_country='United States',
                order_status='Delivered',
                payment_status='Paid',
                payment_method='Razorpay',
                razorpay_order_id='order_demo_101',
                razorpay_payment_id='pay_demo_success_99',
                subtotal=Decimal('229.99'),
                shipping_charge=Decimal('0.00'),
                discount_amount=Decimal('45.99'),
                coupon_code='SPHERE20',
                total_amount=Decimal('184.00'),
                created_at=now - datetime.timedelta(days=12)
            )
            OrderItem.objects.create(
                order=o1,
                product=created_products[0],
                product_name=created_products[0].name,
                product_image_url=created_products[0].display_image,
                unit_price=Decimal('229.99'),
                quantity=1,
                total_price=Decimal('229.99')
            )

            # Shipped / In-Transit Order
            o2 = Order.objects.create(
                user=customer_user,
                shipping_full_name='John Doe',
                shipping_phone='+1 555-0199',
                shipping_address_line1='742 Evergreen Terrace',
                shipping_address_line2='Apt 4B',
                shipping_city='Springfield',
                shipping_state='Oregon',
                shipping_postal_code='97477',
                shipping_country='United States',
                order_status='Shipped',
                payment_status='Paid',
                payment_method='Razorpay',
                subtotal=Decimal('389.00'),
                shipping_charge=Decimal('0.00'),
                discount_amount=Decimal('50.00'),
                coupon_code='WELCOME50',
                total_amount=Decimal('339.00'),
                created_at=now - datetime.timedelta(days=2)
            )
            OrderItem.objects.create(
                order=o2,
                product=created_products[7],
                product_name=created_products[7].name,
                product_image_url=created_products[7].display_image,
                unit_price=Decimal('389.00'),
                quantity=1,
                total_price=Decimal('389.00')
            )

        self.stdout.write(self.style.SUCCESS("ShopSphere data seeding finished successfully! Ready for production & demo."))
