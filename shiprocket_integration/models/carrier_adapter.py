import json
import logging
from datetime import timedelta

import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from .service_client import RocketDeliveryGateway


_logger = logging.getLogger(__name__)


class ShiprocketIntegrationCarrierAdapter(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("shiprocket_integration", "Shiprocket Integration")],
        ondelete={"shiprocket_integration": lambda carriers: carriers.write({
            "delivery_type": "fixed",
            "fixed_price": 0,
        })},
    )
    sr_integration_login_email = fields.Char(
        string="API Login Email",
        help="Email of the Shiprocket API user.",
    )
    sr_integration_secret_key = fields.Char(
        string="API Password",
        groups="base.group_system",
        help="Password of the Shiprocket API user.",
    )
    sr_integration_token = fields.Text(
        string="Session Token",
        copy=False,
        help="Bearer token created from the configured API credentials.",
    )
    sr_integration_token_expiry = fields.Datetime(
        string="Session Valid Until",
        copy=False,
        help="The token is refreshed automatically before Shiprocket expires it.",
    )
    sr_integration_channel_id = fields.Many2one(
        "shiprocket.integration.channel",
        string="Sales Channel",
        domain="[('api_email', '=', sr_integration_login_email)]",
        help="Channel used when creating Shiprocket orders.",
    )
    sr_integration_courier_ids = fields.Many2many(
        "shiprocket.integration.courier",
        "shiprocket_integration_carrier_courier_rel",
        "carrier_id",
        "courier_id",
        string="Allowed Couriers",
        copy=False,
        domain="[('api_email', '=', sr_integration_login_email)]",
        help="When empty, Shiprocket's recommended service is used.",
    )
    sr_integration_package_type_id = fields.Many2one(
        "stock.package.type",
        string="Default Parcel Box",
        help="Default dimensions used when an order has no explicit package.",
    )
    sr_integration_generate_manifest = fields.Boolean(
        string="Create Manifest",
        help="Ask Shiprocket to create a manifest with the label.",
    )
    sr_integration_request_pickup = fields.Boolean(
        string="Request Pickup",
        default=True,
        help="Request pickup when the delivery order is validated.",
    )

    def action_sr_integration_ping(self):
        self.ensure_one()
        if self.delivery_type != "shiprocket_integration":
            return False

        client = RocketDeliveryGateway(self, self.log_xml)
        response = client.authenticate()
        if response.get("token"):
            self.write({
                "sr_integration_token": response["token"],
                "sr_integration_token_expiry": fields.Datetime.now() + timedelta(days=9),
            })
            message_type = "success"
            message = _("Connection validated and token refreshed.")
        else:
            message_type = "danger"
            message = client.error_text(response) or _("Authentication failed. Check the API credentials.")

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Shiprocket Integration"),
                "type": message_type,
                "message": message,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def action_sr_integration_import_channels(self):
        channel_model = self.env["shiprocket.integration.channel"]
        for carrier in self.filtered(lambda item: item.delivery_type == "shiprocket_integration"):
            remote_channels = RocketDeliveryGateway(carrier, self.log_xml).pull_channels()
            if not remote_channels:
                raise ValidationError(_("No Shiprocket channels were returned for this API account."))

            stale_channels = channel_model.search([("api_email", "=", carrier.sr_integration_login_email)])
            create_values = []
            for name, remote_id in remote_channels.items():
                existing = stale_channels.filtered(lambda channel: channel.external_channel_id == remote_id)
                stale_channels -= existing
                if not existing:
                    create_values.append({
                        "name": name,
                        "external_channel_id": remote_id,
                        "api_email": carrier.sr_integration_login_email,
                    })
            if create_values:
                channel_model.create(create_values)
            stale_channels.unlink()

    def action_sr_integration_import_couriers(self):
        courier_model = self.env["shiprocket.integration.courier"]
        for carrier in self.filtered(lambda item: item.delivery_type == "shiprocket_integration"):
            remote_couriers = RocketDeliveryGateway(carrier, self.log_xml).pull_couriers()
            if not remote_couriers:
                raise ValidationError(_("No Shiprocket couriers were returned for this API account."))

            stale_couriers = courier_model.search([("api_email", "=", carrier.sr_integration_login_email)])
            create_values = []
            for courier in remote_couriers:
                remote_id = courier.get("id")
                existing = stale_couriers.filtered(lambda item: item.external_courier_id == remote_id)
                stale_couriers -= existing
                if not existing:
                    create_values.append({
                        "name": courier.get("name"),
                        "external_courier_id": remote_id,
                        "api_email": carrier.sr_integration_login_email,
                    })
            if create_values:
                courier_model.create(create_values)
            stale_couriers.unlink()

    def _sr_integration_weight_kg(self, weight):
        self.ensure_one()
        weight_uom = self.env["product.template"]._get_weight_uom_id_from_ir_config_parameter()
        return weight_uom._compute_quantity(weight, self.env.ref("uom.product_uom_kgm"), round=False)

    def _sr_integration_price_from_inr(self, order, amount):
        return self.env.ref("base.INR")._convert(
            amount,
            order.currency_id,
            order.company_id,
            fields.Date.context_today(self),
        )

    def shiprocket_integration_rate_shipment(self, order):
        client = RocketDeliveryGateway(self, self.log_xml)
        result = client.build_quote(
            order.partner_shipping_id,
            order.warehouse_id.partner_id or order.warehouse_id.company_id.partner_id,
            order=order,
        )
        if result.get("error_found"):
            return {
                "success": False,
                "price": 0.0,
                "error_message": result["error_found"],
                "warning_message": False,
            }

        price = float(result.get("price") or 0.0)
        if order.currency_id != self.env.ref("base.INR"):
            price = self._sr_integration_price_from_inr(order, price)
        return {
            "success": True,
            "price": price,
            "error_message": False,
            "warning_message": result.get("warning_message"),
        }

    def shiprocket_integration_send_shipping(self, pickings):
        client = RocketDeliveryGateway(self, self.log_xml)
        results = []
        for picking in pickings:
            shipment = client.submit_bookings(picking)
            picking.sr_integration_order_refs = " + ".join(shipment.get("order_ids"))
            tracking_number = " + ".join(filter(None, shipment.get("tracking_numbers")))
            results.append({
                "tracking_number": tracking_number,
                "exact_price": shipment.get("exact_price"),
            })

            for package_data in shipment["packages"].values():
                response = package_data.get("response") or {}
                courier = response.get("courier_name")
                awb = response.get("awb_code")
                if response.get("warning_message"):
                    picking.message_post(body=response["warning_message"])
                if response.get("label_url"):
                    label_data = self._sr_integration_download(response["label_url"])
                    if label_data:
                        picking.message_post(
                            body=_(
                                "Label generated for %(courier)s with tracking number %(tracking)s.",
                                courier=courier,
                                tracking=awb,
                            ),
                            attachments=[("%s-%s.pdf" % (courier, awb), label_data)],
                        )
                if self.sr_integration_generate_manifest and response.get("manifest_url"):
                    manifest_data = self._sr_integration_download(response["manifest_url"])
                    if manifest_data:
                        picking.message_post(
                            body=_("Manifest generated for %s.", courier),
                            attachments=[("Manifest-%s-%s.pdf" % (courier, awb), manifest_data)],
                        )

            if not self.prod_environment:
                picking.carrier_tracking_ref = tracking_number
                self.shiprocket_integration_cancel_shipment(picking)
        return results

    def _sr_integration_download(self, url):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            _logger.info("Shiprocket Integration document downloaded from %s", url)
            return response.content
        except requests.exceptions.HTTPError as error:
            _logger.warning("Shiprocket Integration document download failed from %s: %s", url, error)
        except requests.exceptions.ConnectionError as error:
            _logger.warning("Shiprocket Integration document connection failed for %s: %s", url, error)
        return False

    def shiprocket_integration_get_tracking_link(self, picking):
        tracking_numbers = picking.carrier_tracking_ref.split(" + ") if picking.carrier_tracking_ref else []
        tracking_links = [
            (tracking_number, "https://shiprocket.co/tracking/%s" % tracking_number)
            for tracking_number in tracking_numbers
            if tracking_number
        ]
        if len(tracking_links) == 1:
            return tracking_links[0][1]
        return json.dumps(tracking_links)

    def shiprocket_integration_cancel_shipment(self, picking):
        client = RocketDeliveryGateway(self, self.log_xml)
        pickup_requested = picking.carrier_id.sr_integration_request_pickup
        remote_refs = []

        if pickup_requested:
            if not picking.sr_integration_order_refs:
                picking.message_post(body=_("No Shiprocket Integration order reference is available for cancellation."))
            else:
                remote_refs = picking.sr_integration_order_refs.split(" + ")
        elif not picking.carrier_tracking_ref:
            picking.message_post(body=_("No AWB number is available for cancellation."))
        else:
            remote_refs = picking.carrier_tracking_ref.split(" + ")

        if remote_refs:
            for remote_ref, response in client.void_remote_documents(remote_refs, pickup_requested).items():
                if response.get("status") == 200 or response.get("message"):
                    prefix = "Order #" if pickup_requested else "AWB #"
                    picking.message_post(body="%s%s - %s" % (
                        prefix,
                        remote_ref,
                        response.get("message") or _("Cancelled successfully."),
                    ))

        if not self.prod_environment:
            picking.carrier_tracking_ref = ""
