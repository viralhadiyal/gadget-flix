/** @odoo-module **/

(function () {
    if (window.gf_fb_tracking_registered) {
        return;
    }
    window.gf_fb_tracking_registered = true;

    // Helper to get cookie value
    function getCookie(name) {
        const value = "; " + document.cookie;
        const parts = value.split("; " + name + "=");
        if (parts.length === 2) return parts.pop().split(";").shift();
        return null;
    }

    // Helper to delete cookie
    function deleteCookie(name) {
        document.cookie = name + "=; Max-Age=-99999999; path=/;";
    }

    const recentlyTracked = new Set();

    // 1. Listen for Odoo 19's native add_to_cart_event from cart_service.js (capturing phase)
    document.addEventListener("add_to_cart_event", function (ev) {
        if (typeof fbq !== 'undefined' && ev.detail) {
            const items = Array.isArray(ev.detail) ? ev.detail : [ev.detail];
            
            // Read event_id cookie set by server
            const cookieEventId = getCookie("gf_last_add_to_cart_event_id");
            if (cookieEventId) {
                deleteCookie("gf_last_add_to_cart_event_id");
            }

            items.forEach(item => {
                const productId = item.product_id || item.item_id;
                const value = parseFloat(item.price || item.value || 0.0);
                const currency = item.currency || window.gf_fb_cartCurrency || 'USD';
                
                if (productId) {
                    const lockKey = "add_to_cart_" + productId + "_" + value;
                    if (recentlyTracked.has(lockKey)) {
                        return;
                    }
                    recentlyTracked.add(lockKey);
                    setTimeout(() => {
                        recentlyTracked.delete(lockKey);
                    }, 1000); // 1-second lock

                    // Use the matching cookie Event ID, or fall back to generating one if cookie was missing
                    const eventId = cookieEventId || ("ADD_TO_CART_" + productId + "_" + Date.now());

                    fbq('track', 'AddToCart', {
                        content_type: 'product',
                        content_ids: [productId],
                        value: value,
                        currency: currency
                    }, {
                        eventID: eventId
                    });
                }
            });
        }
    }, true);

    // 2. Intercept payment submit button clicks for the one-page checkout funnel
    document.addEventListener("click", function (event) {
        const target = event.target.closest('button[name="o_payment_submit_button"]');
        if (target && typeof fbq !== 'undefined') {
            const val = window.gf_fb_cartTotal || 0.0;
            const cur = window.gf_fb_cartCurrency || 'USD';
            
            // Fire shipping/payment events exactly when they click Pay Now
            fbq('track', 'AddShippingInfo', { value: val, currency: cur });

            const eventIdOpts = {};
            if (window.gf_fb_cartOrderId) {
                eventIdOpts.eventID = 'PAYMENT_INFO_' + window.gf_fb_cartOrderId;
            }
            fbq('track', 'AddPaymentInfo', { value: val, currency: cur }, eventIdOpts);
        }
    });
})();

