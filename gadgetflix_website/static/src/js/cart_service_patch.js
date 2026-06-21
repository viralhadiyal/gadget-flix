/** @odoo-module **/

import { CartService } from "@website_sale/js/cart_service";
import { patch } from "@web/core/utils/patch";

const escapeHtml = (value) => {
    const element = document.createElement("span");
    element.textContent = value == null ? "" : String(value);
    return element.innerHTML;
};

const formatQuantity = (quantity) => {
    const number = Number(quantity);
    return Number.isInteger(number) ? String(number) : String(quantity || 0);
};

const renderMiniCart = (contentEl, data) => {
    const lines = Array.isArray(data.lines) ? data.lines : [];

    if (!lines.length) {
        contentEl.innerHTML = [
            '<div class="p-4 text-center text-muted">',
                '<i class="fa fa-shopping-bag mb-2" aria-hidden="true"></i>',
                '<p class="mb-0">Your cart is empty.</p>',
            '</div>',
        ].join("");
        return;
    }

    const lineItems = lines.map((line) => {
        const url = escapeHtml(line.url || "/shop/cart");
        const imageUrl = escapeHtml(line.image_url || "");
        const name = escapeHtml(line.name || "");
        const quantity = escapeHtml(formatQuantity(line.quantity));
        const price = escapeHtml(line.price || "");

        return [
            '<a class="d-flex gap-3 py-3 text-decoration-none text-reset border-bottom" href="' + url + '">',
                '<span class="flex-shrink-0 rounded border overflow-hidden bg-light" style="width: 64px; height: 64px;">',
                    '<img class="w-100 h-100 object-fit-cover" src="' + imageUrl + '" alt="' + name + '" loading="lazy"/>',
                '</span>',
                '<span class="min-w-0 flex-grow-1">',
                    '<span class="d-block fw-semibold text-truncate">' + name + '</span>',
                    '<span class="d-flex justify-content-between gap-3 small text-muted mt-1">',
                        '<span>Qty ' + quantity + '</span>',
                        '<span>' + price + '</span>',
                    '</span>',
                '</span>',
            '</a>',
        ].join("");
    }).join("");

    contentEl.innerHTML = [
        '<div class="px-4">',
            lineItems,
        '</div>',
        '<div class="px-4 py-3 border-top bg-light">',
            '<div class="d-flex justify-content-between align-items-center mb-3">',
                '<span class="text-muted">Subtotal</span>',
                '<strong>' + escapeHtml(data.total || "") + '</strong>',
            '</div>',
            '<div class="d-grid gap-2">',
                '<a href="/shop/cart" class="btn btn-outline-primary">View Cart</a>',
                '<a href="/shop/checkout" class="btn btn-primary">Checkout</a>',
            '</div>',
        '</div>',
    ].join("");
};

patch(CartService.prototype, {
    _showCartNotification(props, options = {}) {
        const offcanvasEl = document.getElementById("gf_cart_offcanvas");
        const contentEl = document.getElementById("gf_cart_content");
        const loadingEl = document.getElementById("gf_cart_loading");
        const Offcanvas = window.bootstrap && window.bootstrap.Offcanvas;

        if (!offcanvasEl || !contentEl || !Offcanvas) {
            return super._showCartNotification(props, options);
        }

        const offcanvas = Offcanvas.getOrCreateInstance(offcanvasEl);
        contentEl.innerHTML = "";
        if (loadingEl) {
            loadingEl.classList.remove("d-none");
        }
        offcanvas.show();

        return fetch("/gadgetflix/cart/preview", {
            headers: {
                "Accept": "application/json",
            },
            credentials: "same-origin",
        }).then((response) => {
            if (!response.ok) {
                throw new Error("Mini cart request failed");
            }
            return response.json();
        }).then((data) => {
            renderMiniCart(contentEl, data || {});
        }).catch(() => {
            contentEl.innerHTML = [
                '<div class="p-4 text-center text-muted">',
                    '<p class="mb-3">Cart updated.</p>',
                    '<a href="/shop/cart" class="btn btn-primary">View Cart</a>',
                '</div>',
            ].join("");
        }).finally(() => {
            if (loadingEl) {
                loadingEl.classList.add("d-none");
            }
        });
    },
});
