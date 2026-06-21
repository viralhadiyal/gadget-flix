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

    const initIndianAddressLabels = function () {
        const labelMap = {
            name: "Full Name",
            email: "Email",
            phone: "Mobile Number",
            street: "House / Flat No. and Street",
            street2: "Area / Landmark",
            zip: "Pincode",
            city: "City / District",
            state_id: "State",
            country_id: "Country",
        };

        document.querySelectorAll("form.address_autoformat:not(.gf-precart-address-form)").forEach(function (form) {
            Object.keys(labelMap).forEach(function (fieldName) {
                const field = form.querySelector('[name="' + fieldName + '"]');
                if (!field || !field.id) {
                    return;
                }

                const label = form.querySelector('label[for="' + field.id + '"]');
                if (!label || label.dataset.gfIndianLabel === "true") {
                    return;
                }

                const isRequired = field.hasAttribute("required") || label.textContent.includes("*");
                label.textContent = labelMap[fieldName];
                if (isRequired) {
                    label.appendChild(document.createTextNode(" "));
                    const asterisk = document.createElement("span");
                    asterisk.className = "gf-required-asterisk";
                    asterisk.textContent = "*";
                    label.appendChild(asterisk);
                }
                label.dataset.gfIndianLabel = "true";
            });
        });
    };

    const gfAddressFieldRules = [
        {
            name: "street",
            wrapperSelector: "#div_street",
            minLength: 10,
            message: "Please fill address detail proper. (Minimum 10 characters)",
        },
        {
            name: "street2",
            wrapperSelector: "#div_street2",
            minLength: 5,
            message: "Please fill area / landmark detail proper. (Minimum 5 characters)",
        },
    ];

    const getAddressValidationMessageEl = function (fieldInput, rule) {
        const fieldWrap = fieldInput.closest(rule.wrapperSelector) || fieldInput.parentElement;
        if (!fieldWrap) {
            return null;
        }

        let messageEl = fieldWrap.querySelector(".gf-address-street-error");
        if (!messageEl) {
            messageEl = document.createElement("div");
            messageEl.className = "gf-address-street-error";
            messageEl.setAttribute("aria-live", "polite");
            fieldInput.insertAdjacentElement("afterend", messageEl);
        }
        return messageEl;
    };

    const validateAddressField = function (fieldInput, rule, showMessage) {
        const messageEl = getAddressValidationMessageEl(fieldInput, rule);
        const fieldLength = fieldInput.value.replace(/\s/g, "").length;
        const isValid = fieldLength >= rule.minLength;

        fieldInput.classList.toggle("is-invalid", !isValid && showMessage);
        fieldInput.setAttribute("aria-invalid", (!isValid && showMessage) ? "true" : "false");
        if (messageEl) {
            messageEl.textContent = !isValid && showMessage ? rule.message : "";
        }
        return isValid;
    };

    const validateAddressFormDetails = function (form, showMessage) {
        if (!form) {
            return true;
        }

        const invalidField = gfAddressFieldRules.map(function (rule) {
            const fieldInput = form.querySelector('input[name="' + rule.name + '"]');
            if (!fieldInput || validateAddressField(fieldInput, rule, showMessage)) {
                return null;
            }
            return fieldInput;
        }).find(Boolean);

        if (invalidField && showMessage) {
            invalidField.focus();
        }
        return !invalidField;
    };

    const initAddressStreetValidation = function () {
        document.querySelectorAll("form.address_autoformat").forEach(function (form) {
            gfAddressFieldRules.forEach(function (rule) {
                const fieldInput = form.querySelector('input[name="' + rule.name + '"]');
                if (!fieldInput || fieldInput.dataset.gfStreetValidationBound === "true") {
                    return;
                }

                fieldInput.dataset.gfStreetValidationBound = "true";
                fieldInput.addEventListener("input", function () {
                    validateAddressField(fieldInput, rule, false);
                });
                fieldInput.addEventListener("blur", function () {
                    validateAddressField(fieldInput, rule, true);
                });
            });
        });

        if (
            document.documentElement.dataset.gfStreetValidationObserverBound !== "true" &&
            "MutationObserver" in window
        ) {
            document.documentElement.dataset.gfStreetValidationObserverBound = "true";
            new MutationObserver(initAddressStreetValidation).observe(document.body, {
                childList: true,
                subtree: true,
            });
        }

        if (document.documentElement.dataset.gfStreetSubmitValidationBound === "true") {
            return;
        }

        document.documentElement.dataset.gfStreetSubmitValidationBound = "true";
        document.addEventListener("submit", function (event) {
            const form = event.target && event.target.closest && event.target.closest("form.address_autoformat");
            if (!form || validateAddressFormDetails(form, true)) {
                return;
            }

            event.preventDefault();
            event.stopPropagation();
        }, true);
    };

    const initInvoicePreferenceCleanup = function () {
        document.querySelectorAll('[name="invoice_sending_method"], [name="invoice_edi_format"]').forEach(function (field) {
            const row = field.closest(".row");
            if (row) {
                row.remove();
                return;
            }

            const wrapper = field.closest(".mb-3, .col-xl-6, .col-lg-6, div");
            if (wrapper) {
                wrapper.remove();
            }
        });
    };

    const getAddressFormVillage = function (form) {
        if (!form || !form.classList.contains("gf-precart-address-form")) {
            return "";
        }

        const villageReadonly = form.querySelector(".gf-village-readonly");
        if (villageReadonly && !villageReadonly.hidden) {
            return villageReadonly.value.trim();
        }

        const villageSelect = form.querySelector(".gf-village-select");
        if (villageSelect && !villageSelect.hidden && !villageSelect.disabled) {
            return villageSelect.value.trim();
        }

        return "";
    };

    const appendVillageToAddressStreet2 = function (form) {
        const street2Input = form && form.querySelector('[name="street2"]');
        const villageName = getAddressFormVillage(form);
        if (!street2Input || !villageName) {
            return;
        }

        const street2 = street2Input.value.trim();
        if (street2.toLowerCase().includes(villageName.toLowerCase())) {
            return;
        }

        street2Input.value = street2 ? street2 + ", " + villageName : villageName;
        street2Input.dispatchEvent(new Event("input", { bubbles: true }));
        street2Input.dispatchEvent(new Event("change", { bubbles: true }));
    };

    const initAddressLocalitySubmitSync = function () {
        if (document.documentElement.dataset.gfAddressLocalitySubmitBound === "true") {
            return;
        }

        document.documentElement.dataset.gfAddressLocalitySubmitBound = "true";
        document.addEventListener("submit", function (event) {
            const form = event.target && event.target.closest && event.target.closest("form.address_autoformat");
            appendVillageToAddressStreet2(form);
        }, true);
        document.addEventListener("click", function (event) {
            const button = event.target && event.target.closest && event.target.closest('button[type="submit"], input[type="submit"]');
            const form = button && button.closest("form.address_autoformat");
            appendVillageToAddressStreet2(form);
        }, true);
    };

    const initPincodeAddressLookup = function () {
        document.querySelectorAll("form.address_autoformat").forEach(function (form) {
            const hasPopupAddressForm = form.classList.contains("gf-precart-address-form");
            const zipInput = form.querySelector('input[name="zip"]');
            const cityInput = form.querySelector('input[name="city"]');
            const street2Input = form.querySelector('input[name="street2"]');
            const stateSelect = form.querySelector('select[name="state_id"]');
            const countrySelect = form.querySelector('select[name="country_id"]');

            if (!zipInput || !cityInput || !stateSelect || !countrySelect || zipInput.dataset.gfPincodeBound === "true") {
                return;
            }

            zipInput.dataset.gfPincodeBound = "true";
            zipInput.setAttribute("inputmode", "numeric");
            zipInput.setAttribute("maxlength", "6");
            zipInput.setAttribute("placeholder", "Enter 6-digit pincode");
            zipInput.setAttribute("autocomplete", "postal-code");

            const zipDiv = zipInput.closest("#div_zip") || zipInput.parentElement;
            const street2Div = form.querySelector("#div_street2");
            const cityDiv = form.querySelector("#div_city");
            const stateDiv = form.querySelector("#div_state");
            const countryDiv = form.querySelector("#div_country");
            let statusEl = zipDiv ? zipDiv.querySelector(".gf-pincode-status") : null;
            let debounceTimer = null;
            let lastLookup = "";
            let lastPostOffice = null;
            let abortController = null;
            let allowProgrammaticLocationChange = false;
            let villageDiv = form.querySelector("#div_village");
            let villageSelect = form.querySelector(".gf-village-select");
            let villageReadonly = form.querySelector(".gf-village-readonly");

            if (zipDiv && !statusEl) {
                statusEl = document.createElement("div");
                statusEl.className = "gf-pincode-status";
                statusEl.setAttribute("aria-live", "polite");
                zipInput.after(statusEl);
            }

            if (!villageDiv && zipDiv && hasPopupAddressForm) {
                villageDiv = document.createElement("div");
                villageDiv.id = "div_village";
                villageDiv.className = "gf-village-field";
                villageDiv.innerHTML = [
                    '<label for="gf_dynamic_village" class="col-form-label">Locality / Village</label>',
                    '<input id="gf_dynamic_village_readonly" class="form-control gf-address-readonly gf-village-readonly col-form-label" type="text" readonly hidden>',
                    '<select id="gf_dynamic_village" class="col-form-label form-select gf-village-select" disabled>',
                    '<option value="">Village/locality will appear after pincode</option>',
                    '</select>',
                ].join("");
                zipDiv.after(villageDiv);
                villageSelect = villageDiv.querySelector(".gf-village-select");
                villageReadonly = villageDiv.querySelector(".gf-village-readonly");
            }

            const enforceAddressFieldOrder = function () {
                if (!zipDiv || !zipDiv.parentElement) {
                    return;
                }

                if (street2Div && street2Div.parentElement === zipDiv.parentElement) {
                    street2Div.after(zipDiv);
                }
                if (hasPopupAddressForm && villageDiv && villageDiv.parentElement === zipDiv.parentElement) {
                    zipDiv.after(villageDiv);
                }
                if (hasPopupAddressForm && statusEl && villageDiv && villageDiv.parentElement === zipDiv.parentElement && statusEl.parentElement !== villageDiv.parentElement) {
                    villageDiv.after(statusEl);
                }

                const cityAnchor = hasPopupAddressForm && villageDiv ? villageDiv : zipDiv;
                const statusAnchor = statusEl && statusEl.parentElement === cityAnchor.parentElement ? statusEl : cityAnchor;
                if (cityDiv && statusAnchor && cityDiv.parentElement === statusAnchor.parentElement) {
                    statusAnchor.after(cityDiv);
                }
                if (stateDiv && cityDiv && stateDiv.parentElement === cityDiv.parentElement) {
                    cityDiv.after(stateDiv);
                }
                if (countryDiv && stateDiv && countryDiv.parentElement === stateDiv.parentElement) {
                    stateDiv.after(countryDiv);
                }
            };

            const setStatus = function (message, type) {
                if (!statusEl) {
                    return;
                }

                statusEl.textContent = message || "";
                statusEl.classList.toggle("gf-pincode-status--loading", type === "loading");
                statusEl.classList.toggle("gf-pincode-status--success", type === "success");
                statusEl.classList.toggle("gf-pincode-status--error", type === "error");
            };

            const dispatchFieldChange = function (field) {
                allowProgrammaticLocationChange = true;
                field.dispatchEvent(new Event("input", { bubbles: true }));
                field.dispatchEvent(new Event("change", { bubbles: true }));
                window.setTimeout(function () {
                    allowProgrammaticLocationChange = false;
                }, 0);
            };

            const normalize = function (value) {
                return (value || "").toString().trim().toLowerCase();
            };

            const getSelectedVillage = function () {
                if (villageReadonly && !villageReadonly.hidden) {
                    return villageReadonly.value.trim();
                }
                if (villageSelect && !villageSelect.hidden) {
                    return villageSelect.value.trim();
                }
                return "";
            };

            const appendVillageToStreet2 = function () {
                appendVillageToAddressStreet2(form);
                if (street2Input) {
                    dispatchFieldChange(street2Input);
                }
            };

            const selectCountryIndia = function () {
                const previousValue = countrySelect.value;
                const indiaOption = Array.from(countrySelect.options).find(function (option) {
                    return option.getAttribute("code") === "IN" || normalize(option.textContent) === "india";
                });

                if (indiaOption && countrySelect.value !== indiaOption.value) {
                    countrySelect.dataset.gfPreviousValue = previousValue;
                    countrySelect.value = indiaOption.value;
                    dispatchFieldChange(countrySelect);
                }
            };

            const selectStateByName = function (stateName, attempt) {
                const previousValue = stateSelect.value;
                const targetState = normalize(stateName);
                const stateOption = Array.from(stateSelect.options).find(function (option) {
                    return normalize(option.textContent) === targetState;
                });

                if (stateOption) {
                    stateSelect.dataset.gfPreviousValue = previousValue;
                    stateSelect.value = stateOption.value;
                    dispatchFieldChange(stateSelect);
                    return;
                }

                if ((attempt || 0) < 5) {
                    window.setTimeout(function () {
                        selectStateByName(stateName, (attempt || 0) + 1);
                    }, 180);
                }
            };

            const lockSelect = function (select) {
                select.dataset.gfPreviousValue = select.value;
                select.addEventListener("mousedown", function (event) {
                    event.preventDefault();
                });
                select.addEventListener("keydown", function (event) {
                    if (["Tab", "Shift"].includes(event.key)) {
                        return;
                    }
                    event.preventDefault();
                });
                select.addEventListener("change", function () {
                    if (allowProgrammaticLocationChange) {
                        select.dataset.gfPreviousValue = select.value;
                        return;
                    }

                    select.value = select.dataset.gfPreviousValue || "";
                });
            };

            const fillVillageOptions = function (postOffices, shouldEnforceOrder) {
                if (!hasPopupAddressForm || !villageDiv || !villageSelect) {
                    return;
                }

                const names = Array.from(new Set((postOffices || []).map(function (office) {
                    return office && office.Name;
                }).filter(Boolean)));

                villageSelect.options.length = 1;
                villageSelect.value = "";
                villageSelect.options[0].textContent = names.length ? "Select village/locality..." : "Village/locality will appear after pincode";
                villageSelect.hidden = false;
                villageSelect.disabled = !names.length;
                if (villageReadonly) {
                    villageReadonly.value = "";
                    villageReadonly.hidden = true;
                }

                names.forEach(function (name) {
                    villageSelect.appendChild(new Option(name, name));
                });

                if (names.length === 1 && villageReadonly) {
                    villageReadonly.value = names[0];
                    villageReadonly.hidden = false;
                    villageSelect.hidden = true;
                    villageSelect.disabled = true;
                    villageSelect.value = names[0];
                } else if (names.length) {
                    villageSelect.value = names[0];
                    villageSelect.hidden = false;
                    villageSelect.disabled = false;
                }

                if (shouldEnforceOrder !== false) {
                    enforceAddressFieldOrder();
                }
            };

            const fillAddressFromPincode = function (postOffices) {
                const postOffice = postOffices && postOffices[0];
                if (!postOffice) {
                    return;
                }

                lastPostOffice = postOffice;
                selectCountryIndia();
                cityInput.value = postOffice.District || postOffice.Name || "";
                dispatchFieldChange(cityInput);
                selectStateByName(postOffice.State || "", 0);
                fillVillageOptions(postOffices);
                setStatus("Location found: " + [(hasPopupAddressForm && getSelectedVillage()), postOffice.District, postOffice.State, postOffice.Country].filter(Boolean).join(", "), "success");
            };

            if (hasPopupAddressForm && villageSelect && !villageSelect.dataset.gfVillageBound) {
                villageSelect.dataset.gfVillageBound = "true";
                villageSelect.addEventListener("change", function () {
                    if (!lastPostOffice) {
                        return;
                    }
                    setStatus("Location found: " + [getSelectedVillage(), lastPostOffice.District, lastPostOffice.State, lastPostOffice.Country].filter(Boolean).join(", "), "success");
                });
            }

            const lookupPincode = function () {
                const shouldRestoreZipFocus = document.activeElement === zipInput;
                const pincode = zipInput.value.replace(/\D/g, "").slice(0, 6);

                if (zipInput.value !== pincode) {
                    zipInput.value = pincode;
                }

                if (pincode.length < 6) {
                    lastLookup = "";
                    fillVillageOptions([], false);
                    setStatus("", "");
                    return;
                }

                if (pincode === lastLookup) {
                    return;
                }

                lastLookup = pincode;

                if (abortController) {
                    abortController.abort();
                }

                abortController = new AbortController();
                setStatus("Fetching city, state and locality...", "loading");

                window.fetch("https://api.postalpincode.in/pincode/" + encodeURIComponent(pincode), {
                    method: "GET",
                    signal: abortController.signal,
                }).then(function (response) {
                    if (!response.ok) {
                        throw new Error("Pincode lookup failed");
                    }
                    return response.json();
                }).then(function (payload) {
                    const result = Array.isArray(payload) ? payload[0] : null;
                    const postOffices = result && result.Status === "Success" && result.PostOffice;

                    if (!postOffices || !postOffices.length) {
                        fillVillageOptions([]);
                        setStatus("No city/state found for this pincode.", "error");
                        return;
                    }

                    fillAddressFromPincode(postOffices);
                    if (shouldRestoreZipFocus) {
                        window.setTimeout(function () {
                            zipInput.focus({ preventScroll: true });
                        }, 0);
                    }
                }).catch(function (error) {
                    if (error.name === "AbortError") {
                        return;
                    }
                    setStatus("Could not fetch pincode details. Please enter city/state manually.", "error");
                });
            };

            enforceAddressFieldOrder();
            window.setTimeout(enforceAddressFieldOrder, 700);

            zipInput.addEventListener("input", function () {
                window.clearTimeout(debounceTimer);
                debounceTimer = window.setTimeout(lookupPincode, 350);
            });

            zipInput.addEventListener("blur", lookupPincode);
            countrySelect.addEventListener("change", function () {
                window.setTimeout(enforceAddressFieldOrder, 700);
            });
            form.addEventListener("submit", appendVillageToStreet2);
            lockSelect(stateSelect);
            lockSelect(countrySelect);

            if (zipInput.value) {
                lookupPincode();
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

            syncPaymentAmount(result);
        };

        const syncPaymentAmount = function (result) {
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
                // Replacing payment.form HTML breaks Odoo's payment interaction context.
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
    };

    const initPreCartAddressGate = function () {
        const modal = document.getElementById("gf-precart-address-modal");
        if (!modal || modal.dataset.gfPrecartBound === "true") {
            return;
        }

        const form = modal.querySelector(".gf-precart-address-form");
        const errorEl = modal.querySelector("[data-gf-precart-error]");
        const submitButtons = modal.querySelectorAll(".gf-precart-modal__submit");
        const actionsEl = modal.querySelector(".gf-precart-modal__actions");
        let nextAction = "cart";
        let pendingAction = null;
        let bypassNextAdd = false;
        let addressReady = false;

        modal.dataset.gfPrecartBound = "true";

        const jsonrpc = function (url, params) {
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
            }).then(function (payload) {
                return payload.result || {};
            });
        };

        const setError = function (message) {
            if (!errorEl) {
                return;
            }

            errorEl.textContent = message || "";
            errorEl.hidden = !message;
        };

        const setLoading = function (loading) {
            if (actionsEl) {
                actionsEl.classList.toggle("gf-precart-modal__actions--loading", loading);
            }
            submitButtons.forEach(function (button) {
                button.disabled = loading;
            });
        };

        const openModal = function () {
            setError("");
            nextAction = "cart";
            modal.hidden = false;
            modal.setAttribute("aria-hidden", "false");
            document.documentElement.classList.add("gf-precart-modal-open");

            const firstInput = form.querySelector('input[name="name"]');
            if (firstInput) {
                window.setTimeout(function () {
                    firstInput.focus();
                }, 80);
            }
        };

        const closeModal = function (clearPending) {
            modal.hidden = true;
            modal.setAttribute("aria-hidden", "true");
            document.documentElement.classList.remove("gf-precart-modal-open");
            if (clearPending !== false) {
                pendingAction = null;
            }
        };

        const appendLocalityToStreet2 = function (values) {
            const villageSelect = form.querySelector(".gf-village-select");
            const villageReadonly = form.querySelector(".gf-village-readonly");
            const locality = (
                villageReadonly && !villageReadonly.hidden ? villageReadonly.value.trim() :
                villageSelect && !villageSelect.hidden ? villageSelect.value.trim() :
                ""
            );
            if (!locality) {
                return;
            }

            const street2 = (values.street2 || "").trim();
            if (street2.toLowerCase().includes(locality.toLowerCase())) {
                values.street2 = street2;
                return;
            }

            values.street2 = street2 ? street2 + ", " + locality : locality;
        };

        const replayPendingAction = function () {
            if (!pendingAction) {
                return;
            }

            const action = pendingAction;
            pendingAction = null;
            bypassNextAdd = true;

            const submitForm = function (form) {
                if (!form) {
                    return false;
                }

                if (form.requestSubmit) {
                    form.requestSubmit();
                } else {
                    form.submit();
                }
                return true;
            };

            if (action.type === "submit" && action.form) {
                submitForm(action.form);
                return;
            }

            if (action.target) {
                const targetForm = action.target.closest("form");
                const formAction = targetForm && targetForm.getAttribute("action");
                if (formAction && formAction.includes("/shop/cart/update")) {
                    action.target.click();
                    return;
                }

                action.target.click();
            }
        };

        const replayPendingActionWithSessionAddress = function () {
            replayPendingAction();
            window.setTimeout(function () {
                jsonrpc("/gadgetflix/precart/apply_session_address", {});
            }, 450);
        };

        const getPendingForm = function () {
            if (!pendingAction) {
                return null;
            }
            if (pendingAction.form) {
                return pendingAction.form;
            }
            return pendingAction.target ? pendingAction.target.closest("form") : null;
        };

        const addPendingProductToCart = function () {
            const productForm = getPendingForm();
            if (!productForm) {
                return Promise.reject(new Error("No product form found."));
            }

            const productTemplateInput = productForm.querySelector('[name="product_template_id"]');
            const productInput = productForm.querySelector('[name="product_id"]');
            const quantityInput = productForm.querySelector('[name="add_qty"], [name="quantity"]');
            const productTemplateId = parseInt(productTemplateInput && productTemplateInput.value, 10);
            const productId = parseInt(productInput && productInput.value, 10);
            const quantity = parseFloat((quantityInput && quantityInput.value) || "1") || 1;

            if (!productTemplateId || !productId) {
                return Promise.reject(new Error("Please select a valid product option."));
            }

            return jsonrpc("/shop/cart/add", {
                product_template_id: productTemplateId,
                product_id: productId,
                quantity: quantity,
            }).then(function (result) {
                if (!result || (!result.quantity && !result.cart_quantity)) {
                    throw new Error("Product could not be added to cart.");
                }
                return result;
            });
        };

        const updateCartCount = function (result) {
            if (!result || result.cart_quantity === undefined) {
                return;
            }

            window.sessionStorage.setItem("website_sale_cart_quantity", result.cart_quantity);
            document.querySelectorAll(".my_cart_quantity").forEach(function (element) {
                element.textContent = result.cart_quantity;
                element.classList.toggle("d-none", !result.cart_quantity);
            });
        };

        const addPendingProductAndStay = function () {
            return addPendingProductToCart().then(function (result) {
                updateCartCount(result);
                closeModal(false);
                pendingAction = null;
                return result;
            }).catch(function (error) {
                setError(error.message || "Could not add product to cart. Please try again.");
                throw error;
            });
        };

        const replayPendingActionAndCheckout = function () {
            return addPendingProductToCart().then(function () {
                window.location.href = "/shop/checkout";
            }).catch(function (error) {
                setError(error.message || "Could not add product to cart. Please try again.");
                throw error;
            });
        };

        const isAddToCartTarget = function (target) {
            return target && target.closest(
                "#add_to_cart, .o_we_buy_now, #products_grid .o_wsale_product_btn .a-submit, .s_add_to_cart_btn"
            );
        };

        const capturePendingClick = function (event) {
            const target = isAddToCartTarget(event.target);
            if (!target || modal.contains(target)) {
                return;
            }

            if (bypassNextAdd || addressReady) {
                bypassNextAdd = false;
                return;
            }

            event.preventDefault();
            event.stopImmediatePropagation();
            const actionToReplay = { type: "click", target: target };

            jsonrpc("/gadgetflix/precart/address_status", {}).then(function (result) {
                if (!result.needs_address) {
                    addressReady = true;
                    pendingAction = actionToReplay;
                    if (result.has_session_address) {
                        replayPendingActionWithSessionAddress();
                    } else {
                        replayPendingAction();
                    }
                    return;
                }

                pendingAction = actionToReplay;
                openModal();
            }).catch(function () {
                pendingAction = actionToReplay;
                openModal();
            });
        };

        const capturePendingSubmit = function (event) {
            const action = event.target && event.target.getAttribute("action");
            if (!action || !action.includes("/shop/cart/update")) {
                return;
            }

            if (bypassNextAdd || addressReady) {
                bypassNextAdd = false;
                return;
            }

            event.preventDefault();
            event.stopImmediatePropagation();
            const submitButton = event.target.querySelector("#add_to_cart");
            const actionToReplay = submitButton
                ? { type: "click", target: submitButton }
                : { type: "submit", form: event.target };

            jsonrpc("/gadgetflix/precart/address_status", {}).then(function (result) {
                if (!result.needs_address) {
                    addressReady = true;
                    pendingAction = actionToReplay;
                    if (result.has_session_address) {
                        replayPendingActionWithSessionAddress();
                    } else {
                        replayPendingAction();
                    }
                    return;
                }

                pendingAction = actionToReplay;
                openModal();
            }).catch(function () {
                pendingAction = actionToReplay;
                openModal();
            });
        };

        form.addEventListener("submit", function (event) {
            event.preventDefault();
            setError("");

            if (!form.reportValidity()) {
                return;
            }

            if (!validateAddressFormDetails(form, true)) {
                setError("Please complete your address details properly.");
                return;
            }

            const formData = new FormData(form);
            const values = {};
            formData.forEach(function (value, key) {
                values[key] = value;
            });
            appendLocalityToStreet2(values);

            setLoading(true);

            jsonrpc("/gadgetflix/precart/address_save", values).then(function (result) {
                if (!result.success) {
                    setError(result.error || "Please complete your address.");
                    return;
                }

                addressReady = true;
                if (nextAction === "checkout") {
                    return replayPendingActionAndCheckout();
                } else {
                    return addPendingProductAndStay();
                }
            }).catch(function () {
                if (!errorEl || !errorEl.textContent) {
                    setError("Could not save address. Please try again.");
                }
            }).finally(function () {
                setLoading(false);
            });
        });

        submitButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                nextAction = button.dataset.gfPrecartNext || "cart";
            });
        });

        modal.querySelectorAll("[data-gf-precart-close]").forEach(function (button) {
            button.addEventListener("click", closeModal);
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && !modal.hidden) {
                closeModal();
            }
        });

        document.addEventListener("click", capturePendingClick, true);
        document.addEventListener("submit", capturePendingSubmit, true);
    };

    const initHomeOfferPopup = function () {
        const popup = document.querySelector("[data-gf-home-offer-popup]");
        if (!popup || popup.dataset.gfHomeOfferBound === "true") {
            return;
        }

        popup.dataset.gfHomeOfferBound = "true";
        const storageKey = "gadgetflix_offer_popup_seen";
        const alwaysShow = popup.dataset.gfHomeOfferAlways === "true";

        try {
            if (!alwaysShow && window.localStorage.getItem(storageKey) === "1") {
                return;
            }
        } catch (error) {
            // Continue without persistence when storage is unavailable.
        }

        const markSeen = function () {
            if (alwaysShow) {
                return;
            }
            try {
                window.localStorage.setItem(storageKey, "1");
            } catch (error) {
                // Ignore storage errors; closing should still work.
            }
        };

        const closePopup = function () {
            markSeen();
            popup.hidden = true;
            popup.setAttribute("aria-hidden", "true");
            document.documentElement.classList.remove("gf-home-offer-popup-open");
        };

        const openPopup = function () {
            popup.hidden = false;
            popup.setAttribute("aria-hidden", "false");
            document.documentElement.classList.add("gf-home-offer-popup-open");
        };

        popup.querySelectorAll("[data-gf-home-offer-close]").forEach(function (button) {
            button.addEventListener("click", closePopup);
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && !popup.hidden) {
                closePopup();
            }
        });

        window.setTimeout(openPopup, 600);
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
        initIndianAddressLabels();
        initAddressStreetValidation();
        initInvoicePreferenceCleanup();
        initAddressLocalitySubmitSync();
        initPincodeAddressLookup();
        initAutoDeliveryFetcher();
        initPreCartAddressGate();
        initHomeOfferPopup();
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
    const cartBtn         = document.getElementById("add_to_cart");
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

    const initProductCarousel = function () {
        const carouselEl = document.querySelector("#gf-ayc-product-media #o-carousel-product");
        if (!carouselEl) return;

        carouselEl.querySelectorAll(".carousel-control-prev, .carousel-control-next").forEach(function (control) {
            control.setAttribute("href", "#o-carousel-product");
            control.setAttribute("data-bs-target", "#o-carousel-product");
        });
        carouselEl.querySelectorAll(".carousel-indicators [data-bs-slide-to]").forEach(function (indicator) {
            indicator.setAttribute("data-bs-target", "#o-carousel-product");
        });

        if (window.bootstrap && window.bootstrap.Carousel) {
            window.bootstrap.Carousel.getOrCreateInstance(carouselEl, {
                interval: false,
                ride: false,
                touch: true,
            });
        }
    };



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

            // Immediately show brand image (handled by backend rendering on load, but if they change brand, we'll wait for models to load)

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
                        if (m.carousel_html) {
                            li.dataset.carouselHtml = m.carousel_html;
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

        const productInput = document.getElementById("gf-ayc-product-id-input");
        if (productInput) productInput.value = state.activeVariantId || "";
        const productTemplateInput = document.getElementById("gf-ayc-product-template-id-input");
        if (productTemplateInput) productTemplateInput.value = state.activeProductId || "";

        updatePriceDisplay(state.activePrice);

        // update carousel
        if (item.dataset.carouselHtml) {
            const mediaContainer = document.getElementById("gf-ayc-product-media");
            const carouselContainer = mediaContainer ? mediaContainer.querySelector("#o-carousel-product") : document.getElementById("o-carousel-product");
            if (carouselContainer) {
                carouselContainer.outerHTML = item.dataset.carouselHtml;
            } else if (mediaContainer) {
                mediaContainer.innerHTML = item.dataset.carouselHtml;
            }
            initProductCarousel();
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
    if (stickyBtn) {
        stickyBtn.addEventListener("click", function () {
            if (cartBtn) cartBtn.click();
        });
    }

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

    // Initialize state from rendered HTML structure on page load
    if (brandList) {
        const activeBrandItem = brandList.querySelector(".gf-ayc-dropdown__item--active");
        if (activeBrandItem) {
            state.activeBrandProductId = parseInt(activeBrandItem.dataset.productId, 10);
            state.activeBrandValueId   = parseInt(activeBrandItem.dataset.brandValueId, 10);
            state.activeBrandName      = activeBrandItem.dataset.brandName || "";
        }
    }

    if (modelList) {
        const activeModelItem = modelList.querySelector(".gf-ayc-dropdown__item--active");
        if (activeModelItem) {
            state.activeVariantId    = parseInt(activeModelItem.dataset.variantId, 10);
            state.activeProductId    = parseInt(activeModelItem.dataset.productId, 10);
            state.activeModelValueId = parseInt(activeModelItem.dataset.modelValueId, 10);
            state.activePrice        = parseFloat(activeModelItem.dataset.price || 0);
            state.activeModelName    = activeModelItem.dataset.modelName || "";

            // Update title model suffix
            const titleModelSpan = document.getElementById("gf-ayc-title-model");
            if (titleModelSpan) {
                titleModelSpan.textContent = " - " + state.activeModelName;
            }

            if (stickyName) {
                stickyName.textContent = state.activeBrandName + " " + state.activeModelName + " – Anti-Yellow Case";
            }
            if (availEl) {
                availEl.innerHTML = state.activeVariantId
                    ? '<i class="fa fa-check-circle" aria-hidden="true"></i> In stock'
                    : '<i class="fa fa-times-circle" aria-hidden="true"></i> Unavailable';
            }
            setButtonsDisabled(!state.activeVariantId);
            updatePriceDisplay(state.activePrice);

            const productInput = document.getElementById("gf-ayc-product-id-input");
            if (productInput) productInput.value = state.activeVariantId || "";
            const productTemplateInput = document.getElementById("gf-ayc-product-template-id-input");
            if (productTemplateInput) productTemplateInput.value = state.activeProductId || "";
        }
    }
    initProductCarousel();

    // ── Reviews "Read More" logic ──────────────────────────────────────────
    const initReadMore = function () {
        const reviewTexts = document.querySelectorAll(".gf-review-card .r-text");
        reviewTexts.forEach(function (textEl) {
            const container = textEl.parentElement;
            const btn = container.querySelector(".r-read-more");
            if (!btn) return;

            // Temporarily remove clamped to get full height
            const wasClamped = textEl.classList.contains("clamped");
            textEl.classList.remove("clamped");
            const fullHeight = textEl.offsetHeight;

            // Re-apply clamped to get clamped height
            if (wasClamped) {
                textEl.classList.add("clamped");
            }
            const clampedHeight = textEl.offsetHeight;

            if (fullHeight > clampedHeight) {
                btn.style.display = "inline-block";
                if (!btn.dataset.hasListener) {
                    btn.dataset.hasListener = "true";
                    btn.addEventListener("click", function () {
                        const isClamped = textEl.classList.contains("clamped");
                        if (isClamped) {
                            textEl.classList.remove("clamped");
                            btn.textContent = "Read less";
                        } else {
                            textEl.classList.add("clamped");
                            btn.textContent = "Read more";
                        }
                    });
                }
            } else {
                btn.style.display = "none";
            }
        });
    };

    initReadMore();
    window.addEventListener("load", initReadMore);
    setTimeout(initReadMore, 500);
    setTimeout(initReadMore, 1500);
})();
