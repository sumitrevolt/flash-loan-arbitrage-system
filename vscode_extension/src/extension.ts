import * as vscode from 'vscode';
import * as WebSocket from 'ws';
import axios from 'axios';

interface CommandResult {
    success: boolean;
    message: string;
    data?: any;
    timestamp: string;
}

interface SystemStatus {
    mcp_servers: number;
    ai_agents: number;
    revenue_stats: {
        total_profit: number;
        successful_trades: number;
        failed_trades: number;
        opportunities_found: number;
    };
    system_health: string;
}

export class ArbitrageCommandCenter {
    private static instance: ArbitrageCommandCenter;
    private webviewPanel: vscode.WebviewPanel | undefined;
    private websocket: WebSocket | undefined;
    private outputChannel: vscode.OutputChannel;
    private statusBarItem: vscode.StatusBarItem;
    private systemStatus: SystemStatus | undefined;

    constructor(private context: vscode.ExtensionContext) {
        this.outputChannel = vscode.window.createOutputChannel('Arbitrage System');
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
        this.statusBarItem.text = "$(graph-line) Arbitrage: Connecting...";
        this.statusBarItem.command = 'arbitrage.openCommandCenter';
        this.statusBarItem.show();
        
        this.connectToSystem();
        this.updateStatusPeriodically();
    }

    public static getInstance(context: vscode.ExtensionContext): ArbitrageCommandCenter {
        if (!ArbitrageCommandCenter.instance) {
            ArbitrageCommandCenter.instance = new ArbitrageCommandCenter(context);
        }
        return ArbitrageCommandCenter.instance;
    }

    private async connectToSystem() {
        try {
            // Connect to the LangChain command system WebSocket
            this.websocket = new WebSocket('ws://localhost:8888');
            
            this.websocket.on('open', () => {
                this.outputChannel.appendLine('✅ Connected to Arbitrage Command System');
                this.statusBarItem.text = "$(graph-line) Arbitrage: Connected";
                vscode.window.showInformationMessage('Arbitrage Command System Connected');
            });

            this.websocket.on('message', (data: WebSocket.Data) => {
                try {
                    const result = JSON.parse(data.toString()) as CommandResult;
                    this.handleCommandResult(result);
                } catch (error) {
                    this.outputChannel.appendLine(`❌ Error parsing message: ${error}`);
                }
            });

            this.websocket.on('close', () => {
                this.outputChannel.appendLine('🔌 Disconnected from Arbitrage Command System');
                this.statusBarItem.text = "$(graph-line) Arbitrage: Disconnected";
                this.reconnectAfterDelay();
            });

            this.websocket.on('error', (error) => {
                this.outputChannel.appendLine(`❌ WebSocket error: ${error}`);
                this.statusBarItem.text = "$(graph-line) Arbitrage: Error";
            });

        } catch (error) {
            this.outputChannel.appendLine(`❌ Failed to connect: ${error}`);
            this.reconnectAfterDelay();
        }
    }

    private reconnectAfterDelay() {
        setTimeout(() => {
            this.outputChannel.appendLine('🔄 Attempting to reconnect...');
            this.connectToSystem();
        }, 5000);
    }

    private handleCommandResult(result: CommandResult) {
        this.outputChannel.appendLine(`📊 Command Result: ${result.message}`);
        
        if (result.data) {
            this.outputChannel.appendLine(`📋 Data: ${JSON.stringify(result.data, null, 2)}`);
        }

        // Update webview if open
        if (this.webviewPanel && result.data) {
            this.webviewPanel.webview.postMessage({
                type: 'commandResult',
                result: result
            });
        }

        // Show notification for important results
        if (result.success && result.message.includes('profit')) {
            vscode.window.showInformationMessage(`💰 ${result.message}`);
        } else if (!result.success) {
            vscode.window.showErrorMessage(`❌ ${result.message}`);
        }
    }

    public async sendCommand(command: string): Promise<void> {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            vscode.window.showErrorMessage('Not connected to Arbitrage System');
            return;
        }

