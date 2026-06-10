# © 2024 — website_product_enhancement
# License: LGPL-3

from odoo import models, fields, api


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
    variant_image_ids = fields.One2many(
        'product.image.bulk.variant.image', 'variant_line_id', string="Images Preview"
    )
    
    @api.onchange('image_attachment_ids')
    def _onchange_image_attachment_ids(self):
        for rec in self:
            if rec.image_attachment_ids:
                new_lines = []
                for att in rec.image_attachment_ids:
                    is_main = False
                    if not rec.variant_image_ids and not new_lines:
                        is_main = True
                    new_lines.append((0, 0, {
                        'image': att.datas,
                        'image_filename': att.name,
                        'is_main_image': is_main,
                    }))
                lines = [(4, line.id) for line in rec.variant_image_ids]
                lines.extend([(0, 0, vals) for _, _, vals in new_lines])
                rec.variant_image_ids = lines
                rec.image_attachment_ids = [(5, 0, 0)]
    image_action = fields.Selection([
        ('replace', 'Replace Existing Images'),
        ('add', 'Add/Keep Images')
    ], string="Action", default='replace')

    image_count = fields.Integer(
        string="Images", compute='_compute_image_count',
    )

    def _compute_image_count(self):
        for rec in self:
            rec.image_count = len(rec.variant_image_ids)
