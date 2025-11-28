const express = require('express');
const helmet = require('helmet');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3111;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Metrics storage
let metrics = {
  requests: 0,
  errors: 0,
  startTime: Date.now()
};

// Routes
app.get('/', (req, res) => {
  metrics.requests++;
  res.json({ 
    message: 'CI/CD Pipeline Demo Application',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'healthy',
    uptime: Date.now() - metrics.startTime
  });
});

app.get('/ready', (req, res) => {
  res.status(200).json({ status: 'ready' });
});

app.get('/metrics', (req, res) => {
  res.json(metrics);
});

app.get('/api/data', (req, res) => {
  metrics.requests++;
  res.json({
    data: [
      { id: 1, name: 'Item 1' },
      { id: 2, name: 'Item 2' },
      { id: 3, name: 'Item 3' }
    ]
  });
});

// Error simulation endpoint (for testing)
app.get('/api/error', (req, res) => {
  metrics.errors++;
  res.status(500).json({ error: 'Simulated error' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// Error handler
app.use((err, req, res, next) => {
  metrics.errors++;
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

const server = app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = { app, server };