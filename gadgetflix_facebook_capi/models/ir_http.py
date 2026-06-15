import logging
from odoo import models

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    # PageView is handled automatically by the Meta Pixel base code loaded via GTM.
    # Firing a server-side PageView would create duplicates that cannot be deduplicated
    # because the GTM auto-PageView has no event_id we can match against.
    # All other events (ViewContent, AddToCart, etc.) are handled in controllers/main.py
    # and models/sale_order.py with matching event_ids on both browser and server.
