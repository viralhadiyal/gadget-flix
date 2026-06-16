import threading
import hashlib
import time
import requests
import logging
from odoo import models
from odoo.http import request

_logger = logging.getLogger(__name__)


def _send_capi_post_async(url, headers, params, payload):
    """Fire-and-forget HTTP POST in a daemon thread.

    All arguments are plain Python primitives — no Odoo ORM references.
    This function holds no database cursor and is safe to run after the
    originating transaction has already been committed and closed.
    """
    try:
        requests.post(url, headers=headers, params=params, json=payload, timeout=3)
    except Exception as e:
        _logger.warning("Facebook CAPI Purchase Async Error: %s", e)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        for order in self:
            # Only fire for website orders that have CAPI credentials configured
            if (order.website_id
                    and order.website_id.facebook_pixel_id
                    and order.website_id.facebook_capi_token):
                try:
                    order._send_facebook_capi_purchase()
                except Exception as e:
                    _logger.warning("Failed to send Facebook CAPI Purchase event: %s", e)
        return res

    def _hash_data(self, data):
        if not data:
            return ''
        return hashlib.sha256(
            str(data).strip().lower().encode('utf-8')
        ).hexdigest()

    def _send_facebook_capi_purchase(self):
        website = self.website_id

        # ── Safely attempt to read HTTP request data ──────────────────────
        # _action_confirm() may be called from backend UI, cron jobs, or
        # automated actions — there is no guaranteed HTTP request context.
        # The `request` proxy raises RuntimeError when accessed outside an
        # HTTP thread, so we guard with try/except.
        client_ip_address = ''
        client_user_agent = ''
        fbp = ''
        fbc = ''
        try:
            if request.httprequest:
                client_ip_address = request.httprequest.remote_addr or ''
                client_user_agent = (
                    request.httprequest.user_agent.string
                    if request.httprequest.user_agent else ''
                )
                fbp = request.httprequest.cookies.get('_fbp', '')
                fbc = request.httprequest.cookies.get('_fbc', '')
        except RuntimeError:
            # No active HTTP request — called from backend / cron context
            pass

        user_data = {
            'client_ip_address': client_ip_address,
            'client_user_agent': client_user_agent,
        }

        if self.partner_id.email:
            user_data['em'] = [self._hash_data(self.partner_id.email)]

        if self.partner_id.phone:
            # Meta requires phone numbers to be digits-only, with country code
            phone = ''.join(filter(str.isdigit, self.partner_id.phone))
            if phone:
                user_data['ph'] = [self._hash_data(phone)]

        if fbp:
            user_data['fbp'] = fbp
        if fbc:
            user_data['fbc'] = fbc

        content_ids = [
            str(line.product_id.id)
            for line in self.order_line
            if line.product_id
        ]
        custom_data = {
            'value': float(self.amount_total),
            'currency': self.currency_id.name,
            'content_type': 'product',
            'content_ids': content_ids,
        }

        # ── Extract all ORM values before spawning the thread ─────────────
        # The thread must not hold any Odoo ORM reference or DB cursor.
        api_version = website.facebook_capi_api_version or 'v21.0'
        pixel_id = website.facebook_pixel_id
        capi_token = website.facebook_capi_token
        test_code = website.facebook_capi_test_code or ''

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
        if test_code:
            payload['test_event_code'] = test_code

        url = f"https://graph.facebook.com/{api_version}/{pixel_id}/events"
        headers = {'Content-Type': 'application/json'}
        params = {'access_token': capi_token}

        # Daemon thread — will not block Odoo worker shutdown / restart
        t = threading.Thread(
            target=_send_capi_post_async,
            args=(url, headers, params, payload),
            daemon=True,
        )
        t.start()
