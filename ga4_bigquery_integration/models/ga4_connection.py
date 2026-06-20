# -*- coding: utf-8 -*-
import json
import re
from datetime import date, datetime, time, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class GA4Connection(models.Model):
    _name = "ga4.connection"
    _description = "GA4 Connection"
    _order = "name"

    name = fields.Char(required=True, default="GA4 Connection")
    active = fields.Boolean(default=True)
    property_id = fields.Char(string="GA4 Property ID", required=True)
    service_account_json = fields.Text(required=True)
    bigquery_project_id = fields.Char()
    bigquery_dataset_id = fields.Char()
    bigquery_table_prefix = fields.Char(default="events_")
    bigquery_batch_limit = fields.Integer(
        default=0,
        help="0 means no row limit. Set a value only when you want to restrict each BigQuery sync.",
    )
    sync_start_date = fields.Date(default=lambda self: fields.Date.today() - timedelta(days=30))
    last_report_sync_date = fields.Date(readonly=True)
    last_bigquery_sync_date = fields.Date(readonly=True)
    report_count = fields.Integer(compute="_compute_counts")
    raw_event_count = fields.Integer(compute="_compute_counts")
    sync_log_count = fields.Integer(compute="_compute_counts")

    @api.depends()
    def _compute_counts(self):
        Report = self.env["ga4.report"]
        Event = self.env["ga4.raw.event"]
        Log = self.env["ga4.sync.log"]
        for record in self:
            record.report_count = Report.search_count([("connection_id", "=", record.id)])
            record.raw_event_count = Event.search_count([("connection_id", "=", record.id)])
            record.sync_log_count = Log.search_count([("connection_id", "=", record.id)])

    def _service_account_info(self):
        self.ensure_one()
        try:
            return json.loads(self.service_account_json)
        except Exception as error:
            raise UserError(_("Invalid service account JSON: %s") % error) from error

    def _credentials(self, scopes):
        try:
            from google.oauth2 import service_account
        except ImportError as error:
            raise UserError(_("Missing python dependency: google-auth")) from error
        return service_account.Credentials.from_service_account_info(
            self._service_account_info(),
            scopes=scopes,
        )

    def _ga_client(self):
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
        except ImportError as error:
            raise UserError(_("Missing python dependency: google-analytics-data")) from error
        return BetaAnalyticsDataClient(
            credentials=self._credentials(["https://www.googleapis.com/auth/analytics.readonly"])
        )

    def _bigquery_client(self):
        if not self.bigquery_project_id or not self.bigquery_dataset_id:
            raise UserError(_("BigQuery Project ID and Dataset ID are required."))
        try:
            from google.cloud import bigquery
        except ImportError as error:
            raise UserError(_("Missing python dependency: google-cloud-bigquery")) from error
        return bigquery.Client(
            project=self.bigquery_project_id,
            credentials=self._credentials(["https://www.googleapis.com/auth/cloud-platform"]),
        )

    def _report_definitions(self):
        return [
            {
                "type": "overview",
                "dimensions": ["date"],
                "metrics": ["totalUsers", "newUsers", "sessions", "screenPageViews", "eventCount", "keyEvents", "purchaseRevenue"],
            },
            {
                "type": "source_medium",
                "dimensions": ["date", "sessionSource", "sessionMedium", "sessionCampaignName"],
                "metrics": ["totalUsers", "sessions", "screenPageViews", "eventCount", "keyEvents"],
            },
            {
                "type": "page",
                "dimensions": ["date", "pagePath", "pageTitle"],
                "metrics": ["totalUsers", "sessions", "screenPageViews", "eventCount"],
            },
            {
                "type": "event",
                "dimensions": ["date", "eventName"],
                "metrics": ["totalUsers", "eventCount", "keyEvents", "eventValue", "eventCountPerUser"],
            },
            {
                "type": "event_page",
                "dimensions": ["date", "eventName", "pagePath", "pageTitle", "pageLocation"],
                "metrics": ["totalUsers", "sessions", "eventCount", "keyEvents", "eventValue"],
            },
            {
                "type": "event_source",
                "dimensions": ["date", "eventName", "sessionSource", "sessionMedium", "sessionCampaignName"],
                "metrics": ["totalUsers", "sessions", "eventCount", "keyEvents", "eventValue"],
            },
            {
                "type": "event_geo_device",
                "dimensions": ["date", "eventName", "country", "city", "deviceCategory", "operatingSystem", "browser", "platform", "streamId"],
                "metrics": ["totalUsers", "sessions", "eventCount", "keyEvents", "eventValue"],
            },
            {
                "type": "country_city",
                "dimensions": ["date", "country", "city"],
                "metrics": ["totalUsers", "sessions", "screenPageViews", "eventCount"],
            },
            {
                "type": "device",
                "dimensions": ["date", "deviceCategory", "operatingSystem", "browser"],
                "metrics": ["totalUsers", "sessions", "screenPageViews", "eventCount"],
            },
        ]

    def action_sync_all(self):
        for record in self:
            record._sync_reports(trigger_type="manual")
            if record._is_bigquery_configured():
                record._sync_bigquery_events(trigger_type="manual")
        return True

    def action_sync_reports(self):
        for record in self:
            record._sync_reports(trigger_type="manual")
        return True

    def action_sync_bigquery_events(self):
        for record in self:
            record._sync_bigquery_events(trigger_type="manual")
        return True

    @api.model
    def cron_sync_ga4(self):
        for connection in self.search([("active", "=", True)]):
            connection._sync_reports(trigger_type="cron")
            if connection._is_bigquery_configured():
                connection._sync_bigquery_events(trigger_type="cron")

    def _is_bigquery_configured(self):
        self.ensure_one()
        return bool(self.bigquery_project_id and self.bigquery_dataset_id)

    def _sync_reports(self, trigger_type="manual", date_from=None, date_to=None):
        self.ensure_one()
        date_from = date_from or self.last_report_sync_date or self.sync_start_date
        date_to = date_to or fields.Date.today()
        log = self._create_log("report", trigger_type, date_from, date_to)
        try:
            count = self._fetch_reports(date_from, date_to)
            self.last_report_sync_date = date_to
            log.write({"status": "success", "end_datetime": fields.Datetime.now(), "records_fetched": count})
        except Exception as error:
            log.write({"status": "failed", "end_datetime": fields.Datetime.now(), "error_message": str(error)})
            raise

    def _fetch_reports(self, date_from, date_to):
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

        client = self._ga_client()
        Report = self.env["ga4.report"].sudo()
        total_count = 0
        for definition in self._report_definitions():
            Report.search(
                [
                    ("connection_id", "=", self.id),
                    ("report_type", "=", definition["type"]),
                    ("report_date", ">=", date_from),
                    ("report_date", "<=", date_to),
                ]
            ).unlink()
            offset = 0
            while True:
                request = RunReportRequest(
                    property=f"properties/{self.property_id}",
                    dimensions=[Dimension(name=name) for name in definition["dimensions"]],
                    metrics=[Metric(name=name) for name in definition["metrics"]],
                    date_ranges=[DateRange(start_date=str(date_from), end_date=str(date_to))],
                    limit=10000,
                    offset=offset,
                )
                response = client.run_report(request)
                if not response.rows:
                    break
                vals_list = [self._prepare_report_vals(definition, row) for row in response.rows]
                Report.create(vals_list)
                total_count += len(vals_list)
                offset += len(response.rows)
                if offset >= response.row_count:
                    break
        return total_count

    def _prepare_report_vals(self, definition, row):
        dimensions = {
            name: row.dimension_values[index].value
            for index, name in enumerate(definition["dimensions"])
        }
        metrics = {
            name: row.metric_values[index].value
            for index, name in enumerate(definition["metrics"])
        }
        metric_map = {
            "total_users": "totalUsers",
            "new_users": "newUsers",
            "sessions": "sessions",
            "screen_page_views": "screenPageViews",
            "event_count": "eventCount",
            "conversions": "keyEvents",
            "event_value": "eventValue",
            "event_count_per_user": "eventCountPerUser",
            "purchase_revenue": "purchaseRevenue",
        }
        report_date = datetime.strptime(dimensions["date"], "%Y%m%d").date()
        dimension_key = "|".join(
            dimensions.get(name, "") for name in definition["dimensions"] if name != "date"
        ) or definition["type"]
        vals = {
            "connection_id": self.id,
            "report_type": definition["type"],
            "report_date": report_date,
            "dimension_key": dimension_key,
            "source": dimensions.get("sessionSource"),
            "medium": dimensions.get("sessionMedium"),
            "campaign": dimensions.get("sessionCampaignName"),
            "page_path": dimensions.get("pagePath"),
            "page_location": dimensions.get("pageLocation"),
            "page_title": dimensions.get("pageTitle"),
            "event_name": dimensions.get("eventName"),
            "country": dimensions.get("country"),
            "city": dimensions.get("city"),
            "device_category": dimensions.get("deviceCategory"),
            "operating_system": dimensions.get("operatingSystem"),
            "browser": dimensions.get("browser"),
            "platform": dimensions.get("platform"),
            "stream_id": dimensions.get("streamId"),
            "dimensions_json": dimensions,
            "metrics_json": metrics,
        }
        for field_name, metric_name in metric_map.items():
            if metric_name in metrics:
                metric_value = float(metrics[metric_name] or 0)
                vals[field_name] = metric_value if field_name == "purchase_revenue" else int(metric_value)
        return vals

    def _sync_bigquery_events(self, trigger_type="manual", date_from=None, date_to=None):
        self.ensure_one()
        date_from = date_from or self.last_bigquery_sync_date or self.sync_start_date
        date_to = date_to or fields.Date.today()
        log = self._create_log("bigquery", trigger_type, date_from, date_to)
        try:
            count = self._fetch_bigquery_events(date_from, date_to)
            self.last_bigquery_sync_date = date_to
            log.write({"status": "success", "end_datetime": fields.Datetime.now(), "records_fetched": count})
        except Exception as error:
            log.write({"status": "failed", "end_datetime": fields.Datetime.now(), "error_message": str(error)})
            raise

    def _fetch_bigquery_events(self, date_from, date_to):
        client = self._bigquery_client()
        self._check_bigquery_identifier(self.bigquery_project_id, "BigQuery Project ID")
        self._check_bigquery_identifier(self.bigquery_dataset_id, "BigQuery Dataset ID")
        self._check_bigquery_identifier(self.bigquery_table_prefix, "BigQuery Table Prefix")
        table_pattern = f"`{self.bigquery_project_id}.{self.bigquery_dataset_id}.{self.bigquery_table_prefix}*`"
        limit_clause = "LIMIT @limit" if self.bigquery_batch_limit else ""
        sql = f"""
            SELECT
                TO_HEX(SHA256(TO_JSON_STRING(event_row))) AS odoo_unique_key,
                event_row.event_date,
                event_row.event_timestamp,
                event_row.event_name,
                event_row.user_pseudo_id,
                event_row.user_id,
                event_row.user_first_touch_timestamp,
                event_row.stream_id,
                event_row.platform,
                event_row.device.category AS device_category,
                event_row.device.operating_system AS operating_system,
                event_row.device.web_info.browser AS browser,
                event_row.device.language AS language,
                event_row.geo.country AS country,
                event_row.geo.city AS city,
                event_row.traffic_source.source AS source,
                event_row.traffic_source.medium AS medium,
                event_row.traffic_source.name AS campaign,
                event_row.ecommerce.transaction_id AS transaction_id,
                event_row.ecommerce.purchase_revenue AS purchase_revenue,
                event_row.ecommerce.total_item_quantity AS total_item_quantity,
                event_row.event_params,
                event_row.user_properties,
                event_row.ecommerce
            FROM {table_pattern}
            AS event_row
            WHERE _TABLE_SUFFIX BETWEEN @date_from AND @date_to
            {limit_clause}
        """
        job_config = self._bigquery_job_config(date_from, date_to)
        rows = client.query(sql, job_config=job_config).result()
        Event = self.env["ga4.raw.event"].sudo()
        count = 0
        for row in rows:
            vals = self._prepare_bigquery_event_vals(row)
            existing = Event.search([("connection_id", "=", self.id), ("unique_key", "=", vals["unique_key"])], limit=1)
            if existing:
                existing.write(vals)
            else:
                Event.create(vals)
            count += 1
        return count

    def _bigquery_job_config(self, date_from, date_to):
        from google.cloud import bigquery

        query_parameters = [
            bigquery.ScalarQueryParameter("date_from", "STRING", date_from.strftime("%Y%m%d")),
            bigquery.ScalarQueryParameter("date_to", "STRING", date_to.strftime("%Y%m%d")),
        ]
        if self.bigquery_batch_limit:
            query_parameters.append(
                bigquery.ScalarQueryParameter("limit", "INT64", self.bigquery_batch_limit)
            )
        return bigquery.QueryJobConfig(query_parameters=query_parameters)

    def _prepare_bigquery_event_vals(self, row):
        event_params = self._event_params_to_dict(row.event_params)
        event_dt = datetime.combine(date.today(), time.min)
        if row.event_timestamp:
            event_dt = datetime.utcfromtimestamp(row.event_timestamp / 1000000)
        unique_key = row.odoo_unique_key
        return {
            "connection_id": self.id,
            "unique_key": unique_key,
            "event_date": datetime.strptime(row.event_date, "%Y%m%d").date() if row.event_date else False,
            "event_datetime": event_dt,
            "event_name": row.event_name,
            "user_pseudo_id": row.user_pseudo_id,
            "user_id": row.user_id,
            "ga_session_id": str(event_params.get("ga_session_id") or ""),
            "ga_session_number": event_params.get("ga_session_number") or 0,
            "stream_id": row.stream_id,
            "platform": row.platform,
            "page_location": event_params.get("page_location"),
            "page_title": event_params.get("page_title"),
            "page_referrer": event_params.get("page_referrer"),
            "source": row.source,
            "medium": row.medium,
            "campaign": row.campaign,
            "device_category": row.device_category,
            "operating_system": row.operating_system,
            "browser": row.browser,
            "language": row.language,
            "country": row.country,
            "city": row.city,
            "transaction_id": row.transaction_id,
            "currency": event_params.get("currency"),
            "purchase_revenue": row.purchase_revenue or 0.0,
            "value": event_params.get("value") or 0.0,
            "engagement_time_msec": event_params.get("engagement_time_msec") or 0,
            "event_params_json": event_params,
            "user_properties_json": self._record_list_to_json(row.user_properties),
            "ecommerce_json": self._record_to_json(row.ecommerce),
            "raw_payload_json": {
                "event_date": row.event_date,
                "event_timestamp": row.event_timestamp,
                "event_name": row.event_name,
                "user_pseudo_id": row.user_pseudo_id,
                "user_id": row.user_id,
                "user_first_touch_timestamp": row.user_first_touch_timestamp,
                "stream_id": row.stream_id,
                "platform": row.platform,
                "device_category": row.device_category,
                "operating_system": row.operating_system,
                "browser": row.browser,
                "language": row.language,
                "country": row.country,
                "city": row.city,
                "source": row.source,
                "medium": row.medium,
                "campaign": row.campaign,
                "transaction_id": row.transaction_id,
                "purchase_revenue": row.purchase_revenue,
                "total_item_quantity": row.total_item_quantity,
            },
        }

    def _event_params_to_dict(self, params):
        result = {}
        for param in params or []:
            value = getattr(param, "value", None)
            if not value:
                continue
            for value_field in ("string_value", "int_value", "float_value", "double_value"):
                param_value = getattr(value, value_field, None)
                if param_value is not None:
                    result[param.key] = param_value
                    break
        return result

    def _record_list_to_json(self, records):
        return [self._record_to_json(record) for record in records or []]

    def _record_to_json(self, record):
        if not record:
            return {}
        if hasattr(record, "items"):
            return {
                key: self._record_to_json(value)
                for key, value in record.items()
                if not key.startswith("_")
            }
        if isinstance(record, (list, tuple)):
            return [self._record_to_json(value) for value in record]
        return record

    def _check_bigquery_identifier(self, value, label):
        if not value or not re.match(r"^[A-Za-z0-9_-]+$", value):
            raise UserError(_("%s contains unsupported characters.") % label)

    @api.model
    def get_dashboard_data(self, connection_id=False, period_days=30):
        period_days = int(period_days or 30)
        period_days = min(max(period_days, 7), 365)
        today = fields.Date.today()
        date_from = today - timedelta(days=period_days - 1)
        previous_from = date_from - timedelta(days=period_days)
        previous_to = date_from - timedelta(days=1)
        connection = self.browse(connection_id).exists() if connection_id else self.search([], limit=1)
        connections = self.search_read([], ["name", "property_id"], order="name")
        if not connection:
            return {
                "connections": connections,
                "connection_id": False,
                "period_days": period_days,
                "date_from": str(date_from),
                "date_to": str(today),
                "kpis": [],
                "trend": [],
                "top_sources": [],
                "top_pages": [],
                "top_events": [],
                "raw_summary": [],
                "latest_logs": [],
            }

        current_reports = self.env["ga4.report"].search(
            [
                ("connection_id", "=", connection.id),
                ("report_date", ">=", date_from),
                ("report_date", "<=", today),
            ]
        )
        previous_reports = self.env["ga4.report"].search(
            [
                ("connection_id", "=", connection.id),
                ("report_date", ">=", previous_from),
                ("report_date", "<=", previous_to),
            ]
        )
        current_overview = current_reports.filtered(lambda report: report.report_type == "overview")
        previous_overview = previous_reports.filtered(lambda report: report.report_type == "overview")
        raw_domain = [
            ("connection_id", "=", connection.id),
            ("event_date", ">=", date_from),
            ("event_date", "<=", today),
        ]
        raw_event_count = self.env["ga4.raw.event"].search_count(raw_domain)
        previous_raw_event_count = self.env["ga4.raw.event"].search_count(
            [
                ("connection_id", "=", connection.id),
                ("event_date", ">=", previous_from),
                ("event_date", "<=", previous_to),
            ]
        )

        return {
            "connections": connections,
            "connection_id": connection.id,
            "connection_name": connection.display_name,
            "property_id": connection.property_id,
            "period_days": period_days,
            "date_from": str(date_from),
            "date_to": str(today),
            "kpis": [
                self._dashboard_kpi("Users", self._sum_records(current_overview, "total_users"), self._sum_records(previous_overview, "total_users")),
                self._dashboard_kpi("Sessions", self._sum_records(current_overview, "sessions"), self._sum_records(previous_overview, "sessions")),
                self._dashboard_kpi("Page Views", self._sum_records(current_overview, "screen_page_views"), self._sum_records(previous_overview, "screen_page_views")),
                self._dashboard_kpi("Key Events", self._sum_records(current_overview, "conversions"), self._sum_records(previous_overview, "conversions")),
                self._dashboard_kpi("Raw Events", raw_event_count, previous_raw_event_count),
                self._dashboard_kpi("Revenue", self._sum_records(current_overview, "purchase_revenue"), self._sum_records(previous_overview, "purchase_revenue"), money=True),
            ],
            "trend": self._dashboard_trend(current_overview),
            "top_sources": self._dashboard_report_table(
                current_reports.filtered(lambda report: report.report_type == "source_medium"),
                ["source", "medium", "campaign"],
                "sessions",
                label_join=" / ",
            ),
            "top_pages": self._dashboard_report_table(
                current_reports.filtered(lambda report: report.report_type == "page"),
                ["page_title", "page_path"],
                "screen_page_views",
            ),
            "top_events": self._dashboard_report_table(
                current_reports.filtered(lambda report: report.report_type == "event"),
                ["event_name"],
                "event_count",
            ),
            "raw_summary": self._dashboard_raw_events(raw_domain),
            "latest_logs": self._dashboard_latest_logs(connection),
        }

    def _sum_records(self, records, field_name):
        return sum(records.mapped(field_name))

    def _dashboard_kpi(self, label, value, previous, money=False):
        value = value or 0
        previous = previous or 0
        change = 100.0 if value and not previous else ((value - previous) / previous * 100.0 if previous else 0.0)
        return {
            "label": label,
            "value": self._format_dashboard_number(value, money=money),
            "raw_value": value,
            "change": round(change, 1),
            "direction": "up" if change >= 0 else "down",
        }

    def _format_dashboard_number(self, value, money=False):
        if money:
            return "%.2f" % value
        if value >= 1000000:
            return "%.1fM" % (value / 1000000)
        if value >= 1000:
            return "%.1fK" % (value / 1000)
        return str(int(value))

    def _dashboard_trend(self, overview_reports):
        daily = {}
        for report in overview_reports:
            key = str(report.report_date)
            daily.setdefault(key, {"date": key, "users": 0, "sessions": 0, "views": 0})
            daily[key]["users"] += report.total_users
            daily[key]["sessions"] += report.sessions
            daily[key]["views"] += report.screen_page_views
        values = [daily[key] for key in sorted(daily)]
        max_views = max([item["views"] for item in values] or [1])
        for item in values:
            item["height"] = max(8, round((item["views"] / max_views) * 100))
        return values

    def _dashboard_report_table(self, reports, label_fields, metric_field, label_join=" | "):
        grouped = {}
        for report in reports:
            label_parts = [getattr(report, field_name) for field_name in label_fields if getattr(report, field_name)]
            label = label_join.join(label_parts) or report.dimension_key or _("Not Set")
            grouped.setdefault(label, 0)
            grouped[label] += getattr(report, metric_field)
        rows = [{"label": key, "value": value} for key, value in grouped.items()]
        rows = sorted(rows, key=lambda row: row["value"], reverse=True)[:8]
        max_value = max([row["value"] for row in rows] or [1])
        for row in rows:
            row["bar"] = round((row["value"] / max_value) * 100)
            row["display_value"] = self._format_dashboard_number(row["value"])
        return rows

    def _dashboard_raw_events(self, raw_domain):
        rows = self.env["ga4.raw.event"].read_group(
            raw_domain,
            ["event_name"],
            ["event_name"],
            orderby="event_name",
            limit=100,
        )
        rows = sorted(
            [
                {"label": row["event_name"] or _("Not Set"), "value": row.get("__count", 0)}
                for row in rows
            ],
            key=lambda row: row["value"],
            reverse=True,
        )[:8]
        max_value = max([row["value"] for row in rows] or [1])
        for row in rows:
            row["bar"] = round((row["value"] / max_value) * 100)
            row["display_value"] = self._format_dashboard_number(row["value"])
        return rows

    def _dashboard_latest_logs(self, connection):
        logs = self.env["ga4.sync.log"].search([("connection_id", "=", connection.id)], limit=5)
        return [
            {
                "name": log.name,
                "sync_type": dict(log._fields["sync_type"].selection).get(log.sync_type),
                "status": log.status,
                "records_fetched": log.records_fetched,
                "start_datetime": fields.Datetime.to_string(log.start_datetime) if log.start_datetime else "",
            }
            for log in logs
        ]

    def _create_log(self, sync_type, trigger_type, date_from, date_to):
        return self.env["ga4.sync.log"].sudo().create(
            {
                "name": "%s - %s" % (self.display_name, fields.Datetime.now()),
                "connection_id": self.id,
                "sync_type": sync_type,
                "trigger_type": trigger_type,
                "date_from": date_from,
                "date_to": date_to,
            }
        )

    def action_view_reports(self):
        self.ensure_one()
        return self._action_view_related("ga4.report", "GA4 Reports", "list,graph,pivot,form")

    def action_view_raw_events(self):
        self.ensure_one()
        return self._action_view_related("ga4.raw.event", "GA4 Raw Events", "list,graph,pivot,form")

    def action_view_sync_logs(self):
        self.ensure_one()
        return self._action_view_related("ga4.sync.log", "GA4 Sync Logs", "list,form")

    def _action_view_related(self, model, name, view_mode):
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "view_mode": view_mode,
            "domain": [("connection_id", "=", self.id)],
            "context": {"default_connection_id": self.id},
        }
