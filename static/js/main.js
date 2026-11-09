/**
 * ShopSphere - Interactive E-Commerce Client Scripts
 */

document.addEventListener('DOMContentLoaded', function () {
  initCSRFToken();
  initSearchAutocomplete();
  initDealCountdown();
  initWishlistButtons();
  initAddToCartForms();
  initGalleryThumbnails();
  initCartQuantitySteppers();
});

// ---------------- CSRF Cookie Helper ----------------
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

let csrfToken = null;
function initCSRFToken() {
  const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
  if (tokenInput) {
    csrfToken = tokenInput.value;
  } else {
    csrfToken = getCookie('csrftoken');
  }
}

// ---------------- Toast Notifications ----------------
function showToast(title, message, type = 'success') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container-custom';
    document.body.appendChild(container);
  }

  const iconClass =
    type === 'success'
      ? 'bi-check-circle-fill text-success'
      : type === 'error'
      ? 'bi-exclamation-triangle-fill text-danger'
      : 'bi-info-circle-fill text-primary';

  const toastEl = document.createElement('div');
  toastEl.className = 'toast align-items-center show shadow-lg border-0 mb-2';
  toastEl.setAttribute('role', 'alert');
  toastEl.style.backgroundColor = '#ffffff';
  toastEl.style.minWidth = '280px';
  toastEl.style.borderRadius = '12px';

  toastEl.innerHTML = `
    <div class="d-flex p-3 align-items-center">
      <i class="bi ${iconClass} fs-4 me-3"></i>
      <div class="flex-grow-1">
        <h6 class="mb-0 fw-bold text-dark" style="font-size: 0.9rem;">${title}</h6>
        <p class="mb-0 text-muted" style="font-size: 0.8125rem;">${message}</p>
      </div>
      <button type="button" class="btn-close ms-2" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;

  container.appendChild(toastEl);
  setTimeout(() => {
    toastEl.classList.remove('show');
    setTimeout(() => toastEl.remove(), 400);
  }, 4000);
}

// ---------------- Live Search Autocomplete ----------------
function initSearchAutocomplete() {
  const searchInput = document.getElementById('globalSearchInput');
  const resultsBox = document.getElementById('searchAutocompleteBox');

  if (!searchInput || !resultsBox) return;

  let debounceTimer;

  searchInput.addEventListener('input', function () {
    clearTimeout(debounceTimer);
    const query = this.value.trim();

    if (query.length < 2) {
      resultsBox.style.display = 'none';
      resultsBox.innerHTML = '';
      return;
    }

    debounceTimer = setTimeout(() => {
      fetch(`/api/search-suggestions/?q=${encodeURIComponent(query)}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.results && data.results.length > 0) {
            resultsBox.innerHTML = data.results
              .map(
                (item) => `
                <a href="${item.url}" class="autocomplete-item">
                  <img src="${item.image}" alt="${item.name}">
                  <div class="flex-grow-1 overflow-hidden">
                    <div class="fw-semibold text-truncate" style="font-size: 0.875rem;">${item.name}</div>
                    <small class="text-muted">${item.category}</small>
                  </div>
                  <span class="fw-bold text-primary" style="font-size: 0.875rem;">${item.price}</span>
                </a>
              `
              )
              .join('');
            resultsBox.style.display = 'block';
          } else {
            resultsBox.innerHTML = `
              <div class="p-3 text-center text-muted" style="font-size: 0.875rem;">
                No matches found for "${query}"
              </div>
            `;
            resultsBox.style.display = 'block';
          }
        })
        .catch(() => {
          resultsBox.style.display = 'none';
        });
    }, 250);
  });

  document.addEventListener('click', function (e) {
    if (!searchInput.contains(e.target) && !resultsBox.contains(e.target)) {
      resultsBox.style.display = 'none';
    }
  });
}

// ---------------- Deals Countdown Timer ----------------
function initDealCountdown() {
  const hoursEl = document.getElementById('dealHours');
  const minutesEl = document.getElementById('dealMinutes');
  const secondsEl = document.getElementById('dealSeconds');

  if (!hoursEl || !minutesEl || !secondsEl) return;

  // Set target to midnight tonight or next 24 hours
  let target = new Date();
  target.setHours(23, 59, 59, 999);

  function updateTimer() {
    const now = new Date();
    let diff = target - now;

    if (diff <= 0) {
      target = new Date();
      target.setHours(23, 59, 59, 999);
      diff = target - now;
    }

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    hoursEl.textContent = String(hours).padStart(2, '0');
    minutesEl.textContent = String(minutes).padStart(2, '0');
    secondsEl.textContent = String(seconds).padStart(2, '0');
  }

  updateTimer();
  setInterval(updateTimer, 1000);
}

// ---------------- Wishlist AJAX Toggle ----------------
function initWishlistButtons() {
  document.querySelectorAll('.btn-wishlist-toggle').forEach((btn) => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const productId = this.dataset.productId;
      if (!productId) return;

      fetch(`/products/wishlist/toggle/${productId}/?format=json`, {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        },
      })
        .then((res) => {
          if (res.redirected) {
            window.location.href = res.url;
            return;
          }
          return res.json();
        })
        .then((data) => {
          if (data && data.success) {
            const icon = this.querySelector('i');
            if (data.added) {
              this.classList.add('active');
              if (icon) {
                icon.classList.remove('bi-heart');
                icon.classList.add('bi-heart-fill');
              }
              showToast('Wishlist', data.message, 'success');
            } else {
              this.classList.remove('active');
              if (icon) {
                icon.classList.remove('bi-heart-fill');
                icon.classList.add('bi-heart');
              }
              showToast('Wishlist', data.message, 'info');
            }

            // Update badge counters across the page
            document.querySelectorAll('.wishlist-counter-badge').forEach((badge) => {
              badge.textContent = data.total_count;
              badge.style.display = data.total_count > 0 ? 'inline-block' : 'none';
            });
          }
        })
        .catch((err) => console.error(err));
    });
  });
}

