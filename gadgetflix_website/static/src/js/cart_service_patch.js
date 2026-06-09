/** @odoo-module **/

import { CartService } from "@website_sale/js/cart_service";
import { patch } from "@web/core/utils/patch";

patch(CartService.prototype, {
    _showCartNotification(props, options = {}) {
        // Intercept the toast notification and show the offcanvas instead
        const offcanvasEl = document.getElementById('gf_cart_offcanvas');
        if (offcanvasEl) {
            const loadingEl = document.getElementById('gf_cart_loading');
            if (loadingEl) loadingEl.classList.remove('d-none');
            
            let bsOffcanvas = window.Offcanvas.getInstance(offcanvasEl);
            if (!bsOffcanvas) {
                bsOffcanvas = new window.Offcanvas(offcanvasEl);
            }
            bsOffcanvas.show();

            fetch('/shop/cart/mini')
                .then(res => res.text())
                .then(html => {
                    const contentEl = document.getElementById('gf_cart_content');
                    if (contentEl) contentEl.innerHTML = html;
                    if (loadingEl) loadingEl.classList.add('d-none');
                })
                .catch(err => {
                    console.error("[GF] Failed to load mini cart content", err);
                    if (loadingEl) loadingEl.classList.add('d-none');
                });
        } else {
            // If for some reason the offcanvas is missing, fallback to native toast
            super._showCartNotification(props, options);
        }
    }
});
