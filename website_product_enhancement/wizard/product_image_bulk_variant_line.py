# © 2024 — website_product_enhancement
# License: LGPL-3

from odoo import models, fields


class ProductImageBulkVariantLine(models.TransientModel):
    _name = 'product.image.bulk.variant.line'
    _description = 'Bulk Wizard – Variant Line'

    wizard_id = fields.Many2one(
        'product.image.bulk.wizard', required=True, ondelete='cascade',
    )
    # NOT readonly=True — readonly fields are NEVER sent back in form submissions.
    # We control editability in the view (invisible="1") instead.
    product_id = fields.Many2one('product.product', string="Variant")
    variant_name = fields.Char("Variant")
    weight = fields.Float("Weight (kg)", digits='Stock Weight')

    image_attachment_ids = fields.Many2many(
        'ir.attachment',
        'wpe_bulk_variant_att_rel',
        'variant_line_id', 'attachment_id',
        string="Images",
    )

    image_count = fields.Integer(
        string="Images", compute='_compute_image_count',
    )

    def _compute_image_count(self):
        for rec in self:
            rec.image_count = len(rec.image_attachment_ids)
