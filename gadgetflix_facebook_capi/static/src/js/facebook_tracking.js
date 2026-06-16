/** @odoo-module **/

/**
 * Gadgetflix — Facebook Pixel Browser-Side Event Tracking
 *
 * Every event fired here has a matching server-side CAPI call with the
 * same event_id so Meta can deduplicate them into a single conversion.
 *
 * Events handled in this file:
 *   - ViewContent      (product/landing page — fires on page load via DOM element)
 *   - InitiateCheckout (checkout page — fires on page load, same moment as AddPaymentInfo)
 *   - AddPaymentInfo   (checkout page — fires on page load when address form is shown)
 *   - AddToCart        (on Odoo add_to_cart_event, capturing phase)
 *   - AddShippingInfo  (on Pay Now click — address submitted in combined checkout)
 *   - Lead             (on Pay Now click — payment method selected & initiated)
 *   - Purchase         (confirmation page — fires on page load via DOM element)
 *
 * PageView is handled automatically by the Meta Pixel base code in GTM.
 *
 * Deduplication: every browser event shares a stable event_id with its
 * server-side CAPI counterpart. Meta uses this to merge them into one conversion.
 */

(function () {
    'use strict';

    // Prevent double-registration if the script is loaded multiple times
    if (window.gf_fb_tracking_registered) {
        return;
    }
    window.gf_fb_tracking_registered = true;

    // Global queue and helper to handle GTM loading asynchronously
    window.gf_fbq_queue = window.gf_fbq_queue || [];
    window.trackFbEvent = window.trackFbEvent || function (eventName, customData, options) {
        if (typeof window.fbq !== 'undefined' && typeof window.fbq === 'function' && window.fbq !== window.gf_fbq_stub) {
            window.fbq('track', eventName, customData, options);
        } else {
            window.gf_fbq_queue.push({
                eventName: eventName,
                customData: customData,
                options: options
            });
        }
    };

    // Define a stub fbq if it doesn't exist, redirecting to trackFbEvent.
    // This catches direct fbq('track', ...) calls from custom page model-switches.
    if (typeof window.fbq === 'undefined') {
        window.fbq = function () {
            var args = Array.prototype.slice.call(arguments);
            if (args[0] === 'track') {
                window.trackFbEvent(args[1], args[2], args[3]);
            }
        };
        window.gf_fbq_stub = window.fbq;
    }

    // Start interval to flush the queue when window.fbq is available (and is not our stub)
    if (!window.gf_fbq_interval) {
        window.gf_fbq_interval = setInterval(function () {
            if (typeof window.fbq !== 'undefined' && typeof window.fbq === 'function' && window.fbq !== window.gf_fbq_stub) {
                clearInterval(window.gf_fbq_interval);
                window.gf_fbq_interval = null;
                while (window.gf_fbq_queue && window.gf_fbq_queue.length > 0) {
                    var ev = window.gf_fbq_queue.shift();
                    window.fbq('track', ev.eventName, ev.customData, ev.options);
                }
            }
        }, 100);

        // Clear interval after 15 seconds to avoid running forever
        setTimeout(function () {
            if (window.gf_fbq_interval) {
                clearInterval(window.gf_fbq_interval);
                window.gf_fbq_interval = null;
            }
        }, 15000);
    }

    // ── Cookie helpers ──────────────────────────────────────────────────
    function getCookie(name) {
        var value = '; ' + document.cookie;
        var parts = value.split('; ' + name + '=');
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    function deleteCookie(name) {
        document.cookie = name + '=; Max-Age=-1; path=/;';
    }

    // ── Debounce lock ───────────────────────────────────────────────────
    var recentlyTracked = {};

    function isLocked(key) {
        return !!recentlyTracked[key];
    }

    function lock(key, ms) {
        recentlyTracked[key] = true;
        setTimeout(function () {
            delete recentlyTracked[key];
        }, ms || 2000);
    }

    // ══════════════════════════════════════════════════════════════════════
    // STEP: Add to Cart
    // Trigger : User clicks Add to Cart button
    // Event   : AddToCart
    // Method  : Odoo dispatches native 'add_to_cart_event' after cart update
    // Dedup   : event_id matched via cookie gf_fb_atc_eid set by server
    // ══════════════════════════════════════════════════════════════════════
    document.addEventListener('add_to_cart_event', function (ev) {
        if (!ev.detail) return;

        var items = Array.isArray(ev.detail) ? ev.detail : [ev.detail];
        var cookieEventId = getCookie('gf_fb_atc_eid');
        if (cookieEventId) {
            deleteCookie('gf_fb_atc_eid');
        }

        items.forEach(function (item) {
            var productId = item.product_id || item.item_id;
            var value = parseFloat(item.price || item.value || 0);
            var currency = item.currency || window.gf_fb_cartCurrency || 'INR';

            if (!productId) return;

            var lockKey = 'atc_' + productId;
            if (isLocked(lockKey)) return;
            lock(lockKey, 2000);

            var eid = cookieEventId || ('ATC_' + productId + '_' + Date.now());

            window.trackFbEvent('AddToCart', {
                content_type: 'product',
                content_ids: [String(productId)],
                value: value,
                currency: currency
            }, {
                eventID: eid
            });
        });
    }, true); // capturing phase — intercepts before any other handler

    // ══════════════════════════════════════════════════════════════════════
    // STEP: Pay Now button clicked
    // Trigger : User clicks "Pay Now" on /shop/checkout
    //
    // Events fired (in order):
    //   1. AddShippingInfo  — address form submitted (combined checkout: address
    //                         and payment are on the same page, submitted together)
    //   2. Lead             — payment method selected and payment initiated
    //
    // NOTE: AddPaymentInfo is NOT here — it fires earlier at page load time
    // (see initPageDataEvents below) to signal that the user viewed the address form.
    //
    // Dedup: event_ids are SHIPPING_{orderId} and LEAD_{orderId} — stable per order.
    // Server-side equivalents fire in shop_payment_transaction() with the same ids.
    // ══════════════════════════════════════════════════════════════════════
    document.addEventListener('click', function (event) {
        var target = event.target.closest('button[name="o_payment_submit_button"]');
        if (!target) return;

        var val = window.gf_fb_cartTotal || 0;
        var cur = window.gf_fb_cartCurrency || 'INR';
        var orderId = window.gf_fb_cartOrderId || 0;

        // 1. AddShippingInfo — address confirmed at Pay click in combined checkout
        if (orderId && !isLocked('shipping_' + orderId)) {
            lock('shipping_' + orderId, 3000);
            window.trackFbEvent('AddShippingInfo', {
                value: val,
                currency: cur
            }, {
                eventID: 'SHIPPING_' + orderId
            });
        }

        // 2. Lead — payment initiated
        if (isLocked('lead_' + orderId)) return;
        lock('lead_' + orderId, 3000);

        window.trackFbEvent('Lead', {
            value: val,
            currency: cur
        }, {
            eventID: 'LEAD_' + orderId
        });
    });

    // ══════════════════════════════════════════════════════════════════════
    // DOM-based Events — parse hidden div elements with data attributes
    // ══════════════════════════════════════════════════════════════════════
    function initPageDataEvents() {
        // 1. ViewContent (Product / Landing Page)
        var viewEl = document.getElementById('gf_fb_view_content_data');
        if (viewEl) {
            var productName = viewEl.getAttribute('data-product-name') || '';
            var productId = viewEl.getAttribute('data-product-id') || '';
            var productPrice = parseFloat(viewEl.getAttribute('data-product-price') || 0);
            var currencyName = viewEl.getAttribute('data-currency-name') || 'INR';

            var eid = getCookie('gf_fb_view_content_eid');
            if (eid) {
                deleteCookie('gf_fb_view_content_eid');
            }
            var opts = eid ? { eventID: eid } : {};

            window.trackFbEvent('ViewContent', {
                content_name: productName,
                content_ids: [String(productId)],
                content_type: 'product',
                value: productPrice,
                currency: currencyName
            }, opts);
        }

        // 2. InitiateCheckout + AddPaymentInfo (Checkout Page)
        // AddPaymentInfo fires here because this is when the user sees the
        // address form. Server-side guard ensures this only fires when Odoo
        // did NOT redirect the user away to /shop/address.
        var checkoutEl = document.getElementById('gf_fb_checkout_data');
        if (checkoutEl) {
            var cartTotal = parseFloat(checkoutEl.getAttribute('data-cart-total') || 0);
            var cartCurrency = checkoutEl.getAttribute('data-cart-currency') || 'INR';
            var numItems = parseInt(checkoutEl.getAttribute('data-num-items') || 0);
            var cartOrderId = checkoutEl.getAttribute('data-cart-order-id') || '0';

            // Expose globally so Pay button click handler can read them
            window.gf_fb_cartTotal = cartTotal;
            window.gf_fb_cartCurrency = cartCurrency;
            window.gf_fb_cartOrderId = cartOrderId;

            if (window.location.pathname.indexOf('/shop/checkout') !== -1) {
                var lockKey = 'initiate_checkout_' + cartOrderId;
                if (!isLocked(lockKey)) {
                    lock(lockKey, 5000);

                    window.trackFbEvent('InitiateCheckout', {
                        value: cartTotal,
                        currency: cartCurrency,
                        num_items: numItems
                    }, {
                        eventID: 'CHECKOUT_' + cartOrderId
                    });

                    // AddPaymentInfo: user sees the address + payment form
                    window.trackFbEvent('AddPaymentInfo', {
                        value: cartTotal,
                        currency: cartCurrency
                    }, {
                        eventID: 'PAYMENT_' + cartOrderId
                    });
                }
            }
        }

        // 3. Purchase (Confirmation Page)
        var purchaseEl = document.getElementById('gf_fb_purchase_data');
        if (purchaseEl) {
            var orderTotal = parseFloat(purchaseEl.getAttribute('data-order-total') || 0);
            var orderCurrency = purchaseEl.getAttribute('data-order-currency') || 'INR';
            var orderId = purchaseEl.getAttribute('data-order-id') || '0';
            var productIdsStr = purchaseEl.getAttribute('data-product-ids') || '';
            var productIds = productIdsStr ? productIdsStr.split(',').map(function(id) { return String(id).trim(); }) : [];

            var purchaseLockKey = 'purchase_' + orderId;
            if (!isLocked(purchaseLockKey)) {
                lock(purchaseLockKey, 5000);
                window.trackFbEvent('Purchase', {
                    value: orderTotal,
                    currency: orderCurrency,
                    content_type: 'product',
                    content_ids: productIds
                }, {
                    eventID: 'PURCHASE_' + orderId
                });
            }
        }

        // Note: Pending ATC cookie fallback removed — the add_to_cart_event listener
        // above (lines 109–140) handles all AddToCart events reliably with correct prices.
        // A page-reload fallback would fire with value:0 since gf_fb_cartTotal is only
        // available on checkout pages, not on the page loaded after redirect.
    }

    // Run initialization as soon as DOM is ready (or immediately if already ready)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPageDataEvents);
    } else {
        initPageDataEvents();
    }

})();
