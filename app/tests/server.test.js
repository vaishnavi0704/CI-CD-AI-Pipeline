const request = require('supertest');
const { app, server } = require('../src/server');

describe('API Endpoints', () => {
  afterAll((done) => {
    server.close(done);
  });

  test('GET / should return welcome message', async () => {
    const response = await request(app).get('/');
    expect(response.statusCode).toBe(200);
    expect(response.body.message).toBe('CI/CD Pipeline Demo Application');
  });

  test('GET /health should return healthy status', async () => {
    const response = await request(app).get('/health');
    expect(response.statusCode).toBe(200);
    expect(response.body.status).toBe('healthy');
  });

  test('GET /ready should return ready status', async () => {
    const response = await request(app).get('/ready');
    expect(response.statusCode).toBe(200);
    expect(response.body.status).toBe('ready');
  });

  test('GET /api/data should return data array', async () => {
    const response = await request(app).get('/api/data');
    expect(response.statusCode).toBe(200);
    expect(Array.isArray(response.body.data)).toBe(true);
    expect(response.body.data.length).toBeGreaterThan(0);
  });

  test('GET /metrics should return metrics object', async () => {
    const response = await request(app).get('/metrics');
    expect(response.statusCode).toBe(200);
    expect(response.body).toHaveProperty('requests');
    expect(response.body).toHaveProperty('errors');
  });

  test('GET /nonexistent should return 404', async () => {
    const response = await request(app).get('/nonexistent');
    expect(response.statusCode).toBe(404);
  });
});