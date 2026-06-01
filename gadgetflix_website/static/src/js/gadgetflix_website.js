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

    const init = function () {
        initMobileMenu();
        initAccessoriesMenus();
        initHorizontalScroll();
        initMotionSections();
        initProductDescriptions();
        initCartPreview();
        initAddressToggleCleanup();
        initAddressCountryCleanup();
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, { once: true });
    } else {
        init();
    }
})();
