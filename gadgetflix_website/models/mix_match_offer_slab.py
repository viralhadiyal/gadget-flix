# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class MixMatchOfferSlab(models.Model):
    _name = 'gadgetflix.mix.match.offer.slab'
    _description = 'Mix & Match Offer Slab'
    _order = 'sequence, quantity desc'

    sequence = fields.Integer(string="Sequence", default=10)
    offer_id = fields.Many2one('gadgetflix.mix.match.offer', string="Offer", required=True, ondelete='cascade')
    quantity = fields.Integer(string="Quantity", required=True, default=1)
    fixed_price = fields.Monetary(string="Fixed Price", required=True)
    currency_id = fields.Many2one('res.currency', related='offer_id.currency_id')

    @api.constrains('quantity', 'fixed_price')
    def _check_slab_values(self):
        for slab in self:
            if slab.quantity <= 0:
                raise ValidationError("Slab quantity must be greater than 0.")
            if slab.fixed_price < 0:
                raise ValidationError("Slab fixed price cannot be negative.")
