import time
import logging
import odoo.http
from odoo import models
from odoo.http import request

_logger = logging.getLogger(__name__)

# Ensure default attributes exist on Request class to prevent QWeb rendering errors
# on requests that bypass _pre_dispatch (e.g. error/fallback pages)
odoo.http.Request.fb_pv_event_id = ''
odoo.http.Request.fb_vc_event_id = ''
odoo.http.Request.fb_atc_event_id = ''
odoo.http.Request.fb_checkout_event_id = ''



class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _pre_dispatch(cls, rule, arguments):
        res = super()._pre_dispatch(rule, arguments)
        if request:
            request.fb_pv_event_id = f'pv_{int(time.time() * 1000)}'
            request.fb_vc_event_id = ''
            request.fb_atc_event_id = ''
            request.fb_checkout_event_id = ''
        return res

    @classmethod
    def _post_dispatch(cls, response):
        res = super()._post_dispatch(response)

        try:
            if not hasattr(request, 'website') or not request.website:
                return res

            website = request.website
            if not website.facebook_pixel_id or not website.facebook_capi_token:
                return res

            path = request.httprequest.path
            method = request.httprequest.method

            # Fire PageView CAPI for all successful HTML GET requests on public pages
            if method == 'GET' and hasattr(response, 'status_code') and response.status_code == 200:
                mimetype = getattr(response, 'mimetype', '') or ''
                if 'text/html' in mimetype and not path.startswith(('/web', '/odoo', '/logo', '/mail')):
                    from odoo.addons.gadgetflix_facebook_capi.controllers.main import trigger_backend_capi
                    # Use the SAME event_id that was set in _pre_dispatch
                    # and rendered into the QWeb dataLayer.push template
                    event_id = getattr(request, 'fb_pv_event_id', f'pv_{int(time.time() * 1000)}')
                    trigger_backend_capi('PageView', {}, event_id=event_id)

        except Exception as e:
            _logger.warning("CAPI PageView Intercept error: %s", e)

        return res
