from odoo import fields, models


class ShiprocketIntegrationChannel(models.Model):
    _name = "shiprocket.integration.channel"
    _description = "Shiprocket Integration Sales Channel"
    _order = "name"

    name = fields.Char(string="Channel", readonly=True)
    external_channel_id = fields.Integer(string="Remote Channel ID", readonly=True)
    api_email = fields.Char(string="API Account")
