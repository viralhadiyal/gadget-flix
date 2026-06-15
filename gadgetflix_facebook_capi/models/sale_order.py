import hashlib
import time
import requests
import logging
from odoo import models, api
from odoo.http import request

_logger = logging.getLogger(__name__)

def _send_capi_post_async(url, headers, params, payload):
    try:
        requests.post(url, headers=headers, params=params, json=payload, timeout=3)
    except Exception as e:
        _logger.warning("Facebook CAPI Purchase Async Error: %s", e)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        for order in self:
            # Only track if it's a website order and has credentials configured
            if order.website_id and order.website_id.facebook_pixel_id and order.website_id.facebook_capi_token:
                try:
                    order._send_facebook_capi_purchase()
                except Exception as e:
                    _logger.warning("Failed to send Facebook CAPI Event: %s", e)
        return res

    def _hash_data(self, data):
        if not data:
            return ''
        return hashlib.sha256(str(data).strip().lower().encode('utf-8')).hexdigest()

    def _send_facebook_capi_purchase(self):
        website = self.website_id
        
        client_ip_address = ''
        client_user_agent = ''
        fbp = ''
        fbc = ''
        
        if request and request.httprequest:
            client_ip_address = request.httprequest.remote_addr or ''
            client_user_agent = request.httprequest.user_agent.string if request.httprequest.user_agent else ''
            fbp = request.httprequest.cookies.get('_fbp', '')
            fbc = request.httprequest.cookies.get('_fbc', '')

        user_data = {
            'client_ip_address': client_ip_address,
            'client_user_agent': client_user_agent,
        }
        
        if self.partner_id.email:
            user_data['em'] = [self._hash_data(self.partner_id.email)]
            
        if self.partner_id.phone:
            # Meta requires phone numbers to include country code and only digits
            phone = ''.join(filter(str.isdigit, self.partner_id.phone))
            if phone:
                user_data['ph'] = [self._hash_data(phone)]
            
        if fbp:
            user_data['fbp'] = fbp
        if fbc:
            user_data['fbc'] = fbc

        content_ids = [str(line.product_id.id) for line in self.order_line if line.product_id]
        custom_data = {
            'value': float(self.amount_total),
            'currency': self.currency_id.name,
            'content_type': 'product',
            'content_ids': content_ids,
        }

        # Build payload
        payload = {
            'data': [{
                'event_name': 'Purchase',
                'event_time': int(time.time()),
                'action_source': 'website',
                'event_id': f"PURCHASE_{self.id}",
                'user_data': user_data,
                'custom_data': custom_data,
            }]
        }
        
        if website.facebook_capi_test_code:
            payload['test_event_code'] = website.facebook_capi_test_code

        api_version = website.facebook_capi_api_version or 'v19.0'
        url = f"https://graph.facebook.com/{api_version}/{website.facebook_pixel_id}/events"
        headers = {'Content-Type': 'application/json'}
        params = {'access_token': website.facebook_capi_token}
        
        # Fire and forget asynchronously in a background thread to prevent blocking checkout page
        import threading
        threading.Thread(
            target=_send_capi_post_async, 
            args=(url, headers, params, payload)
        ).start()
