/**
 * StyleHouse — main frontend JS (Phase 1)
 */
(function () {
    'use strict';

    // Mobile navigation
    const navToggle = document.getElementById('navToggle');
    const mainNav = document.getElementById('mainNav');

    if (navToggle && mainNav) {
        navToggle.addEventListener('click', () => {
            const isOpen = mainNav.classList.toggle('open');
            navToggle.setAttribute('aria-expanded', String(isOpen));
        });
    }

    // Mobile category dropdown
    document.querySelectorAll('.nav-dropdown-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                btn.closest('.nav-dropdown').classList.toggle('open');
                btn.setAttribute(
                    'aria-expanded',
                    btn.closest('.nav-dropdown').classList.contains('open')
                );
            }
        });
    });

    // User menu (touch devices)
    document.querySelectorAll('.user-menu-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const menu = btn.closest('.user-menu');
            menu.classList.toggle('open');
            btn.setAttribute('aria-expanded', menu.classList.contains('open'));
        });
    });

    document.addEventListener('click', () => {
        document.querySelectorAll('.user-menu.open').forEach((m) => m.classList.remove('open'));
    });

    // Dismiss alerts
    document.querySelectorAll('.alert[data-auto-dismiss]').forEach((alert) => {
        const closeBtn = alert.querySelector('.alert-close');
        const dismiss = () => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        };
        if (closeBtn) closeBtn.addEventListener('click', dismiss);
        setTimeout(dismiss, 6000);
    });

    // Toast helper (used in Phase 3 for add-to-cart)
    window.showToast = function (message, duration = 3000) {
        const toast = document.getElementById('toast');
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add('show');
        toast.setAttribute('aria-hidden', 'false');
        setTimeout(() => {
            toast.classList.remove('show');
            toast.setAttribute('aria-hidden', 'true');
        }, duration);
    };

    // AJAX Add to Cart
    document.addEventListener('submit', (e) => {
        const form = e.target.closest('.add-to-cart-form');
        if (!form) return;

        e.preventDefault();

        const url = form.getAttribute('action');
        const formData = new FormData(form);

        // Fetch CSRF token
        let csrfToken = form.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) {
            const match = document.cookie.match(/csrftoken=([^;]+)/);
            csrfToken = match ? match[1] : '';
        }

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errData => {
                    throw new Error(errData.message || 'Failed to add item to cart');
                }).catch(() => {
                    throw new Error('Failed to add item to cart');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                window.showToast(data.message || 'Product added to cart!');
                // Update navbar badge count
                let badge = document.querySelector('.cart-badge');
                const cartLink = document.querySelector('.cart-link');
                if (data.cart_count > 0) {
                    if (badge) {
                        badge.textContent = data.cart_count;
                    } else if (cartLink) {
                        badge = document.createElement('span');
                        badge.className = 'cart-badge';
                        badge.textContent = data.cart_count;
                        cartLink.appendChild(badge);
                    }
                } else if (badge) {
                    badge.remove();
                }
            } else {
                window.showToast(data.message || 'Error adding to cart');
            }
        })
        .catch(err => {
            console.error('AJAX add-to-cart error:', err);
            window.showToast(err.message || 'Could not add to cart. Try refreshing the page.');
        });
    });
})();
