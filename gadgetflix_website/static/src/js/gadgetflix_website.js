(function () {
    "use strict";

    const initMobileMenu = function () {
        const toggle = document.querySelector("[data-gf-menu-toggle]");
        const menu = document.querySelector("[data-gf-mobile-menu]");
        const profileMenu = document.querySelector("[data-gf-profile-menu]");
        const profileToggle = document.querySelector("[data-gf-profile-toggle]");
        const profilePanel = document.querySelector("[data-gf-profile-panel]");

        if (!toggle || !menu) {
            return;
        }

        const isMobile = function () {
            return window.matchMedia("(max-width: 991px)").matches;
        };

        const setProfileOpen = function (open) {
            if (!profileMenu || !profileToggle) {
                return;
            }

            profileMenu.classList.toggle("is-open", open);
            profileToggle.setAttribute("aria-expanded", open ? "true" : "false");
        };

        const setOpen = function (open) {
            if (open) {
                setProfileOpen(false);
            }

            toggle.setAttribute("aria-expanded", open ? "true" : "false");
            toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
            menu.hidden = !open;
        };

        toggle.addEventListener("click", function () {
            setOpen(menu.hidden);
        });

        if (profileToggle && profileMenu && profilePanel) {
            profileToggle.addEventListener("click", function (event) {
                if (!isMobile()) {
                    return;
                }

                event.preventDefault();
                event.stopPropagation();
                const willOpen = !profileMenu.classList.contains("is-open");
                setOpen(false);
                setProfileOpen(willOpen);
            });

            profilePanel.addEventListener("click", function (event) {
                if (event.target.closest("a")) {
                    setProfileOpen(false);
                }
            });
        }

        menu.addEventListener("click", function (event) {
            if (event.target.closest("a")) {
                setOpen(false);
            }
        });

        document.addEventListener("click", function (event) {
            if (!menu.hidden && !menu.contains(event.target) && !toggle.contains(event.target)) {
                setOpen(false);
            }

            if (
                profileMenu &&
                profileMenu.classList.contains("is-open") &&
                !profileMenu.contains(event.target)
            ) {
                setProfileOpen(false);
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                setOpen(false);
                setProfileOpen(false);
            }
        });

        window.addEventListener("resize", function () {
            if (!isMobile()) {
                setOpen(false);
                setProfileOpen(false);
            }
        });
    };

    const initAccessoriesMenus = function () {
        const desktopMenus = document.querySelectorAll("[data-gf-accessories-menu]");

        const closeDesktopMenus = function () {
            desktopMenus.forEach(function (menu) {
                const button = menu.querySelector("[data-gf-accessories-toggle]");
                const panel = menu.querySelector("[data-gf-accessories-panel]");

                menu.classList.remove("is-open");
                if (button) {
                    button.setAttribute("aria-expanded", "false");
                }
                if (panel) {
                    panel.setAttribute("aria-hidden", "true");
                }
            });
        };

        desktopMenus.forEach(function (menu) {
            const button = menu.querySelector("[data-gf-accessories-toggle]");
            const panel = menu.querySelector("[data-gf-accessories-panel]");
            let closeTimer = null;

            if (!button || !panel) {
                return;
            }

            const setOpen = function (open) {
                if (open) {
                    closeDesktopMenus();
                }

                menu.classList.toggle("is-open", open);
                button.setAttribute("aria-expanded", open ? "true" : "false");
                panel.setAttribute("aria-hidden", open ? "false" : "true");
            };

            const openMenu = function () {
                clearTimeout(closeTimer);
                setOpen(true);
            };

            const scheduleClose = function () {
                clearTimeout(closeTimer);
                closeTimer = setTimeout(function () {
                    if (!menu.matches(":hover") && !panel.matches(":hover") && !menu.contains(document.activeElement) && !panel.contains(document.activeElement)) {
                        setOpen(false);
                    }
                }, 180);
            };

            menu.addEventListener("mouseenter", openMenu);
            menu.addEventListener("mouseleave", scheduleClose);
            panel.addEventListener("mouseenter", openMenu);
            panel.addEventListener("mouseleave", scheduleClose);

            button.addEventListener("click", function (event) {
                event.preventDefault();
                setOpen(!menu.classList.contains("is-open"));
            });

            menu.addEventListener("focusout", function (event) {
                if (!menu.contains(event.relatedTarget) && !panel.contains(event.relatedTarget)) {
                    setOpen(false);
                }
            });

            panel.addEventListener("focusout", function (event) {
                if (!panel.contains(event.relatedTarget) && !menu.contains(event.relatedTarget)) {
                    setOpen(false);
                }
            });
        });

        const mobileMenus = document.querySelectorAll("[data-gf-mobile-accessories-menu]");

        mobileMenus.forEach(function (menu) {
            const button = menu.querySelector("[data-gf-mobile-accessories-toggle]");
            const panel = menu.querySelector("[data-gf-mobile-accessories-panel]");

            if (!button || !panel) {
                return;
            }

            const setOpen = function (open) {
                button.setAttribute("aria-expanded", open ? "true" : "false");
                panel.hidden = !open;
            };

            button.addEventListener("click", function () {
                setOpen(panel.hidden);
            });
        });

        const mobileDeviceGroups = document.querySelectorAll("[data-gf-mobile-device-group]");

        mobileDeviceGroups.forEach(function (group) {
            const button = group.querySelector("[data-gf-mobile-device-toggle]");
            const panel = group.querySelector("[data-gf-mobile-device-panel]");

            if (!button || !panel) {
                return;
            }

            const setOpen = function (open) {
                button.setAttribute("aria-expanded", open ? "true" : "false");
                panel.hidden = !open;
            };

            button.addEventListener("click", function () {
                const parentPanel = group.closest("[data-gf-mobile-accessories-panel]");

                if (panel.hidden && parentPanel) {
                    parentPanel.querySelectorAll("[data-gf-mobile-device-group]").forEach(function (otherGroup) {
                        if (otherGroup === group) {
                            return;
                        }

                        const otherButton = otherGroup.querySelector("[data-gf-mobile-device-toggle]");
                        const otherPanel = otherGroup.querySelector("[data-gf-mobile-device-panel]");

                        if (otherButton && otherPanel) {
                            otherButton.setAttribute("aria-expanded", "false");
                            otherPanel.hidden = true;
                        }
                    });
                }

                setOpen(panel.hidden);
            });
        });

        document.addEventListener("click", function (event) {
            if (!event.target.closest("[data-gf-accessories-menu]")) {
                closeDesktopMenus();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                closeDesktopMenus();
            }
        });
    };

    const initHorizontalScroll = function () {
        const areas = document.querySelectorAll(".gf-scroll-area");

        areas.forEach(function (area) {
            const target = area.querySelector("[data-gf-scroll-target]");
            const previous = area.querySelector('[data-gf-scroll="prev"]');
            const next = area.querySelector('[data-gf-scroll="next"]');

            if (!target || !previous || !next) {
                return;
            }

            const updateButtons = function () {
                const maxScroll = target.scrollWidth - target.clientWidth;
                const hasOverflow = maxScroll > 2;
                area.classList.toggle("gf-scroll-area--has-overflow", hasOverflow);
                previous.disabled = !hasOverflow || target.scrollLeft <= 2;
                next.disabled = !hasOverflow || target.scrollLeft >= maxScroll - 2;
            };

            const scrollByStep = function (direction) {
                const step = Math.max(target.clientWidth * 0.82, 220);
                target.scrollBy({
                    left: direction === "prev" ? -step : step,
                    behavior: "smooth",
                });
            };

            previous.addEventListener("click", function () {
                scrollByStep("prev");
            });

            next.addEventListener("click", function () {
                scrollByStep("next");
            });

            target.addEventListener("scroll", updateButtons, { passive: true });
            window.addEventListener("resize", updateButtons);
            window.addEventListener("load", updateButtons, { once: true });
            requestAnimationFrame(updateButtons);
        });
    };

    const initProductDescriptions = function () {
        const descriptions = document.querySelectorAll("[data-gf-product-description]");

        descriptions.forEach(function (description) {
            const content = description.querySelector("[data-gf-product-description-content]");
            const toggle = description.querySelector("[data-gf-product-description-toggle]");

            if (!content || !toggle) {
                return;
            }

            const moreLabel = toggle.dataset.moreLabel || "See more";
            const lessLabel = toggle.dataset.lessLabel || "See less";

            const isExpanded = function () {
                return !content.classList.contains("is-collapsed");
            };

            const setExpanded = function (expanded) {
                content.classList.toggle("is-collapsed", !expanded);
                toggle.textContent = expanded ? lessLabel : moreLabel;
                toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
            };

            const updateToggle = function () {
                const expanded = isExpanded();

                if (expanded) {
                    content.classList.add("is-collapsed");
                }

                const hasOverflow = content.scrollHeight > content.clientHeight + 1;

                if (expanded) {
                    content.classList.remove("is-collapsed");
                }

                description.classList.toggle("is-overflowing", hasOverflow);
                toggle.hidden = !hasOverflow;
                toggle.setAttribute("aria-hidden", hasOverflow ? "false" : "true");
            };

            toggle.addEventListener("click", function () {
                setExpanded(!isExpanded());
            });

            content.querySelectorAll("img").forEach(function (image) {
                image.addEventListener("load", updateToggle, { once: true });
            });

            window.addEventListener("resize", updateToggle);
            window.addEventListener("load", updateToggle, { once: true });
            requestAnimationFrame(updateToggle);
        });
    };

    const initMotionSections = function () {
        const sections = document.querySelectorAll("[data-gf-motion]");

        if (!sections.length) {
            return;
        }

        const reveal = function (section) {
            section.classList.add("gf-motion-in");
        };

        sections.forEach(function (section) {
            section.classList.add("gf-motion-ready");
        });

        const reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        if (reducedMotion || !("IntersectionObserver" in window)) {
            sections.forEach(reveal);
            return;
        }

        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    reveal(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.28,
        });

        sections.forEach(function (section) {
            observer.observe(section);
        });
    };


    const initCartPreview = function () {
        const menus = document.querySelectorAll("[data-gf-cart-preview]");

        if (!menus.length) {
            return;
        }

        const escapeHtml = function (value) {
            const element = document.createElement("span");
            element.textContent = value == null ? "" : String(value);
            return element.innerHTML;
        };

        const formatQuantity = function (quantity) {
            const number = Number(quantity);
            return Number.isInteger(number) ? String(number) : String(quantity);
        };

        const renderCartPreview = function (menu, data) {
            const linesContainer = menu.querySelector("[data-gf-cart-preview-lines]");
            const totalElement = menu.querySelector("[data-gf-cart-preview-total]");

            if (!linesContainer) {
                return;
            }

            if (!data.lines || !data.lines.length) {
                linesContainer.innerHTML = '<p class="gf-cart-preview__empty">Your cart is empty.</p>';
            } else {
                linesContainer.innerHTML = data.lines.map(function (line) {
                    const url = escapeHtml(line.url || "/shop/cart");
                    const imageUrl = escapeHtml(line.image_url || "");
                    const name = escapeHtml(line.name || "");
                    const quantity = escapeHtml(formatQuantity(line.quantity || 0));
                    const price = escapeHtml(line.price || "");

                    return [
                        '<a class="gf-cart-preview__line" href="' + url + '">',
                            '<span class="gf-cart-preview__image">',
                                '<img src="' + imageUrl + '" alt="' + name + '" loading="lazy"/>',
                            '</span>',
                            '<span class="gf-cart-preview__info">',
                                '<span class="gf-cart-preview__name">' + name + '</span>',
                                '<span class="gf-cart-preview__meta">',
                                    '<span>Qty ' + quantity + '</span>',
                                    '<span>' + price + '</span>',
                                '</span>',
                            '</span>',
                        '</a>',
                    ].join("");
                }).join("");
            }

            if (totalElement) {
                totalElement.textContent = data.total || "";
            }
        };

        const loadCartPreview = function (menu) {
            if (menu.dataset.gfCartPreviewLoading === "1" || menu.dataset.gfCartPreviewLoaded === "1") {
                return;
            }

            const linesContainer = menu.querySelector("[data-gf-cart-preview-lines]");

            menu.dataset.gfCartPreviewLoading = "1";
            if (linesContainer && !linesContainer.children.length) {
                linesContainer.innerHTML = '<p class="gf-cart-preview__loading">Loading cart...</p>';
            }

            window.fetch("/gadgetflix/cart/preview", {
                headers: {
                    "Accept": "application/json",
                },
                credentials: "same-origin",
            }).then(function (response) {
                if (!response.ok) {
                    throw new Error("Cart preview request failed");
                }
                return response.json();
            }).then(function (data) {
                renderCartPreview(menu, data);
                menu.dataset.gfCartPreviewLoaded = "1";
            }).catch(function () {
                menu.dataset.gfCartPreviewLoaded = "0";
            }).finally(function () {
                menu.dataset.gfCartPreviewLoading = "0";
            });
        };

        menus.forEach(function (menu) {
            const link = menu.querySelector(".gf-cart-link");

            const openPreview = function () {
                if (link) {
                    link.setAttribute("aria-expanded", "true");
                }
                loadCartPreview(menu);
            };

            menu.addEventListener("mouseenter", openPreview);
            menu.addEventListener("focusin", openPreview);
            menu.addEventListener("mouseleave", function () {
                if (link) {
                    link.setAttribute("aria-expanded", "false");
                }
            });
        });

        // When Odoo's cart_service updates the cart (add to cart),
        // it dispatches add_to_cart_event — reset our preview cache so
        // it reloads fresh data on next open.
        document.addEventListener("add_to_cart_event", function () {
            menus.forEach(function (menu) {
                menu.dataset.gfCartPreviewLoaded = "0";
            });
        });
    };

    const initAddressToggleCleanup = function () {
        const hideToggle = function () {
            document.querySelectorAll("#use_delivery_as_billing, label[for='use_delivery_as_billing']").forEach(function (element) {
                const row = element.closest(".form-check") || element.closest("label") || element;

                if (row) {
                    row.style.setProperty("display", "none", "important");
                }
            });

            document.querySelectorAll("label, span").forEach(function (element) {
                if (element.textContent.trim() !== "Same as delivery address") {
                    return;
                }

                const row = element.closest(".form-check") || element.closest("label") || element;
                row.style.setProperty("display", "none", "important");
            });

            document.querySelectorAll(".o_portal_addresses #billing_container").forEach(function (element) {
                element.style.setProperty("display", "none", "important");
            });

            document.querySelectorAll(".o_portal_addresses .o_add_billing_address_btn").forEach(function (button) {
                const row = button.closest(".d-flex") || button;
                row.style.setProperty("display", "none", "important");
            });
        };

        hideToggle();

        if ("MutationObserver" in window) {
            const target = document.querySelector("#shop_checkout") || document.querySelector(".o_portal_addresses");

            if (target) {
                new MutationObserver(hideToggle).observe(target, {
                    childList: true,
                    subtree: true,
                });
            }
        }
    };

    const initAddressCountryCleanup = function () {
        document.querySelectorAll("form.address_autoformat select[name='country_id']").forEach(function (select) {
            const indiaOption = Array.from(select.options).find(function (option) {
                return option.getAttribute("code") === "IN" || option.textContent.trim().toLowerCase() === "india";
            });

            if (!indiaOption) {
                return;
            }

            Array.from(select.options).forEach(function (option) {
                if (option !== indiaOption) {
                    option.remove();
                }
            });

            if (select.value !== indiaOption.value) {
                select.value = indiaOption.value;
                select.dispatchEvent(new Event("change", { bubbles: true }));
            }
        });
    };

    const initAutoDeliveryFetcher = function () {
        const checkoutDiv = document.getElementById("shop_checkout");
        if (!checkoutDiv) {
            return;
        }

        const codCarrierId = parseInt(checkoutDiv.dataset.codCarrierId, 10);
        const prepaidCarrierId = parseInt(checkoutDiv.dataset.prepaidCarrierId, 10);
        let currentCarrierId = parseInt(checkoutDiv.dataset.currentCarrierId, 10);

        if (!codCarrierId || !prepaidCarrierId) {
            return;
        }

        // Helper: send JSONRPC call (Odoo 19 JSON-RPC format)
        const jsonrpc = function (url, method, params) {
            return window.fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                credentials: "same-origin",
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    id: Math.random(),
                    params: params || {},
                }),
            }).then(function (response) {
                return response.json();
            });
        };

        const updateCartSummary = function (result, targetEl) {
            const amountDelivery = targetEl.querySelector('tr[name="o_order_delivery"] .monetary_field');
            const amountUntaxed = targetEl.querySelector('tr[name="o_order_total_untaxed"] .monetary_field');
            const amountTax = targetEl.querySelector('tr[name="o_order_total_taxes"] .monetary_field');
            const amountTotal = targetEl.parentElement.querySelectorAll(
                'tr[name="o_order_total"] .monetary_field, #amount_total_summary.monetary_field'
            );

            if (amountDelivery) {
                if (amountDelivery.classList.contains('d-none')) {
                    amountDelivery.querySelector('span[name="o_message_no_dm_set"]')?.classList.add('d-none');
                    amountDelivery.classList.remove('d-none');
                }
                amountDelivery.innerHTML = result.amount_delivery;
            }
            if (amountUntaxed) amountUntaxed.innerHTML = result.amount_untaxed;
            if (amountTax) amountTax.innerHTML = result.amount_tax;
            amountTotal.forEach(total => total.innerHTML = result.amount_total);
        };

        const updateCartSummaries = function (result) {
            const parentElements = document.querySelectorAll(
                '#o_cart_summary_offcanvas, div.o_total_card'
            );
            parentElements.forEach(el => updateCartSummary(result, el));

            // Sync the payment form dataset and interaction context with the updated raw amount_total
            const paymentFormEl = document.getElementById('o_payment_form');
            if (paymentFormEl && result.amount_total_raw !== undefined) {
                const amountVal = parseFloat(result.amount_total_raw);
                paymentFormEl.dataset.amount = amountVal;

                try {
                    const { Component } = odoo.loader.modules.get("@odoo/owl");
                    const env = Component && Component.env;
                    if (env && env.services && env.services["public.interactions"]) {
                        const interactions = env.services["public.interactions"].interactions || [];
                        const paymentFormColibri = interactions.find(function (i) {
                            return i.interaction && i.interaction.el && i.interaction.el.id === 'o_payment_form';
                        });
                        if (paymentFormColibri && paymentFormColibri.interaction.paymentContext) {
                            paymentFormColibri.interaction.paymentContext.amount = amountVal;
                            if (paymentFormColibri.interaction.paymentContext.minorAmount !== undefined) {
                                paymentFormColibri.interaction.paymentContext.minorAmount = Math.round(amountVal * 100);
                            }
                        }
                    }
                } catch (err) {
                    console.error("Failed to sync payment interaction amount:", err);
                }
            }
        };

        const refreshCartSummary = function () {
            return jsonrpc("/gadgetflix/cart/summary_html", "call", {}).then(function (res) {
                if (res && res.result && res.result.success) {
                    const data = res.result;
                    const desktopSummary = document.querySelector("div.o_total_card div.d-none.d-lg-block");
                    if (desktopSummary) {
                        desktopSummary.innerHTML = data.cart_summary_content + data.total;
                    }
                    const mobileSummary = document.querySelector("#o_cart_summary_offcanvas div.offcanvas-body");
                    if (mobileSummary) {
                        mobileSummary.innerHTML = data.cart_summary_content + data.total;
                    }
                    bindPromoForm();
                }
            }).catch(function (err) {
                console.error("Failed to refresh cart summary:", err);
            });
        };

        const handlePromoSubmit = function (event) {
            event.preventDefault();
            const form = event.currentTarget;
            const input = form.querySelector('input[name="promo"]');
            const promoCode = input ? input.value.trim() : "";

            if (!promoCode) {
                return;
            }

            let errorAlert = form.parentElement.querySelector(".js_promo_error_alert");
            if (!errorAlert) {
                errorAlert = document.createElement("div");
                errorAlert.className = "alert alert-danger text-start small mt-2 js_promo_error_alert";
                form.parentElement.appendChild(errorAlert);
            }
            errorAlert.classList.add("d-none");

            jsonrpc("/gadgetflix/cart/apply_promo", "call", {
                promo: promoCode,
            }).then(function (res) {
                if (res && res.result) {
                    if (res.result.success) {
                        refreshCartSummary();
                    } else {
                        errorAlert.textContent = res.result.error || "Failed to apply promo code.";
                        errorAlert.classList.remove("d-none");
                    }
                }
            }).catch(function (err) {
                console.error("Failed to apply promo code:", err);
                errorAlert.textContent = "An error occurred while applying the promo code.";
                errorAlert.classList.remove("d-none");
            });
        };

        const bindPromoForm = function () {
            document.querySelectorAll('form[name="coupon_code"]').forEach(function (form) {
                form.removeEventListener("submit", handlePromoSubmit);
                form.addEventListener("submit", handlePromoSubmit);
            });
        };

        const updateCarrierIfNeeded = function (selectedRadio, isUserTriggered) {
            if (!selectedRadio || !isUserTriggered) {
                return;
            }
            const pmCode = selectedRadio.dataset.paymentMethodCode;
            const optionType = selectedRadio.dataset.paymentOptionType;

            const isCOD = (optionType === "payment_method" && pmCode === "cash_on_delivery");
            const targetCarrierId = isCOD ? codCarrierId : prepaidCarrierId;

            // Safe guard: only perform update if we have valid carrier IDs
            if (!targetCarrierId || isNaN(targetCarrierId)) {
                return;
            }

            if (currentCarrierId !== targetCarrierId) {
                // Set the carrier on the backend and update cart totals inline only
                // Do NOT call refreshCartSummary() — it replaces payment.form HTML
                // and breaks Odoo's payment interaction context.
                jsonrpc("/shop/set_delivery_method", "call", {
                    dm_id: targetCarrierId,
                }).then(function (result) {
                    if (result && result.result && result.result.success) {
                        currentCarrierId = targetCarrierId;
                        updateCartSummaries(result.result);
                    }
                }).catch(function (err) {
                    console.error("Failed to set delivery method:", err);
                });
            }
        };

        // Listen to user-triggered payment method changes only
        document.addEventListener("change", function (event) {
            const radio = event.target;
            if (radio && radio.name === "o_payment_radio" && radio.checked) {
                const pmCode = radio.dataset.paymentMethodCode;
                if (pmCode) {
                    updateCarrierIfNeeded(radio, true);
                }
            }
        });

        // Initial bind of the promo form submit
        bindPromoForm();
    };

    const init = function () {
        initMobileMenu();
        initAccessoriesMenus();
        initHorizontalScroll();
        initMotionSections();
        initProductDescriptions();
        initCartPreview();
        initAddressToggleCleanup();
        initAddressCountryCleanup();
        initAutoDeliveryFetcher();
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, { once: true });
    } else {
        init();
    }
})();


