/** @odoo-module **/

document.addEventListener("DOMContentLoaded", function () {
    // 1. Listen for Odoo 19's native add_to_cart_event from cart_service.js
    // This is 100% safe and doesn't require patching Owl components
    document.addEventListener("add_to_cart_event", function (ev) {
        if (typeof fbq !== 'undefined' && ev.detail) {
            const items = Array.isArray(ev.detail) ? ev.detail : [ev.detail];
            items.forEach(item => {
                const productId = item.product_id || item.item_id;
                const value = parseFloat(item.price || item.value || 0.0);
                const currency = item.currency || window.gf_fb_cartCurrency || 'USD';
                
                if (productId) {
                    fbq('track', 'AddToCart', {
                        content_type: 'product',
                        content_ids: [productId],
                        value: value,
                        currency: currency
                    });
                }
            });
        }
    });

    // 2. Intercept payment submit button clicks for the one-page checkout funnel
    document.addEventListener("click", function (event) {
        const target = event.target.closest('button[name="o_payment_submit_button"]');
        if (target && typeof fbq !== 'undefined') {
            const val = window.gf_fb_cartTotal || 0.0;
            const cur = window.gf_fb_cartCurrency || 'USD';
            
            // Fire shipping/payment events exactly when they click Pay Now
            fbq('track', 'AddShippingInfo', { value: val, currency: cur });
            fbq('track', 'AddPaymentInfo', { value: val, currency: cur });
        }
    });
});

