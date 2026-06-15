/** @odoo-module **/

/**
 * Gadgetflix — Facebook Pixel Browser-Side Event Tracking
 *
 * Every event fired here has a matching server-side CAPI call with the
 * same event_id so Meta can deduplicate them into a single conversion.
 *
 * Events handled in this file:
 *   - AddToCart        (on Odoo add_to_cart_event, matched via cookie)
 *   - AddShippingInfo  (on address form submit, matched via SHIPPING_{order_id})
 *   - AddPaymentInfo   (on Pay button click, matched via PAYMENT_{order_id})
 *   - Lead             (on Pay button click, matched via LEAD_{order_id})
 *
 * Events handled in website_templates.xml (inline QWeb scripts):
 *   - ViewContent      (product page, matched via cookie)
 *   - InitiateCheckout (checkout page, matched via CHECKOUT_{order_id})
 *   - Purchase         (confirmation page, matched via PURCHASE_{order_id})
 *
 * PageView is handled automatically by the Meta Pixel base code in GTM.
 */

(function () {
    'use strict';

    // Prevent double-registration if the script is loaded multiple times
    if (window.gf_fb_tracking_registered) {
        return;
    }
    window.gf_fb_tracking_registered = true;

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
    // AddToCart — listen for Odoo's native add_to_cart_event
    // Server-side: controllers/main.py add_to_cart()
    // Event ID matched via cookie gf_fb_atc_eid
    // ══════════════════════════════════════════════════════════════════════
    document.addEventListener('add_to_cart_event', function (ev) {
        if (typeof fbq === 'undefined' || !ev.detail) return;

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

            fbq('track', 'AddToCart', {
                content_type: 'product',
                content_ids: [String(productId)],
                value: value,
                currency: currency
            }, {
                eventID: eid
            });
        });
    }, true); // capturing phase to intercept before other handlers

    // ══════════════════════════════════════════════════════════════════════
    // AddShippingInfo — fires when checkout address form is submitted
    // Server-side: controllers/main.py shop_address_submit()
    // Event ID: SHIPPING_{order_id}
    // ══════════════════════════════════════════════════════════════════════
    document.addEventListener('submit', function (event) {
        var form = event.target;
        if (!form || form.tagName !== 'FORM') return;
        var action = form.getAttribute('action') || '';
        if (action.indexOf('/shop/address/submit') === -1) return;
        if (typeof fbq === 'undefined') return;

        var val = window.gf_fb_cartTotal || 0;
        var cur = window.gf_fb_cartCurrency || 'INR';
        var orderId = window.gf_fb_cartOrderId || 0;

        if (isLocked('shipping_' + orderId)) return;
        lock('shipping_' + orderId, 3000);

        fbq('track', 'AddShippingInfo', {
            value: val,
            currency: cur
        }, {
            eventID: 'SHIPPING_' + orderId
        });
    }, true);

    // ══════════════════════════════════════════════════════════════════════
    // AddPaymentInfo + Lead — fire when "Pay Now" button is clicked
    // Server-side: controllers/main.py shop_payment_transaction()
    // Event IDs: PAYMENT_{order_id} and LEAD_{order_id}
    // ══════════════════════════════════════════════════════════════════════
    document.addEventListener('click', function (event) {
        var target = event.target.closest('button[name="o_payment_submit_button"]');
        if (!target || typeof fbq === 'undefined') return;

        var val = window.gf_fb_cartTotal || 0;
        var cur = window.gf_fb_cartCurrency || 'INR';
        var orderId = window.gf_fb_cartOrderId || 0;

        if (isLocked('payment_' + orderId)) return;
        lock('payment_' + orderId, 3000);

        fbq('track', 'AddPaymentInfo', {
            value: val,
            currency: cur
        }, {
            eventID: 'PAYMENT_' + orderId
        });

        fbq('track', 'Lead', {
            value: val,
            currency: cur
        }, {
            eventID: 'LEAD_' + orderId
        });
    });

})();
