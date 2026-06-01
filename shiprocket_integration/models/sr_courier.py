from odoo import fields, models


class ShiprocketIntegrationCourier(models.Model):
    _name = "shiprocket.integration.courier"
    _description = "Shiprocket Integration Courier Service"
    _order = "name"

    name = fields.Char(string="Courier", readonly=True)
    external_courier_id = fields.Integer(string="Remote Courier ID", readonly=True)
    api_email = fields.Char(string="API Account")
