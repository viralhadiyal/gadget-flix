import threading
import requests
import time
import hashlib
import logging
from odoo import http
from odoo.http import request
from odoo.addons.gadgetflix_website.controllers.main import WebsiteSaleShop, AntiYellowController
from odoo.addons.website_sale.controllers.cart import Cart
from odoo.addons.website_sale.controllers.payment import PaymentPortal

_logger = logging.getLogger(__name__)


def _send_capi_async(pixel_id, capi_token, api_version, test_code,
                     event_name, custom_data, user_data,
                     request_url=None, event_id=None):
    """Fire-and-forget CAPI event in a daemon background thread.

    All arguments are plain Python primitives — NO Odoo ORM objects are passed
    here.  The thread does not hold any database cursor, so it is safe to run
    after the originating HTTP request has already returned and its cursor has
    been closed.
    """
    url = f"https://graph.facebook.com/{api_version}/{pixel_id}/events"
    headers = {'Content-Type': 'application/json'}
    params = {'access_token': capi_token}

    event_data = {
        'event_name': event_name,
        'event_time': int(time.time()),
        'action_source': 'website',
        'user_data': user_data,
        'custom_data': custom_data,
    }
    if event_id:
        event_data['event_id'] = event_id
    if request_url:
        event_data['event_source_url'] = request_url

    payload = {'data': [event_data]}
    if test_code:
        payload['test_event_code'] = test_code

    try:
        requests.post(url, headers=headers, params=params, json=payload, timeout=3)
    except Exception as e:
        _logger.warning("Facebook CAPI Error [%s]: %s", event_name, e)


def trigger_backend_capi(event_name, custom_data=None, event_id=None):
    """Collect user data from the current request and fire a CAPI event.

    All Odoo ORM values are extracted into plain strings *before* the thread
    is spawned, so the thread holds no live cursor or environment reference.
    """
    website = request.env['website'].get_current_website()
    if not website or not website.facebook_pixel_id or not website.facebook_capi_token:
        return

    # ── Extract all ORM field values now, before entering the thread ──────
    pixel_id = website.facebook_pixel_id or ''
    capi_token = website.facebook_capi_token or ''
    api_version = website.facebook_capi_api_version or 'v21.0'
    test_code = website.facebook_capi_test_code or ''

    # ── Extract request data now, while the request context is still live ─
    client_ip_address = request.httprequest.remote_addr or ''
    client_user_agent = (
        request.httprequest.user_agent.string
        if request.httprequest.user_agent else ''
    )
    fbp = request.httprequest.cookies.get('_fbp', '')
    fbc = request.httprequest.cookies.get('_fbc', '')

    user_data = {
        'client_ip_address': client_ip_address,
        'client_user_agent': client_user_agent,
    }

    if not request.env.user._is_public():
        partner = request.env.user.partner_id
        if partner.email:
            user_data['em'] = [
                hashlib.sha256(
                    str(partner.email).strip().lower().encode('utf-8')
                ).hexdigest()
            ]
        if partner.phone:
            phone = ''.join(filter(str.isdigit, partner.phone))
            if phone:
                user_data['ph'] = [
                    hashlib.sha256(phone.encode('utf-8')).hexdigest()
                ]

    if fbp:
        user_data['fbp'] = fbp
    if fbc:
        user_data['fbc'] = fbc

    current_url = request.httprequest.url

    # ── Spawn a daemon thread so it never blocks Odoo worker shutdown ──────
    t = threading.Thread(
        target=_send_capi_async,
        args=(
            pixel_id, capi_token, api_version, test_code,
            event_name, custom_data or {}, user_data, current_url, event_id,
        ),
        daemon=True,
    )
    t.start()


