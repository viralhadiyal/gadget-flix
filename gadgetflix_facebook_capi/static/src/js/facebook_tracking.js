/** @odoo-module **/

/**
 * Facebook Tracking via GTM DataLayer
 *
 * Instead of calling fbq() directly, we push events to window.dataLayer.
 * GTM picks up these events and fires the Meta Pixel with the same event_id,
 * enabling proper deduplication with server-side CAPI events.
 */

document.addEventListener("DOMContentLoaded", function () {
    window.dataLayer = window.dataLayer || [];

    // 1. Listen for Odoo 19's native add_to_cart_event from cart_service.js
    //    Push to dataLayer so GTM can fire AddToCart via Meta Pixel tag
    document.addEventListener("add_to_cart_event", function (ev) {
        if (ev.detail) {
            const items = Array.isArray(ev.detail) ? ev.detail : [ev.detail];
            items.forEach(function (item) {
                const productId = item.product_id || item.item_id;
                const value = parseFloat(item.price || item.value || 0.0);
                const currency = item.currency || 'USD';

                if (productId) {
                    dataLayer.push({
                        event: 'add_to_cart',
                        product_id: productId,
                        value: value,
                        currency: currency,
                        // Use product-level event_id for real-time add-to-cart actions
                        event_id: 'atc_' + productId + '_' + Date.now()
                    });
                }
            });
        }
    });

    // 2. Intercept payment submit button clicks
    //    Push AddShippingInfo and AddPaymentInfo to dataLayer when user clicks Pay
    document.addEventListener("click", function (event) {
        var target = event.target.closest('button[name="o_payment_submit_button"]');
        if (target) {
            // Read order values from the checkout page context (set by QWeb template)
            var orderDataEl = document.querySelector('[data-order-total]');
            var val = orderDataEl ? parseFloat(orderDataEl.dataset.orderTotal) : 0.0;
            var cur = orderDataEl ? orderDataEl.dataset.orderCurrency : 'USD';
            var orderId = orderDataEl ? orderDataEl.dataset.orderId : '';

            dataLayer.push({
                event: 'add_shipping_info',
                value: val,
                currency: cur,
                event_id: 'ship_' + orderId + '_' + Date.now()
            });

            dataLayer.push({
                event: 'add_payment_info',
                value: val,
                currency: cur,
                event_id: 'payment_' + orderId + '_' + Date.now()
            });
        }
    });
});
