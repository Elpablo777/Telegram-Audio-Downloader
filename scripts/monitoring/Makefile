# Monitoring System Commands
# ===========================

.PHONY: monitor-check monitor-start monitor-dashboard monitor-report monitor-setup

# Run single health check
monitor-check:
	@echo "🔍 Running system health check..."
	python scripts/monitoring/continuous_monitor.py check

# Start continuous monitoring
monitor-start:
	@echo "🔄 Starting continuous monitoring..."
	python scripts/monitoring/continuous_monitor.py start

# Start monitoring dashboard
monitor-dashboard:
	@echo "🏥 Starting monitoring dashboard..."
	@echo "📊 Dashboard will be available at: http://localhost:8080"
	python scripts/monitoring/dashboard.py

# Generate health report
monitor-report:
	@echo "📊 Generating health report..."
	python scripts/monitoring/continuous_monitor.py report

# Setup monitoring dependencies
monitor-setup:
	@echo "📦 Installing monitoring dependencies..."
	pip install psutil schedule plotly flask radon bandit safety

# Quick monitoring status
monitor-status:
	@echo "🏥 System Monitoring Status"
	@echo "=========================="
	@if [ -f "data/metrics/latest_health.json" ]; then \
		python -c "import json; \
		with open('data/metrics/latest_health.json') as f: \
			data = json.load(f); \
			print(f'Health Status: {data[\"overall_health\"]}'); \
			print(f'Health Score: {data[\"score\"]:.1f}/100'); \
			print(f'Last Check: {data[\"timestamp\"]}'); \
			if data['alerts']: \
				print(f'Active Alerts: {len(data[\"alerts\"])}'); \
				for alert in data['alerts'][:3]: \
					print(f'  - {alert}'); \
		"; \
	else \
		echo "No health data available. Run 'make monitor-check' first."; \
	fi

# Clean monitoring data
monitor-clean:
	@echo "🧹 Cleaning monitoring data..."
	rm -rf data/metrics/ data/logs/ data/alerts/
	@echo "✅ Monitoring data cleaned"

# Monitor with Docker
monitor-docker:
	@echo "🐳 Starting monitoring in Docker..."
	docker-compose -f docker/docker-compose.monitoring.yml up -d

# Stop Docker monitoring
monitor-docker-stop:
	@echo "🛑 Stopping Docker monitoring..."
	docker-compose -f docker/docker-compose.monitoring.yml down

# All monitoring commands help
monitor-help:
	@echo "🏥 Monitoring System Commands"
	@echo "============================="
	@echo ""
	@echo "Basic Commands:"
	@echo "  make monitor-check     - Run single health check"
	@echo "  make monitor-start     - Start continuous monitoring"
	@echo "  make monitor-dashboard - Start web dashboard"
	@echo "  make monitor-status    - Show current status"
	@echo "  make monitor-report    - Generate health report"
	@echo ""
	@echo "Setup & Maintenance:"
	@echo "  make monitor-setup     - Install dependencies"
	@echo "  make monitor-clean     - Clean monitoring data"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make monitor-docker       - Start monitoring in Docker"
	@echo "  make monitor-docker-stop  - Stop Docker monitoring"
	@echo ""
	@echo "Dashboard URLs:"
	@echo "  Health Dashboard: http://localhost:8080"
	@echo "  API Health:       http://localhost:8080/api/health"
	@echo "  API History:      http://localhost:8080/api/history"