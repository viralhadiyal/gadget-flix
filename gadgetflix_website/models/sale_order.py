# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.tools.safe_eval import safe_eval
from odoo.osv import expression

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_mix_match_eligible_lines(self, offer):
        self.ensure_one()
        eligible_lines = self.env['sale.order.line']
        lines_to_check = self.order_line.filtered(lambda l: not l.display_type and not getattr(l, 'is_delivery', False) and not getattr(l, 'reward_id', False) and l.product_uom_qty > 0)
        if not lines_to_check:
            return eligible_lines

        if offer.apply_discount_on == 'internal_category':
            eligible_lines = lines_to_check.filtered(lambda l: l.product_id.categ_id.id in offer.internal_category_ids.ids or any(c.id in offer.internal_category_ids.ids for c in l.product_id.categ_id.parents_and_self))
        elif offer.apply_discount_on == 'website_category':
            eligible_lines = lines_to_check.filtered(lambda l: set(l.product_template_id.public_categ_ids.ids).intersection(set(offer.website_category_ids.ids)))
        elif offer.apply_discount_on == 'product_template':
            eligible_lines = lines_to_check.filtered(lambda l: l.product_template_id.id in offer.product_tmpl_ids.ids)
        elif offer.apply_discount_on == 'product_variant':
            eligible_lines = lines_to_check.filtered(lambda l: l.product_id.id in offer.product_variant_ids.ids)
        elif offer.apply_discount_on == 'product_tag':
            eligible_lines = lines_to_check.filtered(lambda l: set(l.product_template_id.product_tag_ids.ids).intersection(set(offer.product_tag_ids.ids)))
        elif offer.apply_discount_on == 'product_attribute':
            eligible_lines = lines_to_check.filtered(lambda l: any(attr.id in offer.attribute_ids.ids for attr in l.product_id.product_template_attribute_value_ids.attribute_id) or any(attr.id in offer.attribute_ids.ids for attr in l.product_id.product_tmpl_id.attribute_line_ids.attribute_id))
        elif offer.apply_discount_on == 'product_attribute_value':
            eligible_lines = lines_to_check.filtered(lambda l: set(l.product_id.product_template_attribute_value_ids.product_attribute_value_id.ids).intersection(set(offer.attribute_value_ids.ids)))
        elif offer.apply_discount_on == 'custom_domain':
            try:
                domain = safe_eval(offer.custom_domain)
                products = self.env['product.product'].search(domain)
                eligible_lines = lines_to_check.filtered(lambda l: l.product_id.id in products.ids)
            except Exception:
                pass

        return eligible_lines

    def _compute_mix_match_discounts(self):
        for order in self:
            if order.state not in ['draft', 'sent'] or self.env.context.get('skip_mix_match_recompute'):
                continue
                
            lines_with_discount = order.order_line.filtered(lambda l: l.mix_match_discount_applied)
            for line in lines_with_discount:
                reset_vals = {
                    'mix_match_discount_applied': False,
                    'mix_match_offer_id': False,
                }
                if line.mix_match_original_price > 0:
                    reset_vals['price_unit'] = line.mix_match_original_price
                    
                line.with_context(skip_mix_match_recompute=True).write(reset_vals)

            now = fields.Datetime.now()
            domain = [
                ('active', '=', True),
                '|', ('date_start', '=', False), ('date_start', '<=', now),
                '|', ('date_end', '=', False), ('date_end', '>=', now),
                ('company_id', 'in', [False, order.company_id.id]),
            ]
            
            if order.website_id:
                domain += [('apply_on_website', '=', True), ('is_published', '=', True)]
            else:
                domain += [('apply_in_backend', '=', True)]

            offers = self.env['gadgetflix.mix.match.offer'].search(domain)
            if not offers:
                continue

            offer_evaluations = []
            
            for offer in offers:
                eligible_lines = order._get_mix_match_eligible_lines(offer)
                if not eligible_lines:
                    continue
                
                total_qty = sum(eligible_lines.mapped('product_uom_qty'))
                if total_qty <= 0:
                    continue
                
                slabs = offer.slab_ids.sorted(key=lambda s: s.quantity, reverse=True)
                offer_price = 0.0
                remaining_qty = total_qty
                
                for slab in slabs:
                    if remaining_qty >= slab.quantity:
                        num_slabs = int(remaining_qty // slab.quantity)
                        offer_price += num_slabs * slab.fixed_price
                        remaining_qty -= num_slabs * slab.quantity
                
                flattened_items = []
                for line in eligible_lines:
                    unit_price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    for _ in range(int(line.product_uom_qty)):
                        flattened_items.append({'line': line, 'price': unit_price})
                        
                flattened_items.sort(key=lambda x: x['price'], reverse=True)
                
                matched_qty = int(total_qty - remaining_qty)
                covered_items = flattened_items[:matched_qty]
                uncovered_items = flattened_items[matched_qty:]
                
                covered_original_price = sum(item['price'] for item in covered_items)
                uncovered_original_price = sum(item['price'] for item in uncovered_items)
                
                discount_amount = covered_original_price - offer_price
                
                if discount_amount > 0:
                    offer_evaluations.append({
                        'offer': offer,
                        'eligible_lines': eligible_lines,
                        'discount_amount': discount_amount,
                        'covered_original_price': covered_original_price,
                        'total_original_price': covered_original_price + uncovered_original_price,
                    })

            if not offer_evaluations:
                continue
                
            offer_evaluations.sort(key=lambda x: (-x['discount_amount'] if x['offer'].conflict_strategy == 'best_discount' else 0, x['offer'].sequence))
            
            applied_lines = self.env['sale.order.line']
            
            for eval_data in offer_evaluations:
                offer = eval_data['offer']
                lines = eval_data['eligible_lines'] - applied_lines
                if not lines:
                    continue
                
                if len(lines) != len(eval_data['eligible_lines']):
                    total_qty = sum(lines.mapped('product_uom_qty'))
                    slabs = offer.slab_ids.sorted(key=lambda s: s.quantity, reverse=True)
                    offer_price = 0.0
                    remaining_qty = total_qty
                    
                    for slab in slabs:
                        if remaining_qty >= slab.quantity:
                            num_slabs = int(remaining_qty // slab.quantity)
                            offer_price += num_slabs * slab.fixed_price
                            remaining_qty -= num_slabs * slab.quantity
                            
                    flattened_items = []
                    for line in lines:
                        unit_price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                        for _ in range(int(line.product_uom_qty)):
                            flattened_items.append({'line': line, 'price': unit_price})
                            
                    flattened_items.sort(key=lambda x: x['price'], reverse=True)
                    matched_qty = int(total_qty - remaining_qty)
                    covered_items = flattened_items[:matched_qty]
                    covered_original_price = sum(item['price'] for item in covered_items)
                    
                    discount_amount = covered_original_price - offer_price
                    if discount_amount <= 0:
                        continue
                else:
                    discount_amount = eval_data['discount_amount']
                    covered_original_price = eval_data['covered_original_price']
                
                if offer.split_method == 'equal':
                    per_item_discount = discount_amount / sum(lines.mapped('product_uom_qty'))
                    for line in lines:
                        line_discount_amount = per_item_discount * line.product_uom_qty
                        
                        if line.product_uom_qty > 0:
                            original_price_unit = line.price_unit
                            line_subtotal_no_disc = original_price_unit * line.product_uom_qty
                            new_subtotal = max(0.0, line_subtotal_no_disc - line_discount_amount)
                            new_price_unit = new_subtotal / line.product_uom_qty
                            
                            line.with_context(skip_mix_match_recompute=True).write({
                                'mix_match_discount_applied': True,
                                'mix_match_offer_id': offer.id,
                                'mix_match_original_price': original_price_unit,
                                'price_unit': new_price_unit,
                            })
                else:
                    total_eligible_subtotal = sum(l.price_unit * l.product_uom_qty for l in lines)
                    for line in lines:
                        line_original_subtotal = line.price_unit * line.product_uom_qty
                        if total_eligible_subtotal > 0:
                            line_discount_amount = discount_amount * (line_original_subtotal / total_eligible_subtotal)
                        else:
                            line_discount_amount = 0.0
                        
                        if line.product_uom_qty > 0:
                            original_price_unit = line.price_unit
                            new_subtotal = max(0.0, line_original_subtotal - line_discount_amount)
                            new_price_unit = new_subtotal / line.product_uom_qty
                            
                            line.with_context(skip_mix_match_recompute=True).write({
                                'mix_match_discount_applied': True,
                                'mix_match_offer_id': offer.id,
                                'mix_match_original_price': original_price_unit,
                                'price_unit': new_price_unit,
                            })
                
                applied_lines |= lines

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._compute_mix_match_discounts()
        return records

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('skip_mix_match_recompute'):
            self._compute_mix_match_discounts()
        return res
