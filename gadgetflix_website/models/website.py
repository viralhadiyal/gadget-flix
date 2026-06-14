# -*- coding: utf-8 -*-

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    gadgetflix_llms_txt_content = fields.Text(string="LLMS.txt Content")
