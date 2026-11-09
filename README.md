# ShopSphere – Advanced E-Commerce Management System

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-API-red?style=for-the-badge)](https://www.django-rest-framework.org/)
[![Bootstrap 5](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Database](https://img.shields.io/badge/Database-MySQL%20%7C%20SQLite-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Deployment](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)

**ShopSphere** is a complete, enterprise-grade, full-stack E-Commerce Web Application built with **Python, Django, Django REST Framework, MySQL / SQLite (with automated crash-free fallback), Bootstrap 5, Chart.js, and Razorpay**. Designed with an international luxury aesthetic inspired by Amazon and Flipkart, it is architected for high concurrency, security, and developer job portfolio excellence.

---

## Architecture Overview

```
                      +---------------------------------------+
                      |       ShopSphere Web Client           |
                      |  (HTML5, Bootstrap 5, JS, Chart.js)   |
                      +-------------------+-------------------+
                                          |
                                HTTP / AJAX / REST
                                          |
                      +-------------------v-------------------+
                      |      Django Application Server        |
                      |   (Gunicorn / WhiteNoise / Auth)      |
                      +-------------------+-------------------+
                                          |
       +-----------------+----------------+-----------------+-----------------+
       |                 |                |                 |                 |
+------v------+   +------v------+  +------v------+   +------v------+   +------v------+
|  Accounts   |   |  Products   |  | Shopping    |   |   Orders    |   |  Analytics  |
| Custom User |   | Categories  |  | Cart &      |   | Tracking    |   | Chart.js    |
| Addresses   |   | Reviews     |  | Coupons     |   | Razorpay/COD|   | Metrics     |
| Security    |   | Wishlist    |  | Sessions    |   | PDF Invoice |   | Management  |
+-------------+   +-------------+  +-------------+   +-------------+   +-------------+
                                          |
                      +-------------------v-------------------+
                      |            Database Layer             |
                      |      MySQL (with SQLite Fallback)     |
                      +---------------------------------------+
```

---

## Key Features & Modules

### 1. Customer & Authentication Module
- **Custom User Model**: Extended `AbstractUser` with unique email login, phone number, avatar, and verification states.
- **Secure Authentication**: Password hashing via Django PBKDF2/argon2, brute-force protections, and session management.
- **Multi-Address Book**: Manage multiple delivery addresses with default shipping and default billing toggles.
- **Profile Management**: Live edit avatar, contact numbers, and security credentials.
- **Password Reset**: Automated self-service workflow with secure tokens.

### 2. Product Catalog & Discovery
- **Hierarchical Taxonomies**: Multi-level Categories and Subcategories with icon indicators.
- **Multi-faceted Filtering**:
  - Live search across titles, brands, and descriptions.
  - Price range slider and min/max budget inputs.
  - Customer review rating thresholds (4★ & above, 3★ & above).
  - Instant stock availability toggle.
- **Multi-criteria Sorting**: Price (Low to High, High to Low), Newest arrivals, Highest customer ratings, and Popularity.
- **Product Details Page**:
  - Multi-angle gallery with dynamic thumbnail zoom switcher.
  - Stock level indicators with low-stock alerts.
  - Star rating breakdown with progress distributions.
  - Verified customer review submissions.
  - Related product recommendations.

### 3. Shopping Cart & Wishlist
- **Persistent Cart Engine**: Seamless guest session cart merging into user cart upon login.
- **AJAX Quantity Steppers**: Live increment/decrement without full page reload.
- **Free Shipping Gamification**: Dynamic progress bar calculating distance to free shipping.
- **Wishlist Toggle**: Heart button on all cards with instant count updates.

### 4. Coupon & Discount Engine
- **Flexible Promo Codes**: Percentage discounts and fixed-amount savings.
- **Real-Time Validation**: Enforces minimum order values, active date windows, and usage caps.
- **Pre-seeded Codes**:
  - `SPHERE20` – 20% off orders over $100
  - `WELCOME50` – $50 flat off orders over $250
  - `FESTIVE15` – 15% off orders over $50

### 5. Checkout & Payment Gateway
- **Cash on Delivery (COD)**: Doorstep collection with instant order confirmation.
- **Razorpay Integration**: Test-mode checkout with HMAC signature verification on the backend.
- **Stock Guard**: Atomic database transaction locking stock inventory during checkout to eliminate overselling.

### 6. Order Tracking & Branded PDF Invoices
- **Visual Shipment Pipeline**: Interactive 5-stage tracking tracker:
  `Pending -> Confirmed -> Processing -> Shipped -> Delivered`.
- **Public Tracking Portal**: Look up any order using Order ID + Email without requiring login.
- **Automated PDF Invoices**: Generates professional branded printable invoices with itemized tables, tax, and discount breakdown using **ReportLab**.
- **Customer Order Cancellation**: Allows user cancellation if order is in Pending or Confirmed status, returning stock to inventory.

### 7. Staff & Admin Analytics Dashboard
- **Chart.js Visualizations**:
  - 6-Month Monthly Revenue Trend line chart.
  - Order Status Distribution doughnut chart.
  - Catalog category distribution bar chart.
- **KPI Metrics**: Total Revenue, Total Orders, Verified Customers, and Low-Stock Warnings.
- **Live Status Control**: Inline fast status switcher to advance orders through fulfillment in real time.

### 8. Django REST Framework (DRF) APIs
- `GET /api/v1/products/` – Filterable & searchable product catalog.
- `GET /api/v1/categories/` – Category listing with subcategories.
- `GET /api/v1/cart/` – Authenticated user shopping cart state.
- `GET /api/v1/orders/` – Authenticated user order history.
- `GET /api/search-suggestions/?q=` – Instant search autocomplete suggestions.

---

## Database Configuration (MySQL + Graceful SQLite Fallback)

As requested, the project natively supports **MySQL** through `PyMySQL`. If local MySQL credentials are missing or the MySQL service is unreachable, ShopSphere **seamlessly and safely falls back to SQLite3 without throwing an unhandled exception**:

```python
# In shopsphere/settings.py
DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite').lower()

if DB_ENGINE == 'mysql':
    # Connects to MySQL via PyMySQL
    # If connection fails, automatically falls back to SQLite3
```

To use MySQL, simply set the following in your `.env` file:
```env
DB_ENGINE=mysql
DB_NAME=shopsphere_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

---

## Getting Started & Local Installation

### Prerequisites
- Python 3.10+
- Git

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-username/shopsphere.git
cd shopsphere

# Optional virtual environment
python -m venv venv
venv\Scripts\activate       # On Windows
# source venv/bin/activate  # On Linux/macOS
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Seed Rich Demo Data
Populate realistic categories, products, Unsplash images, reviews, coupons, and sample orders:
```bash
python manage.py seed_data
```

### 5. Collect Static Files
```bash
python manage.py collectstatic --no-input
```

### 6. Run the Development Server
```bash
python manage.py runserver
```

Open your browser at **`http://127.0.0.1:8000/`**.

---

## Demo Credentials

| Role | Email | Password | Access |
| :--- | :--- | :--- | :--- |
| **Superuser / Staff** | `admin@shopsphere.com` | `admin123` | Analytics Dashboard (`/analytics/dashboard/`) & Django Admin (`/admin/`) |
| **Customer** | `customer@shopsphere.com` | `customer123` | Store, Cart, Checkout, Wishlist, Order Tracking & Profile |

---

## Deployment to Render

The repository includes a ready-to-deploy **`render.yaml`** and **`Procfile`**:

1. Push your repository to **GitHub**.
2. Log into [Render.com](https://render.com) and click **New + -> Blueprint**.
3. Select your repository.
4. Render will automatically detect `render.yaml` and configure:
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python manage.py seed_data`
   - Start Command: `gunicorn shopsphere.wsgi:application`
5. Click **Apply** to deploy your live e-commerce platform!

---

## Project Structure

```
c:\PROJECT-3_E-commerce
├── accounts/               # Custom user model, address book, auth views
├── analytics/              # Staff analytics dashboard & Chart.js integration
├── api/                    # Django REST Framework endpoints & serializers
├── cart/                   # Session & user cart, coupons, quantity updates
├── core/                   # Home, about, contact, seed_data management command
├── orders/                 # Order model, tracking, Razorpay checkout, PDF invoice
├── products/               # Product catalog, categories, reviews, wishlist
├── shopsphere/             # Project settings, URLs, WSGI/ASGI
├── static/
│   ├── css/style.css       # Premium luxury custom CSS styling
│   └── js/main.js          # AJAX cart, wishlist, live search, countdown timer
├── templates/
│   ├── accounts/           # Login, register, profile, addresses, password reset
│   ├── analytics/          # Chart.js analytics dashboard
│   ├── cart/               # Shopping cart & coupon view
│   ├── core/               # Home, about, contact pages
│   ├── includes/           # Reusable product card partial
│   ├── orders/             # Checkout, Razorpay modal, tracking, confirmation
│   └── products/           # Product list, detail view, wishlist
├── Procfile                # Gunicorn deployment configuration
├── render.yaml             # Render Blueprint configuration
├── requirements.txt        # Production dependencies
├── .env.example            # Environment variables template
└── README.md               # Complete documentation
```

---

## License

This project is licensed under the MIT License. Built for professional software engineering portfolios and job interviews.
