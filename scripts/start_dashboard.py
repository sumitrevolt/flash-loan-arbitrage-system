"""
Dashboard for the Flash Loan Arbitrage System.
"""

import asyncio
import sys

# Fix Windows event loop policy for aiodns/aiohttp compatibility
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import os
import json
import logging
import datetime
from flask import Flask, render_template, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Dashboard")

# Create Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Render the dashboard index page."""
    return render_template('index.html')

@app.route('/api/status')
def status():
    """Get the system status."""
    try:
        # Load configuration
        config_path = os.path.join("config", "auto_executor_config.json")
        with open(config_path, "r") as f:
            config = json.load(f)

        # Get latest opportunities
        opportunities = []
        opportunities_dir = os.path.join("data", "opportunities")
        if os.path.exists(opportunities_dir):
            files = sorted([f for f in os.listdir(opportunities_dir) if f.endswith('.json')], reverse=True)
            if files:
                with open(os.path.join(opportunities_dir, files[0]), "r") as f:
                    opportunities = json.load(f)

        # Get latest executions
        executions = []
        executions_dir = os.path.join("data", "executions")
        if os.path.exists(executions_dir):
            files = sorted([f for f in os.listdir(executions_dir) if f.endswith('.json')], reverse=True)
            if files:
                for file in files[:5]:  # Get the 5 most recent executions
                    with open(os.path.join(executions_dir, file), "r") as f:
                        executions.append(json.load(f))

        # Get total profit
        total_profit = 0
        profits_dir = os.path.join("data", "profits")
        if os.path.exists(profits_dir):
            files = [f for f in os.listdir(profits_dir) if f.endswith('.json')]
            for file in files:
                with open(os.path.join(profits_dir, file), "r") as f:
                    for line in f:
                        try:
                            profit_entry = json.loads(line)
                            total_profit += profit_entry.get("profit_usd", 0)
                        except:
                            pass

        # Get current trade size
        trade_size = config.get("trade_size_usd", 100.0)

        return jsonify({
            "status": "running",
            "mode": config.get("real_execution", False) and "revenue" or "test",
            "debug": config.get("debug_mode", False),
            "profit_threshold": config.get("min_profit_threshold", 5.0),
            "scan_interval": config.get("scan_interval", 3),
            "trade_size": trade_size,
            "max_trade_size": config.get("max_trade_size_usd", 10000.0),
            "total_profit": total_profit,
            "opportunities_count": len(opportunities),
            "executions_count": len(executions),
            "last_updated": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        })

@app.route('/api/opportunities')
def get_opportunities():
    """Get the latest arbitrage opportunities."""
    try:
        # Get latest opportunities
        opportunities = []
        opportunities_dir = os.path.join("data", "opportunities")
        if os.path.exists(opportunities_dir):
            files = sorted([f for f in os.listdir(opportunities_dir) if f.endswith('.json')], reverse=True)
            if files:
                with open(os.path.join(opportunities_dir, files[0]), "r") as f:
                    opportunities = json.load(f)

        return jsonify(opportunities)
    except Exception as e:
        logger.error(f"Error getting opportunities: {e}")
        return jsonify([])

@app.route('/api/executions')
def get_executions():
    """Get the latest executions."""
    try:
        # Get latest executions
        executions = []
        executions_dir = os.path.join("data", "executions")
        if os.path.exists(executions_dir):
            files = sorted([f for f in os.listdir(executions_dir) if f.endswith('.json')], reverse=True)
            if files:
                for file in files[:10]:  # Get the 10 most recent executions
                    with open(os.path.join(executions_dir, file), "r") as f:
                        executions.append(json.load(f))

        return jsonify(executions)
    except Exception as e:
        logger.error(f"Error getting executions: {e}")
        return jsonify([])

@app.route('/api/profits')
def get_profits():
    """Get the profit history."""
    try:
        # Get profit history
        profits = []
        profits_dir = os.path.join("data", "profits")
        if os.path.exists(profits_dir):
            files = sorted([f for f in os.listdir(profits_dir) if f.endswith('.json')])
            for file in files:
                with open(os.path.join(profits_dir, file), "r") as f:
                    for line in f:
                        try:
                            profit_entry = json.loads(line)
                            profits.append(profit_entry)
                        except:
                            pass

        return jsonify(profits)
    except Exception as e:
        logger.error(f"Error getting profits: {e}")
        return jsonify([])

