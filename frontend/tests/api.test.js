import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readNode } from '../src/api.js'

test('health stays reachable when ledger returns 503; preserves the API error', async () => {
  const calls = []
  const result = await readNode('node2', async (url) => {
    calls.push(url)
    return url.endsWith('/health')
      ? Response.json({ node_id: 'node2', status: 'ok', consensus_ready: false })
      : Response.json({ error: { code: 'CONSENSUS_NOT_READY' } }, { status: 503 })
  })
  assert.equal(result.health.data.consensus_ready, false)
  assert.equal(result.status.error, 'CONSENSUS_NOT_READY')
  assert.deepEqual(calls.sort(), ['/api/node2/health', '/api/node2/status'])
})

test('wrong node, broken JSON and network errors do not create live data', async () => {
  for (const fetcher of [
    async () => Response.json({ node_id: 'node4', status: 'ok', consensus_ready: true }),
    async () => new Response('not json'),
    async () => { throw new Error('offline') },
  ]) {
    const result = await readNode('node1', fetcher)
    assert.ok(result.health.error)
    assert.ok(result.status.error)
    assert.equal(result.health.data, undefined)
    assert.equal(result.status.data, undefined)
  }
})

test('rejects arbitrary node paths before fetching', async () => {
  await assert.rejects(readNode('../peer/commit', () => assert.fail('must not fetch')))
})

test('reads the existing main scaffold error envelope as well as v1', async () => {
  const result = await readNode('node1', async () => Response.json({
    detail: { code: 'CONSENSUS_NOT_READY', message: 'Not implemented' },
  }, { status: 503 }))
  assert.equal(result.status.error, 'CONSENSUS_NOT_READY')
  assert.equal(result.status.data, undefined)
})
