# -*- coding: utf-8 -*-
from odoo import fields, models


class GA4SyncLog(models.Model):
    _name = "ga4.sync.log"
    _description = "GA4 Sync Log"
    _order = "start_datetime desc, id desc"

    name = fields.Char(required=True)
    connection_id = fields.Many2one("ga4.connection", required=True, ondelete="cascade")
    sync_type = fields.Selection(
        [
            ("report", "GA4 Report"),
            ("bigquery", "BigQuery Raw Events"),
            ("all", "Full Sync"),
        ],
        required=True,
    )
    trigger_type = fields.Selection(
        [("manual", "Manual"), ("cron", "Scheduled")],
        default="manual",
        required=True,
    )
    status = fields.Selection(
        [("running", "Running"), ("success", "Success"), ("failed", "Failed")],
        default="running",
        required=True,
    )
    date_from = fields.Date()
    date_to = fields.Date()
    start_datetime = fields.Datetime(default=fields.Datetime.now, required=True)
    end_datetime = fields.Datetime()
    records_fetched = fields.Integer(default=0)
    error_message = fields.Text()