if __name__ == '__main__':
    # Create template directory if it doesn't exist
    os.makedirs(os.path.join("dashboard", "templates"), exist_ok=True)

    # Create index.html if it doesn't exist
    index_path = os.path.join("dashboard", "templates", "index.html")
    if not os.path.exists(index_path):
        with open(index_path, "w") as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Flash Loan Arbitrage System</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { padding-top: 20px; }
        .card { margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">Flash Loan Arbitrage System</h1>

        <div class="row">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">System Status</div>
                    <div class="card-body">
                        <p><strong>Status:</strong> <span id="status">Loading...</span></p>
                        <p><strong>Mode:</strong> <span id="mode">Loading...</span></p>
                        <p><strong>Debug:</strong> <span id="debug">Loading...</span></p>
                        <p><strong>Profit Threshold:</strong> $<span id="profit-threshold">Loading...</span></p>
                        <p><strong>Scan Interval:</strong> <span id="scan-interval">Loading...</span> seconds</p>
                        <p><strong>Trade Size:</strong> $<span id="trade-size">Loading...</span></p>
                        <p><strong>Max Trade Size:</strong> $<span id="max-trade-size">Loading...</span></p>
                        <p><strong>Last Updated:</strong> <span id="last-updated">Loading...</span></p>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">Profit Summary</div>
                    <div class="card-body">
                        <h2 class="text-center">$<span id="total-profit">0.00</span></h2>
                        <p class="text-center">Total Profit</p>
                        <canvas id="profit-chart"></canvas>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">Activity</div>
                    <div class="card-body">
                        <p><strong>Opportunities Found:</strong> <span id="opportunities-count">0</span></p>
                        <p><strong>Executions:</strong> <span id="executions-count">0</span></p>
                        <canvas id="activity-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Latest Opportunities</div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Token</th>
                                        <th>Buy DEX</th>
                                        <th>Sell DEX</th>
                                        <th>Profit</th>
                                        <th>%</th>
                                    </tr>
                                </thead>
                                <tbody id="opportunities-table">
                                    <tr>
                                        <td colspan="5" class="text-center">Loading...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Latest Executions</div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Token</th>
                                        <th>Route</th>
                                        <th>Profit</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody id="executions-table">
                                    <tr>
                                        <td colspan="5" class="text-center">Loading...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Format date
        function formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleString();
        }

        // Format currency
        function formatCurrency(amount) {
            return parseFloat(amount).toFixed(2);
        }

        // Update system status
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = data.status;
                    document.getElementById('mode').textContent = data.mode;
                    document.getElementById('debug').textContent = data.debug ? 'Enabled' : 'Disabled';
                    document.getElementById('profit-threshold').textContent = formatCurrency(data.profit_threshold);
                    document.getElementById('scan-interval').textContent = data.scan_interval;
                    document.getElementById('trade-size').textContent = formatCurrency(data.trade_size);
                    document.getElementById('max-trade-size').textContent = formatCurrency(data.max_trade_size);
                    document.getElementById('last-updated').textContent = formatDate(data.last_updated);
                    document.getElementById('total-profit').textContent = formatCurrency(data.total_profit);
                    document.getElementById('opportunities-count').textContent = data.opportunities_count;
                    document.getElementById('executions-count').textContent = data.executions_count;
                })
                .catch(error => console.error('Error fetching status:', error));
        }

        // Update opportunities table
        function updateOpportunities() {
            fetch('/api/opportunities')
                .then(response => response.json())
                .then(data => {
                    const tableBody = document.getElementById('opportunities-table');
                    tableBody.innerHTML = '';

                    if (data.length === 0) {
                        const row = document.createElement('tr');
                        row.innerHTML = '<td colspan="5" class="text-center">No opportunities found</td>';
                        tableBody.appendChild(row);
                        return;
                    }

                    data.slice(0, 5).forEach(opportunity => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${opportunity.token}</td>
                            <td>${opportunity.buy_dex}</td>
                            <td>${opportunity.sell_dex}</td>
                            <td>$${formatCurrency(opportunity.profit_usd)}</td>
                            <td>${formatCurrency(opportunity.profit_percentage)}%</td>
                        `;
                        tableBody.appendChild(row);
                    });
                })
                .catch(error => console.error('Error fetching opportunities:', error));
        }

        // Update executions table
        function updateExecutions() {
            fetch('/api/executions')
                .then(response => response.json())
                .then(data => {
                    const tableBody = document.getElementById('executions-table');
                    tableBody.innerHTML = '';

                    if (data.length === 0) {
                        const row = document.createElement('tr');
                        row.innerHTML = '<td colspan="5" class="text-center">No executions found</td>';
                        tableBody.appendChild(row);
                        return;
                    }

                    data.forEach(execution => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${formatDate(execution.timestamp)}</td>
                            <td>${execution.opportunity.token}</td>
                            <td>${execution.opportunity.buy_dex} → ${execution.opportunity.sell_dex}</td>
                            <td>$${formatCurrency(execution.profit_usd)}</td>
                            <td>${execution.status}</td>
                        `;
                        tableBody.appendChild(row);
                    });
                })
                .catch(error => console.error('Error fetching executions:', error));
        }

        // Update profit chart
        function updateProfitChart() {
            fetch('/api/profits')
                .then(response => response.json())
                .then data => {
                    if (data.length === 0) return;

                    // Group profits by day
                    const profitsByDay = {};
                    data.forEach(profit => {
                        const date = new Date(profit.timestamp).toLocaleDateString();
                        profitsByDay[date] = (profitsByDay[date] || 0) + profit.profit_usd;
                    });

                    // Create chart data
                    const labels = Object.keys(profitsByDay).slice(-7); // Last 7 days
                    const values = labels.map(date => profitsByDay[date]);

                    // Create chart
                    const ctx = document.getElementById('profit-chart').getContext('2d');
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Daily Profit (USD)',
                                data: values,
                                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                borderColor: 'rgba(75, 192, 192, 1)',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            }
                        }
                    });
                })
                .catch(error => console.error('Error fetching profits:', error));
        }

        // Update activity chart
        function updateActivityChart() {
            fetch('/api/executions')
                .then(response => response.json())
                .then(data => {
                    if (data.length === 0) return;

                    // Group executions by token
                    const executionsByToken = {};
                    data.forEach(execution => {
                        const token = execution.opportunity.token;
                        executionsByToken[token] = (executionsByToken[token] || 0) + 1;
                    });

                    // Create chart data
                    const labels = Object.keys(executionsByToken);
                    const values = labels.map(token => executionsByToken[token]);

                    // Create chart
                    const ctx = document.getElementById('activity-chart').getContext('2d');
                    new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Executions by Token',
                                data: values,
                                backgroundColor: [
                                    'rgba(255, 99, 132, 0.2)',
                                    'rgba(54, 162, 235, 0.2)',
                                    'rgba(255, 206, 86, 0.2)',
                                    'rgba(75, 192, 192, 0.2)',
                                    'rgba(153, 102, 255, 0.2)',
                                    'rgba(255, 159, 64, 0.2)'
                                ],
                                borderColor: [
                                    'rgba(255, 99, 132, 1)',
                                    'rgba(54, 162, 235, 1)',
                                    'rgba(255, 206, 86, 1)',
                                    'rgba(75, 192, 192, 1)',
                                    'rgba(153, 102, 255, 1)',
                                    'rgba(255, 159, 64, 1)'
                                ],
                                borderWidth: 1
                            }]
                        }
                    });
                })
                .catch(error => console.error('Error fetching executions for chart:', error));
        }

        // Update everything
        function updateAll() {
            updateStatus();
            updateOpportunities();
            updateExecutions();
            updateProfitChart();
            updateActivityChart();
        }

        // Initial update
        updateAll();

        // Update every 10 seconds
        setInterval(updateAll, 10000);
    </script>
</body>
</html>""")

    # Load dashboard configuration
    dashboard_config_path = os.path.join("config", "dashboard_config.json")
    dashboard_config = {"port": 8000, "host": "0.0.0.0", "debug": True}

    if os.path.exists(dashboard_config_path):
        try:
            with open(dashboard_config_path, "r") as f:
                dashboard_config.update(json.load(f))
        except Exception as e:
            logger.error(f"Error loading dashboard config: {e}")

    # Start the dashboard with debug mode enabled
    logger.info(f"Starting dashboard with debug={dashboard_config['debug']}")
    app.run(
        host=dashboard_config.get("host", "0.0.0.0"),
        port=dashboard_config.get("port", 8000),
        debug=dashboard_config.get("debug", True)
    )
