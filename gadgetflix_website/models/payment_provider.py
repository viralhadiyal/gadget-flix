# -*- coding: utf-8 -*-

from odoo import api, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    @api.model
    def _get_compatible_providers(self, *args, sale_order_id=None, report=None, **kwargs):
        compatible_providers = super()._get_compatible_providers(
            *args, sale_order_id=sale_order_id, report=report, **kwargs
        )
        if sale_order_id and self.env.context.get('gf_show_all_payment_methods'):
            order = self.env['sale.order'].browse(sale_order_id).exists()
            if order:
                # Find all published COD providers that are compatible with the order's basic conditions.
                cod_providers = self.sudo().search([
                    ('custom_mode', '=', 'cash_on_delivery'),
                    ('is_published', '=', True),
                    ('state', 'in', ['test', 'enabled']),
                ])
                for cod_p in cod_providers:
                    if cod_p not in compatible_providers:
                        # Ensure company is compatible
                        if cod_p.company_id and cod_p.company_id.id != order.company_id.id:
                            continue
                        compatible_providers |= cod_p

                        # Remove the "not allowed by selected delivery method" reason from report
                        if report:
                            # The key in report dict can be the record itself
                            report.pop(cod_p, None)
                            # Or it can be the ID or a singleton. Let's cover both.
                            for k in list(report.keys()):
                                if getattr(k, 'id', None) == cod_p.id:
                                    report.pop(k, None)

        return compatible_providers
