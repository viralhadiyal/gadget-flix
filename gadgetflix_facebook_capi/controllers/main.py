import threading
import requests
import time
import hashlib
import logging
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.cart import Cart
from odoo.addons.website_sale.controllers.payment import PaymentPortal

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Async CAPI sender (runs in background thread, never blocks the request)
# ---------------------------------------------------------------------------

def _send_capi_async(website, event_name, custom_data, user_data, event_id=None, request_url=None):
    api_version = website.facebook_capi_api_version or 'v19.0'
    url = f"https://graph.facebook.com/{api_version}/{website.facebook_pixel_id}/events"
    headers = {'Content-Type': 'application/json'}
    params = {'access_token': website.facebook_capi_token}

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
    if website.facebook_capi_test_code:
        payload['test_event_code'] = website.facebook_capi_test_code

    try:
        requests.post(url, headers=headers, params=params, json=payload, timeout=3)
    except Exception as e:
        _logger.warning("Facebook CAPI Async Error: %s", e)


# ---------------------------------------------------------------------------
# Helper: build user_data and fire CAPI in a background thread
# ---------------------------------------------------------------------------

def trigger_backend_capi(event_name, custom_data=None, event_id=None):
    """Send a server-side CAPI event. event_id must match the dataLayer push."""
    website = request.env['website'].get_current_website()
    if not website or not website.facebook_pixel_id or not website.facebook_capi_token:
        return

    client_ip_address = request.httprequest.remote_addr or ''
    client_user_agent = request.httprequest.user_agent.string if request.httprequest.user_agent else ''
    fbp = request.httprequest.cookies.get('_fbp', '')
    fbc = request.httprequest.cookies.get('_fbc', '')

    user_data = {
        'client_ip_address': client_ip_address,
        'client_user_agent': client_user_agent,
    }

    if not request.env.user._is_public():
        partner = request.env.user.partner_id
        if partner.email:
            user_data['em'] = [hashlib.sha256(str(partner.email).strip().lower().encode('utf-8')).hexdigest()]
        if partner.phone:
            phone = ''.join(filter(str.isdigit, partner.phone))
            if phone:
                user_data['ph'] = [hashlib.sha256(phone.encode('utf-8')).hexdigest()]

    if fbp:
        user_data['fbp'] = fbp
    if fbc:
        user_data['fbc'] = fbc

    current_url = request.httprequest.url

    threading.Thread(
        target=_send_capi_async,
        args=(website, event_name, custom_data or {}, user_data, event_id, current_url)
    ).start()


# ---------------------------------------------------------------------------
# Helper: generate event_id and store on request for QWeb access
# ---------------------------------------------------------------------------

def _generate_event_id(prefix, entity_id=None):
    """Generate an event_id, store it on request, and return it.

    For entity-based events (cart, checkout, purchase), the ID is fully
    deterministic: ``cart_42``, ``checkout_42``, ``order_42``.

    For time-based events (ViewContent), a millisecond timestamp is appended
    to guarantee uniqueness across page loads.
    """
    if entity_id is not None:
        eid = f'{prefix}_{entity_id}'
    else:
        eid = f'{prefix}_{int(time.time() * 1000)}'
    return eid


# ===================================================================
# Controller overrides — each generates ONE event_id used by both
# the QWeb dataLayer.push() AND the CAPI Graph API payload.
# ===================================================================

class GadgetflixCapiCart(Cart):

    # ---------- Real-time AddToCart (AJAX) ----------
    @http.route(['/shop/cart/add'], type='jsonrpc', auth='public', methods=['POST'], website=True, sitemap=False)
    def add_to_cart(self, product_template_id, product_id, quantity=1.0, uom_id=None,
                    product_custom_attribute_values=None, no_variant_attribute_value_ids=None,
                    linked_products=None, **kwargs):
        res = super().add_to_cart(
            product_template_id, product_id, quantity=quantity, uom_id=uom_id,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_value_ids=no_variant_attribute_value_ids,
            linked_products=linked_products, **kwargs
        )
        try:
            quantity = float(quantity)
            if product_id and quantity > 0:
                product = request.env['product.product'].sudo().browse(int(product_id))
                order = request.cart
                eid = _generate_event_id('cart', order.id if order else None)
                if product.exists():
                    trigger_backend_capi('AddToCart', {
                        'content_type': 'product',
                        'content_ids': [str(product.id)],
                        'value': float(product.list_price * quantity),
                        'currency': request.website.currency_id.name
                    }, event_id=eid)
        except Exception as e:
            _logger.warning("CAPI add_to_cart failed: %s", e)
        return res

    @http.route(['/shop/cart/update'], type='jsonrpc', auth='public', methods=['POST'], website=True, sitemap=False)
    def update_cart(self, line_id, quantity, product_id=None, **kwargs):
        res = super().update_cart(line_id, quantity, product_id=product_id, **kwargs)
        try:
            quantity = float(quantity)
            if line_id:
                line = request.env['sale.order.line'].sudo().browse(int(line_id))
                order = request.cart
                eid = _generate_event_id('cart', order.id if order else None)
                if line.exists() and line.product_id:
                    trigger_backend_capi('AddToCart', {
                        'content_type': 'product',
                        'content_ids': [str(line.product_id.id)],
                        'value': float(line.product_id.list_price * quantity),
                        'currency': request.website.currency_id.name
                    }, event_id=eid)
        except Exception as e:
            _logger.warning("CAPI update_cart failed: %s", e)
        return res

    # ---------- Cart page view (/shop/cart) ----------
    @http.route(['/shop/cart'], type='http', auth='public', website=True, sitemap=False)
    def cart(self, **post):
        # Generate event_id BEFORE super() so QWeb template can read it
        order = request.cart
        if order and order.id:
            request.fb_atc_event_id = _generate_event_id('cart', order.id)
        res = super().cart(**post)
        return res


