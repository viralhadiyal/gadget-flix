# -*- coding: utf-8 -*-
from odoo import fields, models


class GA4Report(models.Model):
    _name = "ga4.report"
    _description = "GA4 Report Data"
    _order = "report_date desc, report_type, id desc"

    connection_id = fields.Many2one("ga4.connection", required=True, ondelete="cascade")
    report_type = fields.Selection(
        [
            ("overview", "Overview"),
            ("source_medium", "Source / Medium"),
            ("page", "Page"),
            ("event", "Event"),
            ("event_page", "Event by Page"),
            ("event_source", "Event by Source"),
            ("event_geo_device", "Event by Geo / Device"),
            ("country_city", "Country / City"),
            ("device", "Device"),
        ],
        required=True,
        index=True,
    )
    report_date = fields.Date(required=True, index=True)
    dimension_key = fields.Char(index=True)
    source = fields.Char(index=True)
    medium = fields.Char(index=True)
    campaign = fields.Char(index=True)
    page_path = fields.Char(index=True)
    page_location = fields.Char(index=True)
    page_title = fields.Char()
    event_name = fields.Char(index=True)
    country = fields.Char(index=True)
    city = fields.Char(index=True)
    device_category = fields.Char(index=True)
    operating_system = fields.Char(index=True)
    browser = fields.Char(index=True)
    platform = fields.Char(index=True)
    stream_id = fields.Char(index=True)
    dimensions_json = fields.Json()
    metrics_json = fields.Json()
    total_users = fields.Integer()
    new_users = fields.Integer()
    sessions = fields.Integer()
    screen_page_views = fields.Integer(string="Views")
    event_count = fields.Integer()
    conversions = fields.Integer(string="Key Events")
    event_value = fields.Float()
    event_count_per_user = fields.Float()
    purchase_revenue = fields.Float()
