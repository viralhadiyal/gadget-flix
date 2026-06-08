# © 2024 — website_product_enhancement
# License: LGPL-3

from odoo import models, fields


class ProductImageBulkTemplateLine(models.TransientModel):
    """One image row in the 'Template Images' section of the wizard."""

    _name = 'product.image.bulk.template.line'
    _description = 'Bulk Wizard – Template Image Line'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'product.image.bulk.wizard',
        string="Wizard",
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    image = fields.Binary("Image", required=True, attachment=False)
    image_filename = fields.Char("Filename")
