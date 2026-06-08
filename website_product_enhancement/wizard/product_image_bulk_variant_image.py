# © 2024 — website_product_enhancement
# License: LGPL-3

from odoo import models, fields


class ProductImageBulkVariantImage(models.TransientModel):
    """One image row inside a variant line."""

    _name = 'product.image.bulk.variant.image'
    _description = 'Bulk Wizard – Variant Image Line'
    _order = 'sequence, id'

    variant_line_id = fields.Many2one(
        'product.image.bulk.variant.line',
        string="Variant Line",
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    image = fields.Binary("Image", required=True, attachment=False)
    image_filename = fields.Char("Filename")