/** @odoo-module **/

// ── Anti-Yellow Case Landing Page ──────────────────────────────────────────
// Searchable brand + model dropdowns, image left panel, add to cart.
(function () {
    "use strict";

    const page = document.getElementById("gf-ayc-page");
    if (!page) return;

    // ── State ──────────────────────────────────────────────────────────────
    const state = {
        activeBrandProductId: 0,
        activeBrandValueId: 0,
        activeBrandName: "",
        activeVariantId: 0,
        activeModelValueId: 0,
        activePrice: 0,
        activeModelName: "",
        loading: false,
    };

    // ── Element refs ───────────────────────────────────────────────────────
    const configurator    = document.getElementById("gf-ayc-configurator");
    const heroImg         = document.getElementById("gf-ayc-hero-img");
    const priceEl         = document.getElementById("gf-ayc-price");
    const availEl         = document.getElementById("gf-ayc-avail");
    const qtyInput        = document.getElementById("gf-ayc-qty");
    const qtyDec          = document.getElementById("gf-ayc-qty-dec");
    const qtyInc          = document.getElementById("gf-ayc-qty-inc");
    const cartBtn         = document.getElementById("gf-ayc-add-to-cart");
    const stickyBar       = document.getElementById("gf-ayc-sticky-bar");
    const stickyBtn       = document.getElementById("gf-ayc-sticky-btn");
    const stickyName      = document.getElementById("gf-ayc-sticky-name");
    const stickyPrice     = document.getElementById("gf-ayc-sticky-price");
    // Brand dropdown
    const brandDropdown   = document.getElementById("gf-ayc-brand-dropdown");
    const brandTrigger    = document.getElementById("gf-ayc-brand-trigger");
    const brandLabel      = document.getElementById("gf-ayc-brand-label");
    const brandIcon       = document.getElementById("gf-ayc-brand-icon");
    const brandPanel      = document.getElementById("gf-ayc-brand-panel");
    const brandList       = document.getElementById("gf-ayc-brand-listbox");
    const brandSearch     = document.getElementById("gf-ayc-brand-search");
    // Model dropdown
    const modelDropdown   = document.getElementById("gf-ayc-model-dropdown");
    const modelTrigger    = document.getElementById("gf-ayc-model-trigger");
    const modelLabel      = document.getElementById("gf-ayc-model-label");
    const modelPanel      = document.getElementById("gf-ayc-model-panel");
    const modelList       = document.getElementById("gf-ayc-model-listbox");
    const modelSearch     = document.getElementById("gf-ayc-model-search");
    const modelSpinner    = document.getElementById("gf-ayc-model-spinner");
    // Thumbnails
    const thumbsEl        = document.getElementById("gf-ayc-thumbs");

    if (!configurator) return;

    // ── JSONRPC helper ─────────────────────────────────────────────────────
    const rpc = function (url, params) {
        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Accept": "application/json" },
            credentials: "same-origin",
            body: JSON.stringify({ jsonrpc: "2.0", method: "call", id: Date.now(), params: params || {} }),
        }).then(r => r.json()).then(r => {
            if (r.error) throw new Error((r.error.data && r.error.data.message) || r.error.message);
            return r.result;
        });
    };

    // ── Cart helper ────────────────────────────────────────────────────────
    const cartUpdate = function (templateId, variantId, qty) {
        return rpc("/shop/cart/add", {
            product_template_id: templateId,
            product_id: variantId,
            quantity: qty
        });
    };

    // ── UI helpers ─────────────────────────────────────────────────────────
    const setButtonsDisabled = function (disabled) {
        if (cartBtn)   cartBtn.disabled = disabled;
        if (stickyBtn) stickyBtn.disabled = disabled;
    };

    const formatPrice = function (price) {
        const sym = document.documentElement.dataset.currencySymbol || "₹";
        return sym + Number(price).toLocaleString("en-IN", {
            minimumFractionDigits: 2, maximumFractionDigits: 2,
        });
    };

    const updatePriceDisplay = function (price) {
        const f = formatPrice(price);
        if (priceEl)    priceEl.textContent = f;
        if (stickyPrice) stickyPrice.textContent = f;
    };

    const updateHeroImage = function (url) {
        const heroContainer = document.querySelector(".gf-ayc-hero");
        if (!heroContainer || !url) return;
        
        let imgEl = heroContainer.querySelector("img#gf-ayc-hero-img");
        if (!imgEl) {
            heroContainer.innerHTML = "";
            imgEl = document.createElement("img");
            imgEl.id = "gf-ayc-hero-img";
            imgEl.className = "img img-fluid w-100";
            imgEl.style.objectFit = "contain";
            imgEl.style.maxHeight = "600px";
            heroContainer.appendChild(imgEl);
        }
        
        imgEl.style.opacity = "0.5";
        const tmp = new Image();
        tmp.onload = function () {
            imgEl.src = url;
            imgEl.style.opacity = "1";
        };
        tmp.src = url;
    };

    const updateThumbnails = function (urls) {
        if (!urls || !urls.length) return;
        updateHeroImage(urls[0]); // Always update main image
        
        const thumbsEl = document.getElementById("gf-ayc-thumbs");
        if (!thumbsEl) return;
        thumbsEl.style.display = "flex";
        thumbsEl.innerHTML = "";
        
        urls.forEach(function (url, idx) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "gf-ayc-thumb" + (idx === 0 ? " gf-ayc-thumb--active" : "");
            btn.dataset.img = url;
            btn.setAttribute("aria-label", "Image " + (idx + 1));
            
            const img = document.createElement("img");
            img.src = url;
            img.alt = "";
            btn.appendChild(img);
            thumbsEl.appendChild(btn);
        });
    };

    // ── Thumbnail strip click handler ─────────────────────────────────────────
    document.addEventListener("click", function (e) {
        const thumb = e.target.closest(".gf-ayc-thumb");
        if (!thumb) return;
        const thumbsEl = document.getElementById("gf-ayc-thumbs");
        if (!thumbsEl) return;
        
        thumbsEl.querySelectorAll(".gf-ayc-thumb").forEach(t => t.classList.remove("gf-ayc-thumb--active"));
        thumb.classList.add("gf-ayc-thumb--active");
        updateHeroImage(thumb.dataset.img);
    });

    // ── Custom Dropdown helper ─────────────────────────────────────────────
    function makeDropdown(dropdownEl, triggerEl, panelEl, searchEl, listEl) {
        if (!dropdownEl || !triggerEl || !panelEl) return;

        const open = function () {
            if (dropdownEl.classList.contains("gf-ayc-dropdown--disabled")) return;
            dropdownEl.classList.add("gf-ayc-dropdown--open");
            triggerEl.setAttribute("aria-expanded", "true");
            if (searchEl) {
                searchEl.value = "";
                filterList(listEl, "");
                setTimeout(function () { searchEl.focus(); }, 50);
            }
        };

        const close = function () {
            dropdownEl.classList.remove("gf-ayc-dropdown--open");
            triggerEl.setAttribute("aria-expanded", "false");
        };

        const toggle = function () {
            dropdownEl.classList.contains("gf-ayc-dropdown--open") ? close() : open();
        };

        triggerEl.addEventListener("click", toggle);
        triggerEl.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); }
            if (e.key === "Escape") close();
        });

        if (searchEl) {
            searchEl.addEventListener("input", function () {
                filterList(listEl, searchEl.value.trim());
            });
        }

        // Close on outside click
        document.addEventListener("click", function (e) {
            if (!dropdownEl.contains(e.target)) close();
        });

        return { open, close };
    }

    function filterList(listEl, query) {
        if (!listEl) return;
        const q = query.toLowerCase();
        let visible = 0;
        listEl.querySelectorAll(".gf-ayc-dropdown__item").forEach(function (item) {
            const name = (item.dataset.brandName || item.dataset.modelName || item.textContent).toLowerCase();
            const match = !q || name.includes(q);
            item.style.display = match ? "" : "none";
            if (match) visible++;
        });
        // No-results message
        const noResults = listEl.closest(".gf-ayc-dropdown__panel").querySelector(".gf-ayc-dropdown__no-results");
        if (noResults) noResults.hidden = visible > 0;
    }

    // ── Init brand dropdown ────────────────────────────────────────────────
    const brandDD = makeDropdown(brandDropdown, brandTrigger, brandPanel, brandSearch, brandList);

    // ── Brand item click ───────────────────────────────────────────────────
    if (brandList) {
        brandList.addEventListener("click", function (e) {
            const item = e.target.closest(".gf-ayc-dropdown__item");
            if (!item) return;

            // Update trigger label + icon
            const name = item.dataset.brandName;
            if (brandLabel) brandLabel.textContent = name;

            brandList.querySelectorAll(".gf-ayc-dropdown__item").forEach(i => i.classList.remove("gf-ayc-dropdown__item--active"));
            item.classList.add("gf-ayc-dropdown__item--active");

            if (brandDD) brandDD.close();

            // Update state
            const productId = parseInt(item.dataset.productId, 10);
            state.activeBrandProductId = productId;
            state.activeBrandValueId   = parseInt(item.dataset.brandValueId, 10);
            state.activeBrandName      = name;

            // Immediately show brand image
            if (item.dataset.imageUrl) updateHeroImage(item.dataset.imageUrl);

            // Reset model dropdown
            state.activeVariantId = 0;
            state.activeModelName = "";
            if (modelLabel) modelLabel.textContent = "Loading models…";
            if (modelList)  modelList.innerHTML = "";
            if (modelDropdown) modelDropdown.classList.add("gf-ayc-dropdown--disabled");
            if (modelSpinner) modelSpinner.hidden = false;
            setButtonsDisabled(true);

            // Fetch models
            rpc("/gadgetflix/anti-yellow/get_models", { product_id: productId })
                .then(function (models) {
                    if (modelSpinner) modelSpinner.hidden = true;
                    if (!models || !models.length) {
                        if (modelLabel) modelLabel.textContent = "No models available";
                        return;
                    }
                    // Populate model list
                    modelList.innerHTML = "";
                    models.forEach(function (m, idx) {
                        const li = document.createElement("li");
                        li.className = "gf-ayc-dropdown__item";
                        li.setAttribute("role", "option");
                        li.setAttribute("aria-selected", idx === 0 ? "true" : "false");
                        li.dataset.modelName  = m.name;
                        li.dataset.variantId  = m.variant_id;
                        li.dataset.modelValueId = m.id;
                        li.dataset.price      = m.price;
                        li.dataset.productId  = productId;
                        li.dataset.imageUrl   = m.image_url || "";
                        if (m.extra_image_urls && m.extra_image_urls.length > 0) {
                            li.dataset.extraImages = JSON.stringify(m.extra_image_urls);
                        }
                        li.innerHTML = `<span class="gf-ayc-dropdown__item-name">${m.name}</span>`;
                        modelList.appendChild(li);
                    });

                    if (modelDropdown) modelDropdown.classList.remove("gf-ayc-dropdown--disabled");
                    if (modelLabel) modelLabel.textContent = "Choose a model…";

                    // Auto-select first model
                    const firstItem = modelList.querySelector(".gf-ayc-dropdown__item");
                    if (firstItem) selectModelItem(firstItem);
                })
                .catch(function (err) {
                    if (modelSpinner) modelSpinner.hidden = true;
                    if (modelLabel) modelLabel.textContent = "Failed to load models";
                    console.error("[GF Anti-Yellow] get_models error:", err);
                });
        });
    }

    // ── Model item click ───────────────────────────────────────────────────
    if (modelList) {
        modelList.addEventListener("click", function (e) {
            const item = e.target.closest(".gf-ayc-dropdown__item");
            if (!item) return;
            selectModelItem(item);
            if (modelDD) modelDD.close();
        });
    }

    const modelDD = makeDropdown(modelDropdown, modelTrigger, modelPanel, modelSearch, modelList);

    function selectModelItem(item) {
        modelList.querySelectorAll(".gf-ayc-dropdown__item").forEach(i => {
            i.classList.remove("gf-ayc-dropdown__item--active");
            i.setAttribute("aria-selected", "false");
        });
        item.classList.add("gf-ayc-dropdown__item--active");
        item.setAttribute("aria-selected", "true");

        const name = item.dataset.modelName;
        if (modelLabel) modelLabel.textContent = name;

        const titleModelSpan = document.getElementById("gf-ayc-title-model");
        if (titleModelSpan) {
            titleModelSpan.textContent = " - " + name;
        }

        state.activeVariantId    = parseInt(item.dataset.variantId, 10);
        state.activeProductId    = parseInt(item.dataset.productId, 10);
        state.activeModelValueId = parseInt(item.dataset.modelValueId, 10);
        state.activePrice        = parseFloat(item.dataset.price || 0);
        state.activeModelName    = name;

        updatePriceDisplay(state.activePrice);
        if (item.dataset.extraImages) {
            try {
                updateThumbnails(JSON.parse(item.dataset.extraImages));
            } catch (e) {
                if (item.dataset.imageUrl) updateHeroImage(item.dataset.imageUrl);
            }
        } else if (item.dataset.imageUrl) {
            updateThumbnails([item.dataset.imageUrl]);
        }
        setButtonsDisabled(!state.activeVariantId);

        if (stickyName) stickyName.textContent = state.activeBrandName + " " + name + " – Anti-Yellow Case";
        if (availEl) {
            availEl.innerHTML = state.activeVariantId
                ? '<i class="fa fa-check-circle" aria-hidden="true"></i> In stock'
                : '<i class="fa fa-times-circle" aria-hidden="true"></i> Unavailable';
        }

        // Fire Facebook Pixel ViewContent when they view a specific model
        if (typeof fbq !== 'undefined' && state.activeVariantId) {
            fbq('track', 'ViewContent', {
                content_name: state.activeBrandName + " " + state.activeModelName,
                content_ids: [state.activeVariantId],
                content_type: 'product',
                value: state.activePrice,
                currency: 'INR'
            });
        }
    }

    // ── Qty stepper ────────────────────────────────────────────────────────
    if (qtyDec && qtyInc && qtyInput) {
        qtyDec.addEventListener("click", function () {
            qtyInput.value = Math.max(1, (parseInt(qtyInput.value, 10) || 1) - 1);
        });
        qtyInc.addEventListener("click", function () {
            qtyInput.value = Math.min(99, (parseInt(qtyInput.value, 10) || 1) + 1);
        });
        qtyInput.addEventListener("change", function () {
            const v = parseInt(qtyInput.value, 10);
            if (isNaN(v) || v < 1) qtyInput.value = 1;
            if (v > 99) qtyInput.value = 99;
        });
    }

    // ── Add to Cart ────────────────────────────────────────────────────────
    const doAddToCart = function (redirect) {
        if (!state.activeVariantId || !state.activeProductId || state.loading) return;
        const qty = parseInt((qtyInput && qtyInput.value) || 1, 10);

        state.loading = true;
        setButtonsDisabled(true);
        if (cartBtn) cartBtn.querySelector("span").textContent = "Adding…";

        cartUpdate(state.activeProductId, state.activeVariantId, qty)
            .then(function (data) {
                state.loading = false;
                if (cartBtn) cartBtn.querySelector("span").textContent = "Added!";
                
                if (data && data.cart_quantity !== undefined) {
                    sessionStorage.setItem("website_sale_cart_quantity", data.cart_quantity);
                    document.querySelectorAll('.my_cart_quantity').forEach(badge => {
                        badge.textContent = data.cart_quantity;
                        badge.classList.remove('d-none');
                        const cartIconElement = badge.closest('li.o_wsale_my_cart');
                        if (cartIconElement) cartIconElement.classList.remove('d-none');
                    });
                }

                document.dispatchEvent(new CustomEvent("add_to_cart_event", {
                    detail: { product_id: state.activeVariantId, quantity: qty }
                }));
            })
            .catch(function (err) {
                state.loading = false;
                setButtonsDisabled(false);
                if (cartBtn) cartBtn.querySelector("span").textContent = "Add to Cart";
                alert("Failed to add to cart. Please try again.");
                console.error("[GF Anti-Yellow] Add to cart error:", err);
            });
    };

    if (cartBtn)   cartBtn.addEventListener("click",   function () { doAddToCart(true); });
    if (stickyBtn) stickyBtn.addEventListener("click",  function () { doAddToCart(true); });

    // ── Sticky bar visibility (mobile) ─────────────────────────────────────
    if (stickyBar) {
        const buyPanel = document.getElementById("gf-ayc-buy");
        if (buyPanel && window.IntersectionObserver) {
            new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    stickyBar.hidden = entry.isIntersecting;
                    stickyBar.setAttribute("aria-hidden", entry.isIntersecting ? "true" : "false");
                });
            }, { threshold: 0.1 }).observe(buyPanel);
        }
    }

    // ── Auto-select first brand on load ────────────────────────────────────
    if (brandList) {
        const firstBrand = brandList.querySelector(".gf-ayc-dropdown__item");
        if (firstBrand) {
            // Simulate click on the first brand to trigger model load
            firstBrand.click();
        }
    }
})();

