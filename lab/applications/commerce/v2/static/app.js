// RETRACE Commerce Lab - Version B Client Script

document.addEventListener('DOMContentLoaded', () => {
  initCartBadge();

  if (document.getElementById('products-grid')) {
    initCatalog();
  }
  if (document.getElementById('cart-items-container')) {
    initCartView();
  }
  if (document.getElementById('checkout-form')) {
    initCheckoutView();
  }
  if (document.getElementById('confirmed-order-id')) {
    initOrderSuccessView();
  }
});

async function api(path, options = {}) {
  try {
    const res = await fetch(path, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    const data = await res.json();
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    return { ok: false, status: 500, error: err.message };
  }
}

async function initCartBadge() {
  const badge = document.getElementById('cart-badge');
  if (!badge) return;
  const res = await api('/api/cart');
  if (res.ok) {
    badge.textContent = res.data.items_count || 0;
  }
}

// -----------------------------------------------------------------------------
// Catalog Logic
// -----------------------------------------------------------------------------
async function initCatalog() {
  const grid = document.getElementById('products-grid');
  const searchInput = document.getElementById('search-input');
  const catButtons = document.querySelectorAll('.cat-btn');

  let currentCategory = '';
  let searchQuery = '';

  async function loadProducts() {
    let url = '/api/products?';
    if (currentCategory) url += `category=${encodeURIComponent(currentCategory)}&`;
    if (searchQuery) url += `query=${encodeURIComponent(searchQuery)}&`;

    const res = await api(url);
    if (!res.ok) return;

    grid.innerHTML = res.data.map(p => `
      <div class="p-5 rounded-xl bg-slate-800/90 border border-slate-700 flex flex-col justify-between hover:border-purple-500/50 transition">
        <div>
          ${p.badge ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-purple-950 text-purple-400 border border-purple-800 inline-block mb-2">${p.badge}</span>` : ''}
          <h3 class="text-base font-semibold text-white">${p.name}</h3>
          <p class="text-xs text-slate-400 mt-1 line-clamp-2">${p.description}</p>
        </div>
        <div class="mt-4 pt-4 border-t border-slate-700/80 flex items-center justify-between">
          <div>
            <span class="text-lg font-bold text-white">$${p.price.toFixed(2)}</span>
            <span class="block text-[10px] text-slate-400 font-mono">⭐ ${p.rating} (${p.inventory} in stock)</span>
          </div>
          <button
            class="add-btn px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold transition"
            data-id="${p.id}"
          >
            Add to Cart
          </button>
        </div>
      </div>
    `).join('');

    document.querySelectorAll('.add-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const pid = e.target.getAttribute('data-id');
        btn.textContent = 'Adding...';
        await api('/api/cart', {
          method: 'POST',
          body: JSON.stringify({ product_id: pid, quantity: 1 }),
        });
        btn.textContent = 'Added ✓';
        initCartBadge();
        setTimeout(() => { btn.textContent = 'Add to Cart'; }, 1000);
      });
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.trim();
      loadProducts();
    });
  }

  catButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      catButtons.forEach(b => {
        b.className = 'cat-btn px-3.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 hover:text-white';
      });
      btn.className = 'cat-btn px-3.5 py-1 rounded-full text-xs font-semibold bg-purple-600 text-white';
      currentCategory = btn.getAttribute('data-cat') || '';
      loadProducts();
    });
  });

  loadProducts();
}

// -----------------------------------------------------------------------------
// Cart Logic
// -----------------------------------------------------------------------------
async function initCartView() {
  const container = document.getElementById('cart-items-container');
  const subtotalEl = document.getElementById('summary-subtotal');
  const discountRow = document.getElementById('discount-row');
  const discountEl = document.getElementById('summary-discount');
  const taxEl = document.getElementById('summary-tax');
  const totalEl = document.getElementById('summary-total');
  const couponInput = document.getElementById('coupon-code-input');
  const applyBtn = document.getElementById('apply-coupon-btn');
  const couponMsg = document.getElementById('coupon-message');

  async function renderCart() {
    const res = await api('/api/cart');
    if (!res.ok) return;
    const cart = res.data;

    subtotalEl.textContent = `$${cart.subtotal.toFixed(2)}`;
    taxEl.textContent = `$${cart.tax_amount.toFixed(2)}`;
    totalEl.textContent = `$${cart.total.toFixed(2)}`;

    if (cart.discount_amount > 0) {
      discountRow.classList.remove('hidden');
      discountEl.textContent = `-$${cart.discount_amount.toFixed(2)} (${cart.applied_coupon})`;
    } else {
      discountRow.classList.add('hidden');
    }

    if (!cart.items || cart.items.length === 0) {
      container.innerHTML = `
        <div class="p-8 text-center rounded-xl bg-slate-800/50 border border-slate-700 text-slate-400 text-sm">
          Your shopping cart is empty. <a href="/" class="text-purple-400 font-semibold ml-1">Browse Catalog</a>
        </div>
      `;
      return;
    }

    // DEF-003: Hydration defect setting rendered quantity always to 1
    container.innerHTML = cart.items.map(item => `
      <div class="p-4 rounded-xl bg-slate-800/90 border border-slate-700 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-semibold text-white">${item.name}</h3>
          <span class="text-xs text-slate-400">$${item.price.toFixed(2)} each</span>
        </div>
        <div class="flex items-center gap-4">
          <span class="text-xs text-slate-300 font-semibold">Qty: 1</span>
          <span class="text-sm font-bold text-white">$${item.line_total.toFixed(2)}</span>
        </div>
      </div>
    `).join('');
  }

  if (applyBtn) {
    applyBtn.addEventListener('click', async () => {
      const code = couponInput.value.trim();
      if (!code) return;
      couponMsg.textContent = 'Applying...';
      couponMsg.className = 'text-xs text-slate-400';

      // DEF-001: Frontend sends {"code": code} but Version B backend expects {"couponCode": code}
      const res = await api('/api/coupons/apply', {
        method: 'POST',
        body: JSON.stringify({ code }),
      });

      if (res.ok) {
        couponMsg.textContent = `✓ ${res.data.message}`;
        couponMsg.className = 'text-xs text-emerald-400';
        renderCart();
      } else {
        couponMsg.textContent = `✗ ${res.data.detail || 'Failed to apply coupon'}`;
        couponMsg.className = 'text-xs text-rose-400';
      }
    });
  }

  renderCart();
}

// -----------------------------------------------------------------------------
// Checkout Logic
// -----------------------------------------------------------------------------
async function initCheckoutView() {
  const form = document.getElementById('checkout-form');
  const itemsList = document.getElementById('checkout-items-list');
  const subtotalEl = document.getElementById('checkout-subtotal');
  const discountRow = document.getElementById('checkout-discount-row');
  const discountEl = document.getElementById('checkout-discount');
  const taxEl = document.getElementById('checkout-tax');
  const totalEl = document.getElementById('checkout-total');

  const cartRes = await api('/api/cart');
  if (cartRes.ok) {
    const cart = cartRes.data;
    subtotalEl.textContent = `$${cart.subtotal.toFixed(2)}`;
    taxEl.textContent = `$${cart.tax_amount.toFixed(2)}`;
    totalEl.textContent = `$${cart.total.toFixed(2)}`;

    if (cart.discount_amount > 0) {
      discountRow.classList.remove('hidden');
      discountEl.textContent = `-$${cart.discount_amount.toFixed(2)}`;
    }

    itemsList.innerHTML = (cart.items || []).map(i => `
      <div class="flex justify-between">
        <span>${i.name} (x${i.quantity})</span>
        <span class="font-semibold text-slate-200">$${i.line_total.toFixed(2)}</span>
      </div>
    `).join('');
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      customer_name: document.getElementById('customer-name').value,
      customer_email: document.getElementById('customer-email').value,
      shipping_address: document.getElementById('shipping-address').value,
      payment_method: document.getElementById('payment-method').value,
      gift_wrapping: document.getElementById('gift-wrapping')?.checked || false,
    };

    const res = await api('/api/checkout', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (res.ok && res.data.order) {
      window.location.href = `/order_success.html?order_id=${res.data.order.order_id}&total=${res.data.order.total}`;
    } else {
      alert(res.data.detail || 'Checkout failed');
    }
  });
}

// -----------------------------------------------------------------------------
// Order Success Logic
// -----------------------------------------------------------------------------
function initOrderSuccessView() {
  const urlParams = new URLSearchParams(window.location.search);
  const orderId = urlParams.get('order_id') || 'ORD-N/A';
  const total = urlParams.get('total') || '0.00';

  document.getElementById('confirmed-order-id').textContent = orderId;
  document.getElementById('confirmed-order-total').textContent = `$${parseFloat(total).toFixed(2)}`;
}
