# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    gadgetflix_show_home = fields.Boolean(string="Show on Homepage")
    gadgetflix_show_accessories_menu = fields.Boolean(string="Show in Accessories Menu")
