# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    gadgetflix_show_featured_home = fields.Boolean(string="Show in Featured Products")
    gadgetflix_show_new_arrival_home = fields.Boolean(string="Show in New Arrivals")
    gadgetflix_show_anti_yellow = fields.Boolean(string="Show on Anti Yellow Page")
    gadgetflix_show_about_page = fields.Boolean(string="Show on About Page")
