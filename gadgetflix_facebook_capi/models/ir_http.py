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

            # Fire PageView for all successful HTML GET requests
            if method == 'GET' and hasattr(response, 'status_code') and response.status_code == 200:
                mimetype = getattr(response, 'mimetype', '')
                if 'text/html' in mimetype and not path.startswith(('/web', '/logo', '/mail')):
                    # Import here to avoid circular imports if any
                    from odoo.addons.gadgetflix_facebook_capi.controllers.main import trigger_backend_capi
                    trigger_backend_capi('PageView', {})
                    
        except Exception as e:
            _logger.warning("CAPI PageView Intercept error: %s", e)
            
        return res
