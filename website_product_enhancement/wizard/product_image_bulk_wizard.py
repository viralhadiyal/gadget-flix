# © 2024 — website_product_enhancement
# License: LGPL-3

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductImageBulkWizard(models.TransientModel):
    _name = 'product.image.bulk.wizard'
    _description = 'Bulk Image Upload Wizard'

    product_tmpl_id = fields.Many2one('product.template', string="Product")
    template_attachment_ids = fields.Many2many(
        'ir.attachment',
        'wpe_bulk_tmpl_att_rel',
        'wizard_id', 'attachment_id',
        string="Images",
    )
    template_image_line_ids = fields.One2many(
        'product.image.bulk.template.line', 'wizard_id', string="Images Preview"
    )
    
    @api.onchange('template_attachment_ids')
    def _onchange_template_attachment_ids(self):
        for rec in self:
            if rec.template_attachment_ids:
                new_lines = []
                for att in rec.template_attachment_ids:
                    is_main = False
                    if not rec.template_image_line_ids and not new_lines:
                        is_main = True
                    new_lines.append((0, 0, {
                        'image': att.datas,
                        'image_filename': att.name,
                        'is_main_image': is_main,
                    }))
                lines = [(4, line.id) for line in rec.template_image_line_ids]
                lines.extend([(0, 0, vals) for _, _, vals in new_lines])
                rec.template_image_line_ids = lines
                rec.template_attachment_ids = [(5, 0, 0)]
    template_image_action = fields.Selection([
        ('replace', 'Replace Existing Images'),
        ('add', 'Add/Keep Images')
    ], string="Action", default='replace')
    variant_line_ids = fields.One2many(
        'product.image.bulk.variant.line', 'wizard_id', string="Variants",
    )
    bulk_weight = fields.Float("Bulk Weight (all variants)", digits='Stock Weight')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        product_tmpl_id = (
            self.env.context.get('active_id')
            or (self.env.context.get('active_ids') or [None])[0]
        )
        if product_tmpl_id:
            tmpl = self.env['product.template'].browse(product_tmpl_id)
            if tmpl.exists():
                res['product_tmpl_id'] = tmpl.id
                if 'variant_line_ids' in fields_list:
                    res['variant_line_ids'] = [
                        (0, 0, {'product_id': v.id, 'variant_name': v.display_name})
                        for v in tmpl.product_variant_ids
                    ]
        return res

    def action_apply(self):
        self.ensure_one()
        if not self.product_tmpl_id:
            raise UserError(_("No product selected. Please reopen this wizard from a product form."))

        if self.template_image_line_ids or self.template_image_action == 'replace':
            if self.template_image_action == 'replace':
                self.env['product.image'].search([
                    ('product_tmpl_id', '=', self.product_tmpl_id.id),
                    ('product_variant_id', '=', False),
                ]).unlink()

            for idx, line in enumerate(self.template_image_line_ids):
                if line.is_main_image:
                    self.product_tmpl_id.image_1920 = line.image
                else:
                    self.env['product.image'].create({
                        'name': line.image_filename or self.product_tmpl_id.name,
                        'product_tmpl_id': self.product_tmpl_id.id,
                        'image_1920': line.image,
                        'sequence': idx + 10,
                    })

        for vline in self.variant_line_ids:
            variant = vline.product_id
            if self.bulk_weight:
                variant.weight = self.bulk_weight
                self.product_tmpl_id.weight = self.bulk_weight
            elif vline.weight:
                variant.weight = vline.weight

            if vline.variant_image_ids or vline.image_action == 'replace':
                if vline.image_action == 'replace':
                    self.env['product.image'].search([
                        ('product_variant_id', '=', variant.id),
                    ]).unlink()
                
                for idx, line in enumerate(vline.variant_image_ids):
                    if line.is_main_image:
                        variant.image_variant_1920 = line.image
                    else:
                        self.env['product.image'].create({
                            'name': line.image_filename or variant.display_name,
                            'product_variant_id': variant.id,
                            'image_1920': line.image,
                            'sequence': idx + 10,
                        })

        return {'type': 'ir.actions.act_window_close'}