class GadgetflixCapiWebsiteSale(WebsiteSale):

    # ---------- ViewContent (product detail page) ----------
    @http.route(['/shop/<model("product.template"):product>'], type='http', auth='public', website=True, sitemap=True)
    def shop_product(self, product, category='', search='', **kwargs):
        # Generate event_id BEFORE super() so QWeb template can read it
        eid = _generate_event_id('vc', f'{product.id}_{int(time.time() * 1000)}')
        request.fb_vc_event_id = eid

        res = super().shop_product(product, category=category, search=search, **kwargs)

        # Fire CAPI with the SAME event_id
        try:
            trigger_backend_capi('ViewContent', {
                'content_type': 'product',
                'content_ids': [str(product.id)],
                'content_name': product.name,
                'value': float(product.list_price),
                'currency': request.website.currency_id.name
            }, event_id=eid)
        except Exception as e:
            _logger.warning("CAPI ViewContent failed: %s", e)
        return res

    # ---------- InitiateCheckout (/shop/checkout) ----------
    @http.route(['/shop/checkout'], type='http', auth="public", website=True, sitemap=False)
    def shop_checkout(self, try_skip_step=None, **query_params):
        # Generate event_id BEFORE super() so QWeb template can read it
        order = request.cart
        if order and order.id:
            request.fb_checkout_event_id = _generate_event_id('checkout', order.id)

        res = super().shop_checkout(try_skip_step=try_skip_step, **query_params)

        # Fire CAPI with the SAME event_id
        try:
            if order and order.amount_total > 0:
                trigger_backend_capi('InitiateCheckout', {
                    'value': float(order.amount_total),
                    'currency': order.currency_id.name,
                    'num_items': order.cart_quantity
                }, event_id=_generate_event_id('checkout', order.id))
        except Exception as e:
            _logger.warning("CAPI InitiateCheckout failed: %s", e)
        return res

    # ---------- Address submit (AddPaymentInfo) ----------
    @http.route(['/shop/address/submit'], type='http', methods=['POST'], auth='public', website=True, sitemap=False)
    def shop_address_submit(self, partner_id=None, address_type='billing',
                            use_delivery_as_billing=None, callback=None, **form_data):
        res = super().shop_address_submit(
            partner_id=partner_id, address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing,
            callback=callback, **form_data
        )
        try:
            order = request.cart
            if order and order.amount_total > 0:
                trigger_backend_capi('AddPaymentInfo', {
                    'value': float(order.amount_total),
                    'currency': order.currency_id.name
                }, event_id=_generate_event_id('payment', order.id))
        except Exception as e:
            _logger.warning("CAPI shop_address_submit failed: %s", e)
        return res


class GadgetflixCapiPaymentPortal(PaymentPortal):
    @http.route('/shop/payment/transaction/<int:order_id>', type='jsonrpc', auth='public', website=True)
    def shop_payment_transaction(self, order_id, access_token, **kwargs):
        res = super().shop_payment_transaction(order_id, access_token, **kwargs)
        try:
            order = request.env['sale.order'].sudo().browse(order_id)
            if order.exists() and order.amount_total > 0:
                trigger_backend_capi('Lead', {
                    'value': float(order.amount_total),
                    'currency': order.currency_id.name
                }, event_id=_generate_event_id('lead', order.id))
        except Exception as e:
            _logger.warning("CAPI shop_payment_transaction failed: %s", e)
        return res
