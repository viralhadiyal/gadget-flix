from odoo import fields, models


class ShiprocketIntegrationTransfer(models.Model):
    _inherit = "stock.picking"

    sr_integration_eway_bill = fields.Char(string="E-Way Bill", copy=False)
    sr_integration_order_refs = fields.Char(
        string="SR Order References",
        copy=False,
        readonly=True,
        help="Remote order references returned by Shiprocket Integration and used during cancellation.",
    )
