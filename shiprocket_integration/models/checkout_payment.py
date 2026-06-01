from odoo import _, api, models
from odoo.addons.payment import utils as payment_utils


class ShiprocketIntegrationCheckoutFilter(models.Model):
    _inherit = "payment.provider"

    @api.model
    def _get_compatible_providers(self, *args, sale_order_id=None, report=None, **kwargs):
        providers = super()._get_compatible_providers(
            *args,
            sale_order_id=sale_order_id,
            report=report,
            **kwargs,
        )
        order = self.env["sale.order"].browse(sale_order_id).exists() if sale_order_id else self.env["sale.order"]
        carrier = order.carrier_id if order else self.env["delivery.carrier"]

        if carrier.delivery_type == "shiprocket_integration" and carrier.allow_cash_on_delivery:
            before_filter = providers
            providers = providers.filtered(lambda provider: provider.custom_mode == "cash_on_delivery")
            payment_utils.add_to_report(
                report,
                before_filter - providers,
                available=False,
                reason=_("The selected courier method only accepts collect-on-delivery payments."),
            )

        return providers