// ---------------- Add To Cart AJAX ----------------
function initAddToCartForms() {
  document.querySelectorAll('.form-add-to-cart').forEach((form) => {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const submitBtn = this.querySelector('button[type="submit"]');
      const originalHtml = submitBtn ? submitBtn.innerHTML : '';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Adding...';
      }

      const formData = new FormData(this);
      formData.append('format', 'json');

      fetch(this.action, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken || getCookie('csrftoken'),
        },
        body: formData,
      })
        .then((res) => res.json())
        .then((data) => {
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHtml;
          }

          if (data.success) {
            showToast('Cart Updated', data.message, 'success');
            // Update cart badges
            document.querySelectorAll('.cart-counter-badge').forEach((badge) => {
              badge.textContent = data.cart_count;
              badge.style.display = data.cart_count > 0 ? 'inline-block' : 'none';
            });
          } else {
            showToast('Stock Notice', data.message || 'Could not add to cart.', 'error');
          }
        })
        .catch((err) => {
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHtml;
          }
          console.error(err);
        });
    });
  });
}

// ---------------- Product Detail Gallery Thumbnails ----------------
function initGalleryThumbnails() {
  const mainImg = document.getElementById('mainGalleryImg');
  const thumbs = document.querySelectorAll('.gallery-thumb');

  if (!mainImg || thumbs.length === 0) return;

  thumbs.forEach((thumb) => {
    thumb.addEventListener('click', function () {
      thumbs.forEach((t) => t.classList.remove('active'));
      this.classList.add('active');
      const newSrc = this.dataset.fullSrc || this.querySelector('img').src;
      mainImg.src = newSrc;
    });
  });
}

// ---------------- Cart Quantity Steppers (AJAX) ----------------
function initCartQuantitySteppers() {
  document.querySelectorAll('.cart-item-row').forEach((row) => {
    const itemId = row.dataset.itemId;
    const qtyInput = row.querySelector('.cart-qty-input');
    const minusBtn = row.querySelector('.cart-qty-minus');
    const plusBtn = row.querySelector('.cart-qty-plus');
    const deleteBtn = row.querySelector('.cart-item-delete');

    if (!qtyInput) return;

    function sendQtyUpdate(newQty) {
      const formData = new FormData();
      formData.append('quantity', newQty);

      fetch(`/cart/update/${itemId}/`, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken || getCookie('csrftoken'),
        },
        body: formData,
      })
        .then((res) => res.json())
        .then((data) => {
          if (!data.success) {
            showToast('Stock Limit', data.message, 'error');
            return;
          }

          if (data.item_deleted) {
            row.remove();
            showToast('Cart', 'Item removed from your cart.', 'info');
          } else {
            qtyInput.value = data.item_quantity;
            const itemTotalEl = row.querySelector('.cart-item-total');
            if (itemTotalEl) {
              itemTotalEl.textContent = `$${data.item_total}`;
            }
          }

          // Update summary values
          const subtotalEl = document.getElementById('summarySubtotal');
          const shippingEl = document.getElementById('summaryShipping');
          const discountEl = document.getElementById('summaryDiscount');
          const finalTotalEl = document.getElementById('summaryFinalTotal');
          const progressBar = document.getElementById('freeShippingProgressBar');
          const amountLeftEl = document.getElementById('freeShippingAmountLeft');

          if (subtotalEl) subtotalEl.textContent = `$${data.subtotal}`;
          if (shippingEl) shippingEl.textContent = `$${data.shipping_charge}`;
          if (discountEl) discountEl.textContent = `-$${data.discount_amount}`;
          if (finalTotalEl) finalTotalEl.textContent = `$${data.final_total}`;

          if (progressBar) progressBar.style.width = `${data.shipping_progress}%`;
          if (amountLeftEl) {
            if (parseFloat(data.amount_left) > 0) {
              amountLeftEl.textContent = `Add $${data.amount_left} more for FREE Shipping!`;
            } else {
              amountLeftEl.textContent = `🎉 You qualify for FREE Express Shipping!`;
            }
          }

          if (data.coupon_warning) {
            showToast('Coupon Notice', data.coupon_warning, 'info');
          }

          // Update header badges
          document.querySelectorAll('.cart-counter-badge').forEach((badge) => {
            badge.textContent = data.cart_count;
            badge.style.display = data.cart_count > 0 ? 'inline-block' : 'none';
          });

          // If cart emptied, reload to display empty state
          if (data.cart_count === 0) {
            window.location.reload();
          }
        })
        .catch((err) => console.error(err));
    }

    if (minusBtn) {
      minusBtn.addEventListener('click', () => {
        const current = parseInt(qtyInput.value) || 1;
        if (current > 1) {
          sendQtyUpdate(current - 1);
        }
      });
    }

    if (plusBtn) {
      plusBtn.addEventListener('click', () => {
        const current = parseInt(qtyInput.value) || 1;
        sendQtyUpdate(current + 1);
      });
    }

    if (deleteBtn) {
      deleteBtn.addEventListener('click', () => {
        sendQtyUpdate(0);
      });
    }
  });
}
