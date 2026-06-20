# -*- coding: utf-8 -*-
{
    "name": "GA4 BigQuery Integration",
    "summary": "Sync Google Analytics 4 reports and raw BigQuery events into Odoo",
    "version": "19.0.1.0.0",
    "category": "Marketing/Analytics",
    "author": "Gadgetflix",
    "website": "https://www.candidroot.com",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/ga4_connection_views.xml",
        "views/ga4_report_views.xml",
        "views/ga4_raw_event_views.xml",
        "views/ga4_sync_log_views.xml",
        "views/ga4_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ga4_bigquery_integration/static/src/js/ga4_dashboard.js",
            "ga4_bigquery_integration/static/src/xml/ga4_dashboard.xml",
            "ga4_bigquery_integration/static/src/scss/ga4_dashboard.scss",
        ],
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
