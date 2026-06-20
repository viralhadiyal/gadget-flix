# -*- coding: utf-8 -*-
from odoo import fields, models


class GA4RawEvent(models.Model):
    _name = "ga4.raw.event"
    _description = "GA4 Raw Event"
    _order = "event_datetime desc, id desc"

    connection_id = fields.Many2one("ga4.connection", required=True, ondelete="cascade")
    unique_key = fields.Char(required=True, index=True)
    event_date = fields.Date(index=True)
    event_datetime = fields.Datetime(index=True)
    event_name = fields.Char(index=True)
    user_pseudo_id = fields.Char(index=True)
    user_id = fields.Char(index=True)
    ga_session_id = fields.Char(index=True)
    ga_session_number = fields.Integer()
    stream_id = fields.Char()
    platform = fields.Char()
    page_location = fields.Char()
    page_title = fields.Char()
    page_referrer = fields.Char()
    source = fields.Char()
    medium = fields.Char()
    campaign = fields.Char()
    device_category = fields.Char()
    operating_system = fields.Char()
    browser = fields.Char()
    language = fields.Char()
    country = fields.Char()
    city = fields.Char()
    transaction_id = fields.Char(index=True)
    currency = fields.Char()
    purchase_revenue = fields.Float()
    value = fields.Float()
    engagement_time_msec = fields.Integer()
    event_params_json = fields.Json()
    user_properties_json = fields.Json()
    ecommerce_json = fields.Json()
    raw_payload_json = fields.Json()

    _sql_constraints = [
        (
            "unique_connection_event",
            "unique(connection_id, unique_key)",
            "Raw GA4 event already exists for this connection.",
        )
    ]
