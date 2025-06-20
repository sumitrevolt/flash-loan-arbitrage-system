const express = require('express');
const app = express();

app.use(express.json());

app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'price-oracle-mcp',
    timestamp: new Date().toISOString()
  });
});

app.get('/price/:token', (req, res) => {
  const token = req.params.token;
  const mockPrice = Math.random() * 1000;
  res.json({
    token: token,
    price: mockPrice,
    timestamp: new Date().toISOString(),
    source: 'mock-oracle'
  });
});

app.get('/prices', (req, res) => {
  const tokens = ['ETH', 'BTC', 'USDC', 'DAI', 'WETH'];
  const prices = tokens.map(token => ({
    token,
    price: Math.random() * 1000,
    timestamp: new Date().toISOString()
  }));
  res.json({ prices });
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Price Oracle MCP Server running on port ${PORT}`);
});
