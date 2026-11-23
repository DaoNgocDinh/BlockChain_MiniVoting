export const nodes = ['node1', 'node2', 'node3', 'node4']

// Read-only W1 adapter. No mock fallback, signing, submission or peer routes.
export async function readNode(nodeId, fetcher = fetch, signal) {
  if (!nodes.includes(nodeId)) throw new Error('Unknown node')
  async function read(path) {
    try {
      const response = await fetcher(`/api/${nodeId}/${path}`, {
        signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(3000)])
          : AbortSignal.timeout(3000),
      })
      const body = await response.json()
      // main's W1 scaffold uses FastAPI detail; proposed v1 uses error.code.
      if (!response.ok) return { error: body?.error?.code ?? body?.detail?.code ?? `HTTP_${response.status}` }
      if (body.node_id !== nodeId) return { error: 'INVALID_RESPONSE' }
      if (path === 'health' && (body.status !== 'ok' || typeof body.consensus_ready !== 'boolean')) {
        return { error: 'INVALID_RESPONSE' }
      }
      return { data: body }
    } catch {
      return { error: 'NETWORK_OR_INVALID_RESPONSE' }
    }
  }
  const [health, status] = await Promise.all([read('health'), read('status')])
  return { nodeId, observedAt: new Date().toISOString(), health, status }
}