# ═══════════════════════════════════════════════════════════════════════
# Product/Cart/Checkout Override — inherits from gadgetflix_website's
# WebsiteSaleShop (which already inherits from Odoo's WebsiteSale/Delivery)
# so the full MRO is preserved and our combined checkout is not bypassed.
# ═══════════════════════════════════════════════════════════════════════
class GadgetflixCapiWebsiteSale(WebsiteSaleShop):

    # ── ViewContent — Product Page ────────────────────────────────────
    @http.route()
    def product(self, product, category=None, pricelist=None, **kwargs):
        res = super().product(product, category=category, pricelist=pricelist, **kwargs)
        try:
            if product and product.exists():
                event_id = f"VIEW_{product.id}_{int(time.time() * 1000)}"
                # Cookie lets the browser JS use the same event_id → deduplication
                request.set_cookie('gf_fb_view_content_eid', event_id, httponly=False)
                trigger_backend_capi('ViewContent', {
                    'content_name': product.name,
                    'content_ids': [str(product.id)],
                    'content_type': 'product',
                    'value': float(product.list_price),
                    'currency': request.website.currency_id.name,
                }, event_id=event_id)
        except Exception as e:
            _logger.warning("CAPI ViewContent failed: %s", e)
        return res

    # ── AddToCart — HTTP POST (classic form submit) ───────────────────
    @http.route(['/shop/cart/update'], type='http', auth="public",
                methods=['POST'], website=True, sitemap=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        res = super().cart_update(product_id, add_qty=add_qty, set_qty=set_qty, **kw)
        try:
            qty = float(add_qty or 0)
            if qty > 0 and product_id:
                product = request.env['product.product'].sudo().browse(int(product_id))
                if product.exists():
                    event_id = f"ATC_{product.id}_{int(time.time() * 1000)}"
                    request.set_cookie('gf_fb_atc_eid', event_id, httponly=False)
                    trigger_backend_capi('AddToCart', {
                        'content_type': 'product',
                        'content_ids': [str(product.id)],
                        'value': float(product.list_price * qty),
                        'currency': request.website.currency_id.name,
                    }, event_id=event_id)
        except Exception as e:
            _logger.warning("CAPI cart_update AddToCart failed: %s", e)
        return res

    # ── AddToCart — JSON AJAX update ──────────────────────────────────
    @http.route(['/shop/cart/update_json'], type='json', auth="public",
                methods=['POST'], website=True, sitemap=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None,
                         set_qty=None, display=True, **kw):
        res = super().cart_update_json(
            product_id, line_id=line_id, add_qty=add_qty,
            set_qty=set_qty, display=display, **kw,
        )
        try:
            qty = float(add_qty or 0)
            if qty > 0 and product_id:
                product = request.env['product.product'].sudo().browse(int(product_id))
                if product.exists():
                    event_id = f"ATC_{product.id}_{int(time.time() * 1000)}"
                    request.set_cookie('gf_fb_atc_eid', event_id, httponly=False)
                    trigger_backend_capi('AddToCart', {
                        'content_type': 'product',
                        'content_ids': [str(product.id)],
                        'value': float(product.list_price * qty),
                        'currency': request.website.currency_id.name,
                    }, event_id=event_id)
        except Exception as e:
            _logger.warning("CAPI cart_update_json AddToCart failed: %s", e)
        return res

    # ── InitiateCheckout + AddPaymentInfo — Combined checkout page ───────
    # InitiateCheckout : user lands on the checkout page (address already set)
    # AddPaymentInfo   : user sees the address form on checkout (same page load)
    #
    # NOTE: Odoo redirects users with no saved address to /shop/address.
    # We skip all events when a redirect is returned — events fire on the
    # next visit to /shop/checkout after address has been saved.
    @http.route(['/shop/checkout'], type='http', auth="public",
                website=True, sitemap=False)
    def shop_checkout(self, try_skip_step=None, **query_params):
        res = super().shop_checkout(try_skip_step=try_skip_step, **query_params)
        try:
            # Skip events if Odoo redirected user away (e.g. to address form)
            if hasattr(res, 'status_code') and res.status_code in (301, 302, 303, 307, 308):
                return res

            order = request.cart
            if order and order.exists() and order.amount_total > 0:
                val = float(order.amount_total)
                cur = order.currency_id.name

                trigger_backend_capi('InitiateCheckout', {
                    'value': val,
                    'currency': cur,
                    'num_items': order.cart_quantity,
                }, event_id=f"CHECKOUT_{order.id}")

                # AddPaymentInfo: fires when user actually lands on the checkout
                # page and sees the address + payment form (not on redirect).
                trigger_backend_capi('AddPaymentInfo', {
                    'value': val,
                    'currency': cur,
                }, event_id=f"PAYMENT_{order.id}")
        except Exception as e:
            _logger.warning("CAPI InitiateCheckout/AddPaymentInfo failed: %s", e)
        return res



# ═══════════════════════════════════════════════════════════════════════
# Add to Cart — express / quick-add (jsonrpc endpoint)
# ═══════════════════════════════════════════════════════════════════════
class GadgetflixCapiCart(Cart):

    @http.route(['/shop/cart/add'], type='jsonrpc', auth='public',
                methods=['POST'], website=True, sitemap=False)
    def add_to_cart(self, product_template_id, product_id, quantity=1.0,
                    uom_id=None, product_custom_attribute_values=None,
                    no_variant_attribute_value_ids=None, linked_products=None,
                    **kwargs):
        res = super().add_to_cart(
            product_template_id, product_id, quantity=quantity, uom_id=uom_id,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_value_ids=no_variant_attribute_value_ids,
            linked_products=linked_products, **kwargs,
        )
        try:
            qty = float(quantity)
            if product_id and qty > 0:
                product = request.env['product.product'].sudo().browse(int(product_id))
                if product.exists():
                    event_id = f"ATC_{product.id}_{int(time.time() * 1000)}"
                    request.set_cookie('gf_fb_atc_eid', event_id, httponly=False)
                    trigger_backend_capi('AddToCart', {
                        'content_type': 'product',
                        'content_ids': [str(product.id)],
                        'value': float(product.list_price * qty),
                        'currency': request.website.currency_id.name,
                    }, event_id=event_id)
        except Exception as e:
            _logger.warning("CAPI AddToCart (add_to_cart) failed: %s", e)
        return res


# ═══════════════════════════════════════════════════════════════════════
# Payment Transaction — AddShippingInfo + Lead
#
# Event mapping:
#   AddShippingInfo → user clicks Pay Now (address submitted at this moment)
#   Lead            → user clicks Pay Now (payment initiated)
#
# Note: AddPaymentInfo is NOT here — it fires earlier at checkout page load.
# ═══════════════════════════════════════════════════════════════════════
class GadgetflixCapiPaymentPortal(PaymentPortal):

    @http.route('/shop/payment/transaction/<int:order_id>', type='jsonrpc',
                auth='public', website=True)
    def shop_payment_transaction(self, order_id, access_token, **kwargs):
        res = super().shop_payment_transaction(order_id, access_token, **kwargs)
        try:
            order = request.env['sale.order'].sudo().browse(order_id)
            if order.exists() and order.amount_total > 0:
                val = float(order.amount_total)
                cur = order.currency_id.name

                # AddShippingInfo: address is submitted at the same moment
                # the user clicks Pay Now in the combined checkout.
                trigger_backend_capi('AddShippingInfo', {
                    'value': val,
                    'currency': cur,
                }, event_id=f"SHIPPING_{order.id}")

                # Lead: user has selected a payment method and initiated payment
                trigger_backend_capi('Lead', {
                    'value': val,
                    'currency': cur,
                }, event_id=f"LEAD_{order.id}")
                # NOTE: No cookie needed for Lead — browser uses stable
                # 'LEAD_{orderId}' format matching server's 'LEAD_{order.id}'.
        except Exception as e:
            _logger.warning("CAPI Payment/Lead failed: %s", e)
        return res


# ═══════════════════════════════════════════════════════════════════════
# Anti-Yellow Landing Page — ViewContent (server-side)
# ═══════════════════════════════════════════════════════════════════════
class GadgetflixCapiAntiYellowController(AntiYellowController):

    @http.route('/', type='http', auth='public', website=True, sitemap=True)
    def anti_yellow_case_page(self, **kw):
        res = super().anti_yellow_case_page(**kw)
        try:
            # Response.qcontext is not a reliable attribute in Odoo 17+.
            # Re-query the first anti-yellow product directly instead.
            website = request.env['website'].get_current_website()
            ay_category = request.env['product.public.category'].sudo().search([
                ('name', 'ilike', 'Anti-Yellow Cases')
            ], limit=1)
            domain = [('website_published', '=', True)]
            if ay_category:
                domain.append(('public_categ_ids', 'in', ay_category.ids))
            product = request.env['product.template'].sudo().search(
                domain + website.website_domain(),
                order='website_sequence asc, id asc',
                limit=1,
            )
            if product and product.exists():
                variant = product.product_variant_ids[:1]
                event_id = f"VIEW_{product.id}_{int(time.time() * 1000)}"
                request.set_cookie('gf_fb_view_content_eid', event_id, httponly=False)
                trigger_backend_capi('ViewContent', {
                    'content_name': product.name,
                    'content_ids': [str(variant.id if variant else product.id)],
                    'content_type': 'product',
                    'value': float(variant.lst_price if variant else product.list_price),
                    'currency': request.website.currency_id.name,
                }, event_id=event_id)
        except Exception as e:
            _logger.warning("CAPI Anti-Yellow ViewContent failed: %s", e)
        return res
