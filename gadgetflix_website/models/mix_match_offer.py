# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class MixMatchOffer(models.Model):
    _name = 'gadgetflix.mix.match.offer'
    _description = 'Mix & Match Offer Master'
    _order = 'sequence asc, id desc'

    name = fields.Char(string="Offer Name", required=True)
    active = fields.Boolean(default=True)
    is_published = fields.Boolean(string="Published", default=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    date_start = fields.Datetime(string="Start Date")
    date_end = fields.Datetime(string="End Date")

    apply_in_backend = fields.Boolean(string="Apply in Backend", default=True)
    apply_on_website = fields.Boolean(string="Apply on Website", default=True)

    apply_discount_on = fields.Selection([
        ('internal_category', 'Internal Product Category'),
        ('website_category', 'Website / eCommerce Category'),
        ('product_template', 'Product Template'),
        ('product_variant', 'Product Variant'),
        ('product_tag', 'Product Tag'),
        ('product_attribute', 'Product Attribute'),
        ('product_attribute_value', 'Product Attribute Value'),
        ('custom_domain', 'Custom Domain'),
    ], string="Apply Discount On", required=True, default='website_category')

    internal_category_ids = fields.Many2many('product.category', string="Internal Categories")
    website_category_ids = fields.Many2many('product.public.category', string="Website Categories")
    product_tmpl_ids = fields.Many2many('product.template', string="Product Templates")
    product_variant_ids = fields.Many2many('product.product', string="Product Variants")
    product_tag_ids = fields.Many2many('product.tag', string="Product Tags")
    attribute_ids = fields.Many2many('product.attribute', string="Attributes")
    attribute_value_ids = fields.Many2many('product.attribute.value', string="Attribute Values")
    custom_domain = fields.Text(string="Custom Domain")

    split_method = fields.Selection([
        ('equal', 'Equal Split'),
        ('proportional', 'Proportional By Amount'),
    ], string="Split Method", default='proportional', required=True)

    conflict_strategy = fields.Selection([
        ('sequence', 'Use Sequence Priority'),
        ('best_discount', 'Apply Best Discount'),
    ], string="Conflict Strategy", default='sequence', required=True)

    slab_ids = fields.One2many('gadgetflix.mix.match.offer.slab', 'offer_id', string="Slabs")

    @api.constrains('slab_ids')
    def _check_slabs(self):
        for offer in self:
            if not offer.slab_ids:
                raise ValidationError("At least one slab is required for the offer.")
            quantities = offer.slab_ids.mapped('quantity')
            if len(quantities) != len(set(quantities)):
                raise ValidationError("Duplicate quantities are not allowed in the same offer.")

    @api.constrains('apply_discount_on', 'internal_category_ids', 'website_category_ids', 'product_tmpl_ids', 'product_variant_ids', 'product_tag_ids', 'attribute_ids', 'attribute_value_ids', 'custom_domain')
    def _check_conditions(self):
        for offer in self:
            if offer.apply_discount_on == 'internal_category' and not offer.internal_category_ids:
                raise ValidationError("Please select Internal Product Categories.")
            if offer.apply_discount_on == 'website_category' and not offer.website_category_ids:
                raise ValidationError("Please select Website / eCommerce Categories.")
            if offer.apply_discount_on == 'product_template' and not offer.product_tmpl_ids:
                raise ValidationError("Please select Product Templates.")
            if offer.apply_discount_on == 'product_variant' and not offer.product_variant_ids:
                raise ValidationError("Please select Product Variants.")
            if offer.apply_discount_on == 'product_tag' and not offer.product_tag_ids:
                raise ValidationError("Please select Product Tags.")
            if offer.apply_discount_on == 'product_attribute' and not offer.attribute_ids:
                raise ValidationError("Please select Product Attributes.")
            if offer.apply_discount_on == 'product_attribute_value' and not offer.attribute_value_ids:
                raise ValidationError("Please select Product Attribute Values.")
            if offer.apply_discount_on == 'custom_domain' and not offer.custom_domain:
                raise ValidationError("Please enter a Custom Domain.")
