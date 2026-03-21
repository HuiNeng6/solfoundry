/**
 * Dispute Resolution API Tests
 * 
 * Tests for the Dispute Resolution System (Issue #192)
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { TestContext } from '../test-helpers';

describe('Dispute Resolution API', () => {
  let ctx: TestContext;

  beforeAll(async () => {
    ctx = new TestContext();
    await ctx.setup();
  });

  afterAll(async () => {
    await ctx.teardown();
  });

  describe('POST /api/disputes', () => {
    it('should create a new dispute', async () => {
      const response = await ctx.request
        .post('/api/disputes')
        .send({
          bounty_id: 'test-bounty-id',
          reason: 'incorrect_review',
          description: 'The AI review incorrectly evaluated my submission. The code meets all acceptance criteria.',
          evidence_links: [
            { type: 'link', url: 'https://github.com/example/pr/1', description: 'My PR with the solution' }
          ]
        });

      expect(response.status).toBe(201);
      expect(response.body).toHaveProperty('id');
      expect(response.body.status).toBe('pending');
      expect(response.body.reason).toBe('incorrect_review');
    });

    it('should reject dispute without bounty_id', async () => {
      const response = await ctx.request
        .post('/api/disputes')
        .send({
          reason: 'incorrect_review',
          description: 'Test description'
        });

      expect(response.status).toBe(422);
    });

    it('should reject dispute with short description', async () => {
      const response = await ctx.request
        .post('/api/disputes')
        .send({
          bounty_id: 'test-bounty-id',
          reason: 'incorrect_review',
          description: 'Too short'
        });

      expect(response.status).toBe(422);
    });
  });

  describe('GET /api/disputes', () => {
    it('should list disputes', async () => {
      const response = await ctx.request
        .get('/api/disputes');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('items');
      expect(response.body).toHaveProperty('total');
    });

    it('should filter by status', async () => {
      const response = await ctx.request
        .get('/api/disputes?status=pending');

      expect(response.status).toBe(200);
      expect(response.body.items.every((d: any) => d.status === 'pending')).toBe(true);
    });
  });

  describe('GET /api/disputes/:id', () => {
    it('should return dispute details with history', async () => {
      // First create a dispute
      const createResponse = await ctx.request
        .post('/api/disputes')
        .send({
          bounty_id: 'test-bounty-id-2',
          reason: 'technical_issue',
          description: 'Technical issue prevented proper testing.'
        });

      const disputeId = createResponse.body.id;

      const response = await ctx.request
        .get(`/api/disputes/${disputeId}`);

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('history');
    });

    it('should return 404 for non-existent dispute', async () => {
      const response = await ctx.request
        .get('/api/disputes/non-existent-id');

      expect(response.status).toBe(404);
    });
  });

  describe('POST /api/disputes/:id/evidence', () => {
    it('should submit additional evidence', async () => {
      // First create a dispute
      const createResponse = await ctx.request
        .post('/api/disputes')
        .send({
          bounty_id: 'test-bounty-id-3',
          reason: 'other',
          description: 'Test dispute for evidence submission.'
        });

      const disputeId = createResponse.body.id;

      const response = await ctx.request
        .post(`/api/disputes/${disputeId}/evidence`)
        .send({
          evidence_links: [
            { type: 'link', url: 'https://example.com/evidence', description: 'Additional evidence' }
          ]
        });

      expect(response.status).toBe(200);
      expect(response.body.evidence_links.length).toBeGreaterThan(0);
    });
  });

  describe('POST /api/disputes/:id/resolve', () => {
    it('should resolve a dispute', async () => {
      // First create a dispute
      const createResponse = await ctx.request
        .post('/api/disputes')
        .send({
          bounty_id: 'test-bounty-id-4',
          reason: 'incorrect_review',
          description: 'Test dispute for resolution.'
        });

      const disputeId = createResponse.body.id;

      const response = await ctx.request
        .post(`/api/disputes/${disputeId}/resolve`)
        .send({
          outcome: 'approved',
          review_notes: 'After review, the contributor\'s submission meets all criteria.',
          resolution_action: 'Payout will be released within 24 hours.'
        });

      expect(response.status).toBe(200);
      expect(response.body.status).toBe('resolved');
      expect(response.body.outcome).toBe('approved');
    });
  });

  describe('POST /api/disputes/:id/ai-mediate', () => {
    it('should run AI mediation', async () => {
      // First create a dispute
      const createResponse = await ctx.request
        .post('/api/disputes')
        .send({
          bounty_id: 'test-bounty-id-5',
          reason: 'incorrect_review',
          description: 'Test dispute for AI mediation.'
        });

      const disputeId = createResponse.body.id;

      const response = await ctx.request
        .post(`/api/disputes/${disputeId}/ai-mediate`);

      expect(response.status).toBe(200);
      // AI score >= 7 should auto-resolve
      expect(['resolved', 'under_review']).toContain(response.body.status);
    });
  });

  describe('GET /api/disputes/stats', () => {
    it('should return dispute statistics', async () => {
      const response = await ctx.request
        .get('/api/disputes/stats');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('total_disputes');
      expect(response.body).toHaveProperty('pending_disputes');
      expect(response.body).toHaveProperty('resolved_disputes');
      expect(response.body).toHaveProperty('approval_rate');
    });
  });
});