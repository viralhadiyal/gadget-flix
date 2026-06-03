import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta

import requests

from odoo import _, fields
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools.urls import urljoin as url_join


_logger = logging.getLogger(__name__)


class RocketDeliveryGateway:
    BASE_URL = "https://apiv2.shiprocket.in/v1/"

    def __init__(self, carrier, debug_logger):
        self.carrier = carrier
        self.debug_logger = debug_logger
        self.session = requests.Session()

    def call_api(self, endpoint, method="GET", payload=None, authenticate=True):
        headers = {"Content-Type": "application/json"}
        if authenticate:
            headers["Authorization"] = "Bearer %s" % self.auth_token()

        url = url_join(self.BASE_URL, endpoint)
        log_key = "sr_integration_%s" % endpoint.strip("/").replace("/", "_")
        logged_payload = payload
        if endpoint == "external/auth/login" and payload:
            logged_payload = {**payload, "password": "********"}
        try:
            self.debug_logger("%s\n%s\n%s" % (url, method, logged_payload), "%s_request" % log_key)
            response = self.session.request(method, url, json=payload, headers=headers, timeout=30)
            self.debug_logger("%s\n%s" % (response.status_code, response.text), "%s_response" % log_key)
            return response.json()
        except requests.exceptions.ConnectionError as error:
            _logger.warning("Shiprocket Integration connection failed for %s: %s", url, error)
            return {"errors": {"connection": _("Cannot reach Shiprocket. Please try again later.")}}
        except ValueError as error:
            _logger.warning("Shiprocket returned invalid JSON for %s: %s", url, error)
            return {"errors": {"json": str(error)}}

    def authenticate(self):
        return self.call_api(
            "external/auth/login",
            "POST",
            {
                "email": self.carrier.sr_integration_login_email,
                "password": self.carrier.sudo().sr_integration_secret_key,
            },
            authenticate=False,
        )

    def auth_token(self):
        if not (self.carrier.sr_integration_login_email and self.carrier.sudo().sr_integration_secret_key):
            action = self.carrier.env.ref("delivery.action_delivery_carrier_form")
            raise RedirectWarning(
                _("Configure Shiprocket Integration credentials on the delivery method."),
                action.id,
                _("Open Delivery Method"),
            )

        expired = (
            self.carrier.sr_integration_token_expiry
            and self.carrier.sr_integration_token_expiry < fields.Datetime.now()
        )
        if not self.carrier.sr_integration_token or expired:
            auth_response = self.authenticate()
            if not auth_response.get("token"):
                raise ValidationError(self.error_text(auth_response) or _("Shiprocket did not accept the API login."))
            self.carrier.write({
                "sr_integration_token": auth_response["token"],
                "sr_integration_token_expiry": fields.Datetime.now() + timedelta(days=9),
            })
        return self.carrier.sr_integration_token

    def error_text(self, response):
        response = response or {}
        errors = response.get("errors") or {}
        payload = response.get("payload") or {}
        message_template = _("Shiprocket API response: %s")

        if errors:
            formatted = []
            for value in errors.values():
                if isinstance(value, list):
                    formatted.append("\n".join(map(str, value)))
                else:
                    formatted.append(str(value or ""))
            return "\n".join(message_template % item for item in formatted if item)
        if response.get("message"):
            return message_template % response["message"]
        if payload.get("error_message"):
            return message_template % payload["error_message"]
        if payload.get("awb_assign_error"):
            return message_template % payload["awb_assign_error"]
        if response.get("response") and not response.get("label_created"):
            return message_template % response["response"]
        return ""

    def pull_channels(self):
        response = self.call_api("external/channels")
        if "data" not in response:
            raise ValidationError(self.error_text(response))
        return {
            channel["name"]: channel["id"]
            for channel in response["data"]
            if channel.get("name") and channel.get("id")
        }

    def pull_couriers(self):
        response = self.call_api("external/courier/courierListWithCounts")
        if "courier_data" not in response:
            raise ValidationError(self.error_text(response))
        return response["courier_data"]

    def lookup_serviceability(self, recipient, warehouse_partner, weight_kg, dimensions):
        domestic_route = recipient.country_id.code == "IN" and warehouse_partner.country_id.code == "IN"
        payload = {
            "cod": "1" if domestic_route and self.carrier.allow_cash_on_delivery else 0,
            "height": dimensions.get("height"),
            "breadth": dimensions.get("width"),
            "length": dimensions.get("length"),
            "delivery_country": recipient.country_id.code,
            "weight": weight_kg,
            "delivery_postcode": recipient.zip,
            "pickup_postcode": warehouse_partner.zip,
        }
        endpoint = (
            "external/courier/serviceability/"
            if domestic_route
            else "external/courier/international/serviceability"
        )
        response = self.call_api(endpoint, payload=payload)
        company_options = (response.get("data") or {}).get("available_courier_companies") or []
        if not company_options:
            return {"error_found": self.error_text(response), "currency": "INR"}

        selected = self._select_courier(company_options)
        if not selected:
            return {"error_found": _("None of the allowed courier services can cover this route."), "currency": "INR"}

        price = selected.get("rate")
        if isinstance(price, dict):
            price = price.get("rate")
        courier_name = selected.get("courier_name")
        recommended = ""
        if not self.carrier.sr_integration_courier_ids:
            recommended = (response.get("data") or {}).get("recommended_by", {}).get("title")

        return {
            "warning_message": (
                _("Recommended by %(source)s: %(service)s", source=recommended, service=courier_name)
                if recommended else _("Selected courier service: %s", courier_name)
            ),
            "courier_code": selected.get("courier_company_id"),
            "price": price,
            "courier_name": courier_name,
            "currency": "INR",
        }

    def _select_courier(self, courier_options):
        allowed_codes = set(self.carrier.sr_integration_courier_ids.mapped("external_courier_id"))
        if not allowed_codes:
            return courier_options[0]
        return next(
            (
                option
                for option in courier_options
                if option.get("courier_company_id") in allowed_codes
            ),
            False,
        )

    def build_quote(self, recipient, warehouse_partner, order=None, picking=None, package=None):
        if not (order or picking):
            raise UserError(_("Select a sale order or transfer before asking for a carrier quote."))

        products = picking.move_ids.product_id if picking else order.order_line.product_id
        self.validate_shipping_inputs(
            recipient,
            warehouse_partner,
            products.filtered(lambda product: product.type == "consu"),
        )

        if package:
            dimensions = package.dimension
            total_weight = package.weight
        else:
            default_package = self.carrier.sr_integration_package_type_id
            packages = (
                self.carrier._get_packages_from_picking(picking, default_package)
                if picking else self.carrier._get_packages_from_order(order, default_package)
            )
            total_weight = sum(pack.weight for pack in packages)
            dimensions = {}
            if len(packages) == 1:
                dimensions = {
                    "length": packages[0].dimension["length"],
                    "width": packages[0].dimension["width"],
                    "height": packages[0].dimension["height"],
                }

        return self.lookup_serviceability(
            recipient,
            warehouse_partner,
            self.carrier._sr_integration_weight_kg(total_weight),
            dimensions,
        )

    def amount_to_inr(self, amount, picking):
        inr = picking.env.ref("base.INR")
        currency = picking.sale_id.currency_id if picking.sale_id else picking.company_id.currency_id
        if currency == inr:
            return amount
        return currency._convert(
            amount,
            inr,
            picking.company_id or picking.env.company,
            picking.date_done or datetime.today(),
        )

    def gst_rate(self, moves):
        taxes = moves.sale_line_id.sudo().tax_ids if moves.sale_line_id else moves.product_id.sudo().taxes_id
        gst_amount = 0.0
        for tax in taxes.flatten_taxes_hierarchy():
            tax_tags = tax.invoice_repartition_line_ids.tag_ids
            if tax_tags and any(
                (tax.env.ref("l10n_in.tax_tag_%sgst" % tag, False) or tax.env["account.account.tag"]) in tax_tags
                for tag in ("c", "s", "i")
            ):
                gst_amount += tax.amount
        return gst_amount

    def compose_item_rows(self, package, picking):
        values_by_product = {}
        parcel_value = 0.0
        destination_moves = picking.env["stock.move"]
        for move in picking.move_ids:
            move_destinations = move._rollup_move_dests(set())
            if move_destinations:
                destination_moves |= picking.env["stock.move"].browse(move_destinations)

        for commodity in package.commodities:
            moves = self._package_moves_for_product(picking, package, commodity.product_id)
            if destination_moves:
                moves = destination_moves.filtered(lambda move: move.product_id == commodity.product_id) or moves

            unit_price = self.amount_to_inr(round(commodity.monetary_value, 2), package.picking_id)
            values_by_product[commodity.product_id.id] = {
                "tax": self.gst_rate(moves),
                "hsn": commodity.product_id.hs_code or "",
                "selling_price": unit_price,
                "units": commodity.qty,
                "sku": commodity.product_id.default_code or "",
                "name": commodity.product_id.name,
            }
            parcel_value += unit_price * commodity.qty

        if parcel_value > 50000 and not picking.sr_integration_eway_bill:
            raise ValidationError(_("Enter the E-Way Bill before booking parcels above 50,000 INR."))
        return values_by_product

    def _package_moves_for_product(self, picking, package, product):
        moves = picking.env["stock.move"]
        for move in picking.move_ids.filtered(lambda item: item.product_id == product):
            if package.name == "Bulk Content":
                if any(not line.result_package_id for line in move.move_line_ids):
                    moves |= move
            elif any(line.result_package_id.name == package.name for line in move.move_line_ids):
                moves |= move
        return moves

    def booking_payload(self, picking, package, courier_code=False, shipping_charge=0.0, sequence=1):
        order_name = picking.name
        customer = picking.partner_id
        invoice_partner = customer.child_ids.filtered(lambda partner: partner.type == "invoice")[:1] or customer
        if picking.sale_id:
            invoice_partner = picking.sale_id.partner_invoice_id
            order_name = "%s-%s" % (order_name, picking.sale_id.name)

        warehouse_partner = picking.picking_type_id.warehouse_id.partner_id or picking.company_id.partner_id
        pickup_name = re.sub(r"[^a-zA-Z0-9\s]+", "", warehouse_partner.name or "")[:36] or "Warehouse"
        dimensions = package.dimension
        line_values = list(self.compose_item_rows(package, picking).values())
        discount_lines = picking.sale_id.order_line.filtered(lambda line: line._is_discount_line())
        order_date = picking.sale_id.date_order or picking.scheduled_date or fields.Datetime.now()
        if isinstance(order_date, datetime):
            order_date = order_date.date()

        return {
            "order_id": order_name,
            "channel_id": self.carrier.sr_integration_channel_id.external_channel_id,
            "order_date": order_date.strftime("%Y-%m-%d"),
            "request_pickup": self.carrier.sr_integration_request_pickup,
            "generate_manifest": self.carrier.sr_integration_generate_manifest,
            "print_label": True,
            "weight": picking.shipping_weight if picking and picking.shipping_weight > 0 else self.carrier._sr_integration_weight_kg(package.weight),
            "height": dimensions.get("height"),
            "breadth": dimensions.get("width"),
            "length": dimensions.get("length"),
            "ewaybill_no": picking.sr_integration_eway_bill,
            "courier_id": courier_code,
            "order_items": line_values,
            "sub_total": sum(line["selling_price"] * line["units"] for line in line_values),
            "total_discount": abs(sum(discount_lines.mapped("price_total"))),
            "shipping_charges": shipping_charge,
            "payment_method": "COD" if self.carrier.allow_cash_on_delivery else "Prepaid",
            "company_name": invoice_partner.commercial_partner_id.name,
            "billing_customer_name": invoice_partner.name,
            "billing_address": invoice_partner.street,
            "billing_address_2": invoice_partner.street2 or "",
            "billing_pincode": invoice_partner.zip,
            "billing_city": invoice_partner.city or "",
            "billing_country": invoice_partner.country_id.name,
            "billing_state": invoice_partner.state_id.name or "",
            "billing_email": invoice_partner.email,
            "billing_phone": self.phone_digits(invoice_partner),
            "billing_last_name": "",
            "shipping_is_billing": invoice_partner == customer,
            "shipping_customer_name": customer.name,
            "shipping_address": customer.street or "",
            "shipping_address_2": customer.street2 or "",
            "shipping_pincode": customer.zip,
            "shipping_city": customer.city or "",
            "shipping_country": customer.country_id.name,
            "shipping_state": customer.state_id.name or "",
            "shipping_email": customer.email,
            "shipping_phone": self.phone_digits(customer),
            "shipping_last_name": "",
            "pickup_location": pickup_name,
            "vendor_details": {
                "pickup_location": pickup_name,
                "name": pickup_name,
                "phone": self.phone_digits(warehouse_partner),
                "email": warehouse_partner.email,
                "pin_code": warehouse_partner.zip,
                "city": warehouse_partner.city or "",
                "country": warehouse_partner.country_id.name,
                "state": warehouse_partner.state_id.name or "",
                "address_2": warehouse_partner.street2 or "",
                "address": warehouse_partner.street,
            },
        }

    def booking_payloads(self, picking):
        if not self.carrier.sr_integration_channel_id:
            action = self.carrier.env.ref("delivery.action_delivery_carrier_form")
            raise RedirectWarning(
                _("Choose a Shiprocket Integration channel on the delivery method."),
                action.id,
                _("Open Delivery Method"),
            )

        warehouse_partner = picking.picking_type_id.warehouse_id.partner_id or picking.company_id.partner_id
        default_package = self.carrier.sr_integration_package_type_id
        packages = self.carrier._get_packages_from_picking(picking, default_package)
        carrier_lines = picking.sale_id.order_line.filtered(lambda line: line.product_id == self.carrier.product_id)
        shipping_charge = sum(carrier_lines.mapped("price_unit"))

        parcels = {}
        for sequence, package in enumerate(packages, start=1):
            rate = self.build_quote(picking.partner_id, warehouse_partner, picking=picking, package=package)
            if rate.get("error_found"):
                raise ValidationError(rate["error_found"])
            parcels[package] = self.booking_payload(
                picking,
                package,
                courier_code=rate.get("courier_code"),
                shipping_charge=shipping_charge,
                sequence=sequence,
            )
        return parcels

    def submit_bookings(self, picking):
        products = picking.move_line_ids.product_id
        self.validate_shipping_inputs(
            picking.partner_id,
            picking.picking_type_id.warehouse_id.partner_id or picking.company_id.partner_id,
            products.filtered(lambda product: product.type == "consu"),
        )

        result = {
            "packages": defaultdict(lambda: {"response": {}, "details": {}}),
            "order_ids": [],
            "tracking_numbers": [],
            "exact_price": 0.0,
        }
        for delivery_package, parcel in self.booking_payloads(picking).items():
            response = self.call_api("external/shipments/create/forward-shipment", "POST", parcel)
            if response.get("errors"):
                picking.message_post(body=self.error_text(response))
                continue

            payload = response.get("payload")
            if not payload:
                picking.message_post(body=_("Tracking number was not assigned: %s") % (self.error_text(response)))
                continue

            result["packages"][delivery_package]["response"] = payload
            duplicate_order = (
                payload.get("shipment_id")
                and payload.get("error_message")
                and "Oops! Cannot reassign courier" in payload["error_message"]
            )
            if duplicate_order:
                payload.pop("error_message")
                payload["warning_message"] = _(
                    "Shiprocket already has this order, so Odoo attached the existing remote label."
                )
                payload["label_url"] = self.label_url_for(payload["shipment_id"]).get("label_url")

            if payload.get("shipment_id") and not payload.get("error_message") and not payload.get("awb_assign_error"):
                result["tracking_numbers"].append(payload.get("awb_code"))
                details = self.call_api("external/shipments/%s" % payload["shipment_id"])
                order_id = (details.get("data") or {}).get("order_id")
                if order_id:
                    result["order_ids"].append(str(order_id))
                result["packages"][delivery_package]["details"] = details
                freight_charge = ((details.get("data") or {}).get("charges") or {}).get("freight_charges") or 0.0
                result["exact_price"] += float(freight_charge)
            else:
                picking.message_post(body=_("Tracking number was not assigned: %s") % (self.error_text(response)))
        return result

    def label_url_for(self, shipment_id):
        response = self.call_api(
            "external/courier/generate/label",
            "POST",
            {"shipment_id": [shipment_id]},
        )
        if response and response.get("label_url"):
            return response
        raise ValidationError(self.error_text(response))

    def void_remote_documents(self, remote_refs, pickup_requested):
        responses = {}
        for remote_ref in remote_refs:
            if pickup_requested:
                endpoint = "external/orders/cancel"
                payload = {"ids": [remote_ref]}
            else:
                endpoint = "external/orders/cancel/shipment/awbs"
                payload = {"awbs": [remote_ref]}
            responses[remote_ref] = self.call_api(endpoint, "POST", payload)
        return responses

    def validate_shipping_inputs(self, recipient, warehouse_partner, products):
        missing = {"Customer": [], "Warehouse": []}
        self._collect_partner_gaps(missing["Customer"], recipient)
        self._collect_partner_gaps(missing["Warehouse"], warehouse_partner)

        for product in products:
            product_messages = []
            if not product.weight:
                product_messages.append(_("Set a product weight."))
            if not product.default_code:
                product_messages.append(_("Set an internal reference/SKU."))
            if product_messages:
                missing[product.display_name] = product_messages

        message = "".join(
            "%s\n- %s\n" % (section, "\n- ".join(values))
            for section, values in missing.items()
            if values
        )
        if message:
            raise ValidationError(message)
        return True

    def _collect_partner_gaps(self, target, partner):
        if not partner.street:
            target.append(_("Add a street address."))
        if not partner.zip:
            target.append(_("Add the postal code."))
        if not partner.country_id:
            target.append(_("Select a country."))
        if not partner.email:
            target.append(_("Add an email address."))
        if not (partner.phone or partner.mobile):
            target.append(_("Add a phone or mobile number."))

    def phone_digits(self, partner):
        return "".join(re.findall(r"\d+", partner.phone or partner.mobile or ""))
