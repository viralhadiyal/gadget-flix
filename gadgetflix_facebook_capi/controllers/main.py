import threading
import requests
import time
import hashlib
import logging
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.cart import Cart

_logger = logging.getLogger(__name__)

def _send_capi_async(website, event_name, custom_data, user_data, request_url=None):
    """Fire and forget CAPI event to prevent blocking the request."""
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
    if request_url:
        event_data['event_source_url'] = request_url

    payload = {'data': [event_data]}
    
    if website.facebook_capi_test_code:
        payload['test_event_code'] = website.facebook_capi_test_code

    try:
        requests.post(url, headers=headers, params=params, json=payload, timeout=3)
    except Exception as e:
        _logger.warning("Facebook CAPI Async Error: %s", e)

def trigger_backend_capi(event_name, custom_data=None):
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

    if fbp: user_data['fbp'] = fbp
    if fbc: user_data['fbc'] = fbc

    current_url = request.httprequest.url

    threading.Thread(
        target=_send_capi_async, 
        args=(website, event_name, custom_data or {}, user_data, current_url)
    ).start()

class GadgetflixCapiCart(Cart):
    @http.route(['/shop/cart/add'], type='jsonrpc', auth='public', methods=['POST'], website=True, sitemap=False)
    def add_to_cart(self, product_template_id, product_id, quantity=1.0, uom_id=None, product_custom_attribute_values=None, no_variant_attribute_value_ids=None, linked_products=None, **kwargs):
        res = super().add_to_cart(product_template_id, product_id, quantity=quantity, uom_id=uom_id, product_custom_attribute_values=product_custom_attribute_values, no_variant_attribute_value_ids=no_variant_attribute_value_ids, linked_products=linked_products, **kwargs)
        try:
            quantity = float(quantity)
            if product_id and quantity > 0:
                product = request.env['product.product'].sudo().browse(int(product_id))
                if product.exists():
                    trigger_backend_capi('AddToCart', {
                        'content_type': 'product',
                        'content_ids': [str(product.id)],
                        'value': float(product.list_price * quantity),
                        'currency': request.website.currency_id.name
                    })
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
                if line.exists() and line.product_id:
                    trigger_backend_capi('AddToCart', {
                        'content_type': 'product',
                        'content_ids': [str(line.product_id.id)],
                        'value': float(line.product_id.list_price * quantity),
                        'currency': request.website.currency_id.name
                    })
        except Exception as e:
            _logger.warning("CAPI update_cart failed: %s", e)
        return res

class GadgetflixCapiWebsiteSale(WebsiteSale):
    @http.route(['/shop/checkout'], type='http', auth="public", website=True, sitemap=False)
    def shop_checkout(self, try_skip_step=None, **query_params):
        res = super().shop_checkout(try_skip_step=try_skip_step, **query_params)
        try:
            order = request.cart
            if order and order.amount_total > 0:
                trigger_backend_capi('InitiateCheckout', {
                    'value': float(order.amount_total),
                    'currency': order.currency_id.name,
                    'num_items': order.cart_quantity
                })
        except Exception as e:
            _logger.warning("CAPI InitiateCheckout failed: %s", e)
        return res

    @http.route(['/shop/payment'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment(self, **post):
        res = super().shop_payment(**post)
        try:
            order = request.cart
            if order and order.amount_total > 0:
                # AddShippingInfo and AddPaymentInfo are usually triggered around payment step
                custom_data = {
                    'value': float(order.amount_total),
                    'currency': order.currency_id.name
                }
                trigger_backend_capi('AddShippingInfo', custom_data)
                trigger_backend_capi('AddPaymentInfo', custom_data)
        except Exception as e:
            _logger.warning("CAPI AddPaymentInfo failed: %s", e)
        return res

