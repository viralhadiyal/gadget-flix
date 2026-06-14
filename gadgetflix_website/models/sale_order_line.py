# -*- coding: utf-8 -*-

from odoo import fields, models, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    mix_match_discount_applied = fields.Boolean(string="Mix & Match Discount Applied", copy=False)
    mix_match_offer_id = fields.Many2one('gadgetflix.mix.match.offer', string="Mix & Match Offer", copy=False)
    mix_match_original_price = fields.Float(string="Mix & Match Original Price", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('skip_mix_match_recompute'):
            records.mapped('order_id')._compute_mix_match_discounts()
        return records

    def write(self, vals):
        mix_match_fields = {'mix_match_discount_applied', 'mix_match_offer_id', 'mix_match_original_price'}
        
        if not self.env.context.get('skip_mix_match_recompute') and not set(vals.keys()).issubset(mix_match_fields):
            res = super().write(vals)
            self.mapped('order_id')._compute_mix_match_discounts()
            return res
        return super().write(vals)

    def unlink(self):
        orders = self.mapped('order_id')
        res = super().unlink()
        if not self.env.context.get('skip_mix_match_recompute'):
            orders._compute_mix_match_discounts()
        return res