// ── Global Offcanvas Cart Listener ─────────────────────────────────────
(function () {
    "use strict";

    let isFetchingMiniCart = false;
    let isUpdatingQuantity = false;

    const rpc = function (url, params) {
        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Accept": "application/json" },
            credentials: "same-origin",
            body: JSON.stringify({ jsonrpc: "2.0", method: "call", id: Date.now(), params: params || {} }),
        }).then(r => r.json()).then(r => {
            if (r.error) throw new Error((r.error.data && r.error.data.message) || r.error.message);
            return r.result;
        });
    };

    const fetchMiniCart = function() {
        if (isFetchingMiniCart) return;
        isFetchingMiniCart = true;
        
        const loadingEl = document.getElementById('gf_cart_loading');
        if (loadingEl) loadingEl.classList.remove('d-none');

        fetch('/shop/cart/mini')
            .then(res => res.text())
            .then(html => {
                const doc = new DOMParser().parseFromString(html, "text/html");
                const newContentEl = doc.body;
                const contentEl = document.getElementById('gf_cart_content');
                
                if (!newContentEl || !contentEl) return;
                
                const newContainer = newContentEl.querySelector('#gf_cart_lines_container');
                const oldContainer = contentEl.querySelector('#gf_cart_lines_container');
                
                if (!newContainer || !oldContainer) {
                    contentEl.innerHTML = newContentEl.innerHTML;
                    return;
                }

                // Update header and subtotal
                const newHeader = newContentEl.querySelector('h5');
                const oldHeader = contentEl.querySelector('h5');
                if (newHeader && oldHeader) oldHeader.innerHTML = newHeader.innerHTML;

                const newSubtotal = newContentEl.querySelector('#gf_cart_subtotal');
                const oldSubtotal = contentEl.querySelector('#gf_cart_subtotal');
                if (newSubtotal && oldSubtotal) oldSubtotal.innerHTML = newSubtotal.innerHTML;

                // Sync lines safely without destroying inputs
                const oldLines = Array.from(oldContainer.querySelectorAll('.gf-cart-line'));
                const newLines = Array.from(newContainer.querySelectorAll('.gf-cart-line'));
                
                oldLines.forEach(oldLine => {
                    if (!newContainer.querySelector(`.gf-cart-line[data-line-id="${oldLine.dataset.lineId}"]`)) {
                        oldLine.remove();
                    }
                });
                
                newLines.forEach((newLine, index) => {
                    const oldLine = oldContainer.querySelector(`.gf-cart-line[data-line-id="${newLine.dataset.lineId}"]`);
                    if (oldLine) {
                        const newPrice = newLine.querySelector('.gf-line-price');
                        const oldPrice = oldLine.querySelector('.gf-line-price');
                        if (newPrice && oldPrice) oldPrice.innerHTML = newPrice.innerHTML;
                        
                        const newQtyText = newLine.querySelector('.gf-cart-qty-text');
                        const oldQtyText = oldLine.querySelector('.gf-cart-qty-text');
                        if (newQtyText && oldQtyText) oldQtyText.innerHTML = newQtyText.innerHTML;
                    } else {
                        if (index === 0) oldContainer.prepend(newLine);
                        else {
                            const prevLine = oldContainer.querySelector(`.gf-cart-line[data-line-id="${newLines[index - 1].dataset.lineId}"]`);
                            if (prevLine) prevLine.after(newLine);
                            else oldContainer.appendChild(newLine);
                        }
                    }
                });
            })
            .finally(() => {
                isFetchingMiniCart = false;
                if (loadingEl) loadingEl.classList.add('d-none');
            });
    };

    const openOffcanvasCart = function () {
        const offcanvasEl = document.getElementById('gf_cart_offcanvas');
        if (!offcanvasEl) return;
        
        let bsOffcanvas = window.Offcanvas.getInstance(offcanvasEl);
        if (!bsOffcanvas) {
            bsOffcanvas = new window.Offcanvas(offcanvasEl);
        }
        bsOffcanvas.show();
        fetchMiniCart(false);
    };

    window.addEventListener("add_to_cart_event", function () {
        if (!isUpdatingQuantity) {
            openOffcanvasCart();
        }
    }, true);

    document.addEventListener("DOMContentLoaded", function () {
        const cartBadges = document.querySelectorAll('.my_cart_quantity');
        cartBadges.forEach(badge => {
            let lastVal = badge.textContent.trim();
            const observer = new MutationObserver(() => {
                const newVal = badge.textContent.trim();
                if (newVal !== lastVal) {
                    if (parseInt(newVal) > parseInt(lastVal || 0)) {
                        if (!isUpdatingQuantity) {
                            openOffcanvasCart();
                        }
                    }
                    lastVal = newVal;
                }
            });
            observer.observe(badge, { childList: true, characterData: true, subtree: true });
        });

        const cartLinks = document.querySelectorAll('.o_wsale_my_cart a, a[href="/shop/cart"]');
        cartLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                openOffcanvasCart();
            });
        });
    });

    const updateOffcanvasQuantity = function (input, newQty) {
        if (!input) return;
        const lineId = parseInt(input.dataset.lineId, 10);
        const productId = parseInt(input.dataset.productId, 10);
        
        isUpdatingQuantity = true;
        const loadingEl = document.getElementById('gf_cart_loading');
        if (loadingEl) loadingEl.classList.remove('d-none');
        input.disabled = true;

        rpc('/shop/cart/update', {
            line_id: lineId,
            product_id: productId,
            quantity: newQty,
        }).then(function(data) {
            if (data && data.cart_quantity !== undefined) {
                sessionStorage.setItem("website_sale_cart_quantity", data.cart_quantity);
                document.querySelectorAll('.my_cart_quantity').forEach(b => {
                    b.textContent = data.cart_quantity;
                    b.classList.remove('d-none');
                    const cartIconElement = b.closest('li.o_wsale_my_cart');
                    if (cartIconElement) cartIconElement.classList.remove('d-none');
                });
            }
            
            // Re-fetch mini cart while preserving focus
            fetchMiniCart();
        }).catch(function(err) {
            console.error("[GF] Failed to update cart quantity", err);
            if (loadingEl) loadingEl.classList.add('d-none');
        }).finally(() => {
            input.disabled = false;
            setTimeout(() => { isUpdatingQuantity = false; }, 100);
        });
    };

    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.gf-cart-qty-btn');
        if (!btn) return;
        e.preventDefault();
        
        const input = btn.parentElement.querySelector('.gf-cart-qty-input');
        if (!input || input.disabled) return;
        
        let qty = parseInt(input.value, 10) || 0;
        if (btn.classList.contains('gf-cart-qty-minus')) {
            qty = Math.max(0, qty - 1);
        } else {
            qty += 1;
        }
        
        input.value = qty;
        updateOffcanvasQuantity(input, qty);
    });

    document.addEventListener('change', function(e) {
        if (!e.target.classList.contains('gf-cart-qty-input')) return;
        const input = e.target;
        let qty = parseInt(input.value, 10) || 0;
        if (qty < 0) qty = 0;
        input.value = qty;
        updateOffcanvasQuantity(input, qty);
    });
})();