        try {
            this.outputChannel.appendLine(`🎯 Sending command: ${command}`);
            this.websocket.send(JSON.stringify({ command }));
        } catch (error) {
            this.outputChannel.appendLine(`❌ Failed to send command: ${error}`);
            vscode.window.showErrorMessage(`Failed to send command: ${error}`);
        }
    }

    public openCommandCenter() {
        if (this.webviewPanel) {
            this.webviewPanel.reveal();
            return;
        }

        this.webviewPanel = vscode.window.createWebviewPanel(
            'arbitrageCommandCenter',
            'Arbitrage Command Center',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.webviewPanel.webview.html = this.getWebviewContent();
        
        this.webviewPanel.webview.onDidReceiveMessage(async (message) => {
            switch (message.type) {
                case 'command':
                    await this.sendCommand(message.command);
                    break;
                case 'getStatus':
                    await this.updateSystemStatus();
                    break;
            }
        });

        this.webviewPanel.onDidDispose(() => {
            this.webviewPanel = undefined;
        });
    }

    private async updateSystemStatus() {
        try {
            const response = await axios.get('http://localhost:8889/status');
            this.systemStatus = response.data;
            
            // Update status bar
            const profit = this.systemStatus.revenue_stats.total_profit.toFixed(2);
            this.statusBarItem.text = `$(graph-line) Arbitrage: $${profit} profit`;
            
            // Send to webview
            if (this.webviewPanel) {
                this.webviewPanel.webview.postMessage({
                    type: 'statusUpdate',
                    status: this.systemStatus
                });
            }
        } catch (error) {
            this.outputChannel.appendLine(`❌ Failed to get status: ${error}`);
        }
    }

    private updateStatusPeriodically() {
        setInterval(() => {
            this.updateSystemStatus();
        }, 30000); // Update every 30 seconds
    }

    private getWebviewContent(): string {
        return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Arbitrage Command Center</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    color: var(--vscode-foreground);
                    background-color: var(--vscode-editor-background);
                    padding: 20px;
                    margin: 0;
                }
                .header {
                    display: flex;
                    align-items: center;
                    margin-bottom: 20px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid var(--vscode-panel-border);
                }
                .header h1 {
                    margin: 0;
                    font-size: 24px;
                }
                .status-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 20px;
                }
                .status-card {
                    background-color: var(--vscode-editor-inactiveSelectionBackground);
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 8px;
                    padding: 15px;
                }
                .status-card h3 {
                    margin: 0 0 10px 0;
                    font-size: 14px;
                    opacity: 0.8;
                }
                .status-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: var(--vscode-textLink-foreground);
                }
                .command-section {
                    margin-top: 20px;
                }
                .command-buttons {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 10px;
                    margin-bottom: 20px;
                }
                .btn {
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    padding: 10px 15px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 13px;
                    transition: background-color 0.2s;
                }
                .btn:hover {
                    background-color: var(--vscode-button-hoverBackground);
                }
                .btn.primary {
                    background-color: var(--vscode-textLink-foreground);
                    color: var(--vscode-editor-background);
                }
                .btn.danger {
                    background-color: var(--vscode-errorForeground);
                    color: var(--vscode-editor-background);
                }
                .custom-command {
                    display: flex;
                    gap: 10px;
                    margin-top: 15px;
                }
                .custom-command input {
                    flex: 1;
                    background-color: var(--vscode-input-background);
                    color: var(--vscode-input-foreground);
                    border: 1px solid var(--vscode-input-border);
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 13px;
                }
                .results {
                    margin-top: 20px;
                    background-color: var(--vscode-textBlockQuote-background);
                    border-left: 4px solid var(--vscode-textLink-foreground);
                    padding: 15px;
                    border-radius: 4px;
                }
                .profit {
                    color: #4CAF50;
                }
                .loss {
                    color: #f44336;
                }
                .loading {
                    opacity: 0.6;
                    pointer-events: none;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Arbitrage Command Center</h1>
            </div>

            <div class="status-grid" id="statusGrid">
                <div class="status-card">
                    <h3>Total Profit</h3>
                    <div class="status-value profit" id="totalProfit">$0.00</div>
                </div>
                <div class="status-card">
                    <h3>Successful Trades</h3>
                    <div class="status-value" id="successfulTrades">0</div>
                </div>
                <div class="status-card">
                    <h3>MCP Servers</h3>
                    <div class="status-value" id="mcpServers">0</div>
                </div>
                <div class="status-card">
                    <h3>AI Agents</h3>
                    <div class="status-value" id="aiAgents">0</div>
                </div>
            </div>

            <div class="command-section">
                <h2>Quick Commands</h2>
                <div class="command-buttons">
                    <button class="btn primary" onclick="sendCommand('index codex')">
                        📚 Index & Codex
                    </button>
                    <button class="btn" onclick="sendCommand('self heal')">
                        🔧 Self Heal
                    </button>
                    <button class="btn primary" onclick="sendCommand('start bot')">
                        🤖 Start Bot
                    </button>
                    <button class="btn danger" onclick="sendCommand('stop bot')">
                        ⏹️ Stop Bot
                    </button>
                    <button class="btn primary" onclick="sendCommand('generate revenue')">
                        💰 Generate Revenue
                    </button>
                    <button class="btn" onclick="sendCommand('coordinate agents')">
                        🎯 Coordinate Agents
                    </button>
                    <button class="btn" onclick="sendCommand('system status')">
                        📊 System Status
                    </button>
                    <button class="btn" onclick="sendCommand('scan arbitrage')">
                        🔍 Scan Arbitrage
                    </button>
                </div>

                <div class="custom-command">
                    <input type="text" id="customCommandInput" placeholder="Enter custom command..." />
                    <button class="btn" onclick="sendCustomCommand()">Send</button>
                </div>
            </div>

            <div class="results" id="results" style="display: none;">
                <h3>Results</h3>
                <div id="resultsContent"></div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                
                function sendCommand(command) {
                    document.body.classList.add('loading');
                    vscode.postMessage({ type: 'command', command });
                    showResults('Executing: ' + command);
                }
                
                function sendCustomCommand() {
                    const input = document.getElementById('customCommandInput');
                    const command = input.value.trim();
                    if (command) {
                        sendCommand(command);
                        input.value = '';
                    }
                }
                
                function showResults(message) {
                    const results = document.getElementById('results');
                    const content = document.getElementById('resultsContent');
                    content.innerHTML = '<pre>' + message + '</pre>';
                    results.style.display = 'block';
                }
                
                function updateStatus(status) {
                    document.getElementById('totalProfit').textContent = '$' + status.revenue_stats.total_profit.toFixed(2);
                    document.getElementById('successfulTrades').textContent = status.revenue_stats.successful_trades;
                    document.getElementById('mcpServers').textContent = status.mcp_servers;
                    document.getElementById('aiAgents').textContent = status.ai_agents;
                }
                
                // Listen for messages from extension
                window.addEventListener('message', event => {
                    const message = event.data;
                    switch (message.type) {
                        case 'commandResult':
                            document.body.classList.remove('loading');
                            showResults(JSON.stringify(message.result, null, 2));
                            break;
                        case 'statusUpdate':
                            updateStatus(message.status);
                            break;
                    }
                });
                
                // Enter key support for custom commands
                document.getElementById('customCommandInput').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendCustomCommand();
                    }
                });
                
                // Request initial status
                vscode.postMessage({ type: 'getStatus' });
            </script>
        </body>
        </html>`;
    }

    public dispose() {
        if (this.websocket) {
            this.websocket.close();
        }
        if (this.webviewPanel) {
            this.webviewPanel.dispose();
        }
        this.statusBarItem.dispose();
        this.outputChannel.dispose();
    }
}

export function activate(context: vscode.ExtensionContext) {
    console.log('Arbitrage Command Center extension is now active!');
    
    const commandCenter = ArbitrageCommandCenter.getInstance(context);
    
    // Register commands
    const commands = [
        vscode.commands.registerCommand('arbitrage.openCommandCenter', () => {
            commandCenter.openCommandCenter();
        }),
        vscode.commands.registerCommand('arbitrage.startBot', () => {
            commandCenter.sendCommand('start bot');
        }),
        vscode.commands.registerCommand('arbitrage.stopBot', () => {
            commandCenter.sendCommand('stop bot');
        }),
        vscode.commands.registerCommand('arbitrage.systemStatus', () => {
            commandCenter.sendCommand('system status');
        }),
        vscode.commands.registerCommand('arbitrage.generateRevenue', () => {
            commandCenter.sendCommand('generate revenue');
        }),
        vscode.commands.registerCommand('arbitrage.selfHeal', () => {
            commandCenter.sendCommand('self heal');
        }),
        vscode.commands.registerCommand('arbitrage.indexCodex', () => {
            commandCenter.sendCommand('index codex');
        })
    ];
    
    commands.forEach(command => context.subscriptions.push(command));
    
    // Auto-open command center on activation
    setTimeout(() => {
        commandCenter.openCommandCenter();
    }, 1000);
}

export function deactivate() {
    // Cleanup will be handled automatically
}
