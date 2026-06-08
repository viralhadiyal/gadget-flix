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
        string="Template Images",
    )
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

        attachments = self.template_attachment_ids
        if attachments:
            self.env['product.image'].search([
                ('product_tmpl_id', '=', self.product_tmpl_id.id),
                ('product_variant_id', '=', False),
            ]).unlink()
            for idx, att in enumerate(attachments):
                if idx == 0:
                    self.product_tmpl_id.image_1920 = att.datas
                else:
                    self.env['product.image'].create({
                        'name': att.name or self.product_tmpl_id.name,
                        'product_tmpl_id': self.product_tmpl_id.id,
                        'image_1920': att.datas,
                        'sequence': idx,
                    })

        for vline in self.variant_line_ids:
            variant = vline.product_id
            if self.bulk_weight:
                variant.weight = self.bulk_weight
                self.product_tmpl_id.weight = self.bulk_weight
            elif vline.weight:
                variant.weight = vline.weight

            var_attachments = vline.image_attachment_ids
            if var_attachments:
                self.env['product.image'].search([
                    ('product_variant_id', '=', variant.id),
                ]).unlink()
                for idx, att in enumerate(var_attachments):
                    if idx == 0:
                        variant.image_variant_1920 = att.datas
                    else:
                        self.env['product.image'].create({
                            'name': att.name or variant.display_name,
                            'product_variant_id': variant.id,
                            'image_1920': att.datas,
                            'sequence': idx,
                        })

        return {'type': 'ir.actions.act_window_close'}
