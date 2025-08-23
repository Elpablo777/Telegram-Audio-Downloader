#!/usr/bin/env python3
"""
Monitoring Dashboard - Telegram Audio Downloader
================================================

Web-based dashboard for continuous monitoring system.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import asdict

from flask import Flask, render_template_string, jsonify, request
import plotly.graph_objs as go
import plotly.utils

app = Flask(__name__)

class MonitoringDashboard:
    """Web dashboard for monitoring system."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.metrics_dir = self.project_root / "data" / "metrics"
        self.alerts_dir = self.project_root / "data" / "alerts"
    
    def get_latest_health(self) -> Optional[Dict]:
        """Get latest health status."""
        latest_file = self.metrics_dir / "latest_health.json"
        if latest_file.exists():
            with open(latest_file) as f:
                return json.load(f)
        return None
    
    def get_health_history(self, days: int = 7) -> List[Dict]:
        """Get health history for specified days."""
        history = []
        cutoff = datetime.now() - timedelta(days=days)
        
        for metrics_file in sorted(self.metrics_dir.glob("health_*.json")):
            try:
                # Extract date from filename
                date_str = metrics_file.stem.split('_')[1]  # health_YYYYMMDD_HHMMSS
                file_date = datetime.strptime(date_str, '%Y%m%d')
                
                if file_date >= cutoff:
                    with open(metrics_file) as f:
                        history.append(json.load(f))
            except Exception:
                continue
        
        return sorted(history, key=lambda x: x['timestamp'])
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts."""
        alerts = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        for alert_file in sorted(self.alerts_dir.glob("alert_*.json")):
            try:
                # Extract timestamp from filename
                timestamp_str = alert_file.stem.replace('alert_', '')
                file_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                if file_time >= cutoff:
                    with open(alert_file) as f:
                        alerts.append(json.load(f))
            except Exception:
                continue
        
        return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
    
    def create_health_score_chart(self, history: List[Dict]) -> str:
        """Create health score chart."""
        if not history:
            return "{}"
        
        timestamps = [h['timestamp'] for h in history]
        scores = [h['score'] for h in history]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=scores,
            mode='lines+markers',
            name='Health Score',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8)
        ))
        
        # Add threshold lines
        fig.add_hline(y=80, line_dash="dash", line_color="green", 
                     annotation_text="Good Threshold")
        fig.add_hline(y=60, line_dash="dash", line_color="orange", 
                     annotation_text="Warning Threshold")
        fig.add_hline(y=40, line_dash="dash", line_color="red", 
                     annotation_text="Critical Threshold")
        
        fig.update_layout(
            title="Health Score Trend",
            xaxis_title="Time",
            yaxis_title="Health Score",
            yaxis=dict(range=[0, 100]),
            height=400
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def create_metrics_chart(self, history: List[Dict]) -> str:
        """Create metrics comparison chart."""
        if not history:
            return "{}"
        
        timestamps = [h['timestamp'] for h in history]
        
        fig = go.Figure()
        
        # Add test coverage
        coverage = [h.get('quality_metrics', {}).get('test_coverage', 0) for h in history]
        fig.add_trace(go.Scatter(
            x=timestamps, y=coverage, name='Test Coverage', 
            line=dict(color='#A23B72')
        ))
        
        # Add lint score
        lint_scores = [h.get('quality_metrics', {}).get('lint_score', 0) for h in history]
        fig.add_trace(go.Scatter(
            x=timestamps, y=lint_scores, name='Code Quality',
            line=dict(color='#F18F01')
        ))
        
        # Add security score
        security_scores = [h.get('security_metrics', {}).get('bandit_score', 0) for h in history]
        fig.add_trace(go.Scatter(
            x=timestamps, y=security_scores, name='Security Score',
            line=dict(color='#C73E1D')
        ))
        
        fig.update_layout(
            title="Quality Metrics Trend",
            xaxis_title="Time",
            yaxis_title="Score (%)",
            yaxis=dict(range=[0, 100]),
            height=400
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

dashboard = MonitoringDashboard()

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏥 Monitoring Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f5f5f5; 
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;
            text-align: center;
        }
        .status-grid { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-bottom: 30px; 
        }
        .status-card { 
            background: white; padding: 25px; border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;
        }
        .status-healthy { border-left: 5px solid #28a745; }
        .status-warning { border-left: 5px solid #ffc107; }
        .status-critical { border-left: 5px solid #dc3545; }
        .chart-container { 
            background: white; padding: 20px; border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;
        }
        .alerts-section { 
            background: white; padding: 20px; border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .alert-item { 
            padding: 15px; margin: 10px 0; border-radius: 5px;
            background: #f8f9fa; border-left: 4px solid #dc3545;
        }
        .metric-value { font-size: 2em; font-weight: bold; margin: 10px 0; }
        .metric-label { color: #666; font-size: 0.9em; }
        .refresh-btn {
            background: #007bff; color: white; border: none; padding: 10px 20px;
            border-radius: 5px; cursor: pointer; margin: 10px;
        }
        .timestamp { color: #666; font-size: 0.8em; }
    </style>
    <script>
        function refreshData() {
            location.reload();
        }
        
        function autoRefresh() {
            setTimeout(refreshData, 300000); // 5 minutes
        }
        
        window.onload = autoRefresh;
    </script>
</head>
<body>
    <div class="header">
        <h1>🏥 System Health Monitoring Dashboard</h1>
        <p>Real-time monitoring for Telegram Audio Downloader</p>
        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
        <div class="timestamp">Last updated: {{ current_time }}</div>
    </div>

    {% if health_data %}
    <div class="status-grid">
        <div class="status-card status-{{ health_data.overall_health.lower() }}">
            <div class="metric-label">Overall Health</div>
            <div class="metric-value">{{ health_data.overall_health }}</div>
            <div class="metric-label">Score: {{ "%.1f"|format(health_data.score) }}/100</div>
        </div>
        
        <div class="status-card">
            <div class="metric-label">Test Coverage</div>
            <div class="metric-value">{{ "%.1f"|format(health_data.quality_metrics.get('test_coverage', 0)) }}%</div>
        </div>
        
        <div class="status-card">
            <div class="metric-label">Code Quality</div>
            <div class="metric-value">{{ "%.1f"|format(health_data.quality_metrics.get('lint_score', 0)) }}%</div>
        </div>
        
        <div class="status-card">
            <div class="metric-label">Security Score</div>
            <div class="metric-value">{{ "%.1f"|format(health_data.security_metrics.get('bandit_score', 0)) }}%</div>
        </div>
        
        <div class="status-card">
            <div class="metric-label">CPU Usage</div>
            <div class="metric-value">{{ "%.1f"|format(health_data.system_metrics.get('cpu_percent', 0)) }}%</div>
        </div>
        
        <div class="status-card">
            <div class="metric-label">Memory Usage</div>
            <div class="metric-value">{{ "%.1f"|format(health_data.system_metrics.get('memory_percent', 0)) }}%</div>
        </div>
    </div>

    <div class="chart-container">
        <div id="healthChart"></div>
    </div>

    <div class="chart-container">
        <div id="metricsChart"></div>
    </div>

    {% if health_data.alerts %}
    <div class="alerts-section">
        <h2>🚨 Active Alerts ({{ health_data.alerts|length }})</h2>
        {% for alert in health_data.alerts %}
        <div class="alert-item">
            <strong>⚠️ {{ alert }}</strong>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if recent_alerts %}
    <div class="alerts-section">
        <h2>📋 Recent Alert History</h2>
        {% for alert in recent_alerts[:5] %}
        <div class="alert-item">
            <div><strong>{{ alert.health_status }}</strong> - Score: {{ "%.1f"|format(alert.score) }}/100</div>
            <div class="timestamp">{{ alert.timestamp }}</div>
            {% if alert.alerts %}
            <ul>
                {% for item in alert.alerts %}
                <li>{{ item }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <script>
        // Render health score chart
        var healthChartData = {{ health_chart|safe }};
        if (healthChartData && Object.keys(healthChartData).length > 0) {
            Plotly.newPlot('healthChart', healthChartData.data, healthChartData.layout);
        }
        
        // Render metrics chart
        var metricsChartData = {{ metrics_chart|safe }};
        if (metricsChartData && Object.keys(metricsChartData).length > 0) {
            Plotly.newPlot('metricsChart', metricsChartData.data, metricsChartData.layout);
        }
    </script>

    {% else %}
    <div class="status-card">
        <h2>⚠️ No Health Data Available</h2>
        <p>Run a health check to see monitoring data.</p>
        <pre>python scripts/monitoring/continuous_monitor.py check</pre>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def dashboard_home():
    """Main dashboard page."""
    health_data = dashboard.get_latest_health()
    history = dashboard.get_health_history(days=7)
    recent_alerts = dashboard.get_recent_alerts(hours=24)
    
    health_chart = dashboard.create_health_score_chart(history)
    metrics_chart = dashboard.create_metrics_chart(history)
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                health_data=health_data,
                                recent_alerts=recent_alerts,
                                health_chart=health_chart,
                                metrics_chart=metrics_chart,
                                current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/health')
def api_health():
    """API endpoint for current health status."""
    health_data = dashboard.get_latest_health()
    return jsonify(health_data) if health_data else jsonify({"error": "No health data available"})

@app.route('/api/history')
def api_history():
    """API endpoint for health history."""
    days = request.args.get('days', 7, type=int)
    history = dashboard.get_health_history(days=days)
    return jsonify(history)

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for recent alerts."""
    hours = request.args.get('hours', 24, type=int)
    alerts = dashboard.get_recent_alerts(hours=hours)
    return jsonify(alerts)

if __name__ == '__main__':
    print("🏥 Starting Monitoring Dashboard...")
    print("📊 Dashboard URL: http://localhost:8080")
    print("🔗 API Health: http://localhost:8080/api/health")
    print("📈 API History: http://localhost:8080/api/history")
    print("🚨 API Alerts: http://localhost:8080/api/alerts")
    
    app.run(host='0.0.0.0', port=8080, debug=True)