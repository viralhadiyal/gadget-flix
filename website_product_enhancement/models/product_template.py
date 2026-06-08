# License: LGPL-3

from odoo import api, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _search_get_detail(self, website, order, options):
        result = super()._search_get_detail(website, order, options)
        result['search_fields'].append('attribute_line_ids.value_ids.name')
        return result

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('default_code'):
                vals['default_code'] = (
                        self.env['ir.sequence'].next_by_code(
                            'product.product.internal.ref'
                        ) or '/'
                )
        return super().create(vals_list)