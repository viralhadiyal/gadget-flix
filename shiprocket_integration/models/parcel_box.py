from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ShiprocketIntegrationParcelBox(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(selection_add=[("shiprocket_integration", "SR Integration")])

    @api.constrains("packaging_length", "width", "height", "package_carrier_type")
    def _check_sr_integration_dimensions(self):
        for package in self:
            if package.package_carrier_type != "shiprocket_integration":
                continue
            if any(dimension <= 0 for dimension in (package.packaging_length, package.width, package.height)):
                raise ValidationError(_("Length, width, and height are required for SR Integration packages."))

    @api.depends("package_carrier_type")
    def _compute_length_uom_name(self):
        super()._compute_length_uom_name()
        for package in self.filtered(lambda rec: rec.package_carrier_type == "shiprocket_integration"):
            package.length_uom_name = "cm"
