import time
import logging
from odoo import models
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

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

            # Fire PageView for all successful HTML GET requests on public pages
            if method == 'GET' and hasattr(response, 'status_code') and response.status_code == 200:
                mimetype = getattr(response, 'mimetype', '') or ''
                if 'text/html' in mimetype and not path.startswith(('/web', '/odoo', '/logo', '/mail')):
                    # Generate ONE event_id used by BOTH dataLayer and CAPI
                    event_id = f'pv_{int(time.time() * 1000)}'

                    # 1) Inject dataLayer.push into the HTML <head>
                    script = (
                        '<script>'
                        'window.dataLayer=window.dataLayer||[];'
                        'dataLayer.push({event:"meta_pageview",'
                        f'event_id:"{event_id}"'
                        '});'
                        '</script>'
                    )
                    try:
                        body = res.get_data(as_text=True)
                        res.set_data(body.replace('</head>', script + '</head>'))
                    except Exception:
                        pass

                    # 2) Fire CAPI with the SAME event_id
                    from odoo.addons.gadgetflix_facebook_capi.controllers.main import trigger_backend_capi
                    trigger_backend_capi('PageView', {}, event_id=event_id)

        except Exception as e:
            _logger.warning("CAPI PageView Intercept error: %s", e)

        return res
