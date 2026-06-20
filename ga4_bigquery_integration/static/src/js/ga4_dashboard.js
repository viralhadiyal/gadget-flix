/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { Component, onWillStart, useState } from "@odoo/owl";

class GA4Dashboard extends Component {
    static template = "ga4_bigquery_integration.Dashboard";
    static components = { Layout };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            periodDays: 30,
            connectionId: false,
            data: {},
        });
        onWillStart(async () => this.loadDashboard());
    }

    get display() {
        return { controlPanel: {} };
    }

    async loadDashboard() {
        this.state.loading = true;
        this.state.data = await this.orm.call("ga4.connection", "get_dashboard_data", [], {
            connection_id: this.state.connectionId,
            period_days: this.state.periodDays,
        });
        this.state.connectionId = this.state.data.connection_id;
        this.state.loading = false;
    }

    async setPeriod(days) {
        this.state.periodDays = days;
        await this.loadDashboard();
    }

    async setConnection(ev) {
        this.state.connectionId = Number(ev.target.value) || false;
        await this.loadDashboard();
    }

    openReports() {
        this.action.doAction("ga4_bigquery_integration.action_ga4_report");
    }

    openRawEvents() {
        this.action.doAction("ga4_bigquery_integration.action_ga4_raw_event");
    }

    openSyncLogs() {
        this.action.doAction("ga4_bigquery_integration.action_ga4_sync_log");
    }

    openConnections() {
        this.action.doAction("ga4_bigquery_integration.action_ga4_connection");
    }
}

registry.category("actions").add("ga4_bigquery_dashboard", GA4Dashboard);
