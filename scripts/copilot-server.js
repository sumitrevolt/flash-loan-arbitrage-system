const express = require('express');
const app = express();

app.use(express.json());

app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'enhanced-copilot-mcp',
    timestamp: new Date().toISOString()
  });
});

app.get('/assist', (req, res) => {
  res.json({
    service: 'enhanced-copilot-mcp',
    message: 'AI assistance ready',
    capabilities: ['code-completion', 'code-analysis', 'documentation']
  });
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Enhanced Copilot MCP Server running on port ${PORT}`);
});
