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
    @http.route()
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        res = super().cart_update(product_id, add_qty, set_qty, **kw)
        try:
            if add_qty > 0:
                product = request.env['product.product'].sudo().browse(int(product_id))
                if product.exists():
                    trigger_backend_capi('AddToCart', {
                        'content_type': 'product',
                        'content_ids': [str(product.id)],
                        'value': float(product.list_price * add_qty),
                        'currency': request.website.currency_id.name
                    })
        except Exception as e:
            _logger.warning("CAPI AddToCart failed: %s", e)
        return res

class GadgetflixCapiWebsiteSale(WebsiteSale):
    @http.route()
    def checkout(self, **post):
        res = super().checkout(**post)
        try:
            order = request.website.sale_get_order()
            if order and order.amount_total > 0:
                trigger_backend_capi('InitiateCheckout', {
                    'value': float(order.amount_total),
                    'currency': order.currency_id.name,
                    'num_items': order.cart_quantity
                })
        except Exception as e:
            _logger.warning("CAPI InitiateCheckout failed: %s", e)
        return res

    @http.route()
    def payment(self, **post):
        res = super().payment(**post)
        try:
            order = request.website.sale_get_order()
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

