import { useEffect, useState } from 'react'

const nodes = ['node1', 'node2', 'node3', 'node4']

export default function App() {
  const [health, setHealth] = useState({})

  useEffect(() => {
    let active = true
    const controller = new AbortController()
    async function load() {
      const entries = await Promise.all(nodes.map(async (id) => {
        try {
          const response = await fetch(`/api/${id}/health`, {
            signal: controller.signal,
          })
          if (!response.ok) throw new Error('Health request failed')
          const data = await response.json()
          if (data.node_id !== id || data.status !== 'ok') throw new Error('Unexpected node')
          return [id, 'API phản hồi']
        } catch {
          return [id, 'Chưa kết nối']
        }
      }))
      if (active) setHealth(Object.fromEntries(entries))
    }
    void load()
    return () => { active = false; controller.abort() }
  }, [])

  return (
    <main>
      <header>
        <p className="eyebrow">CHUỖI KHỐI & SỔ CÁI PHÂN TÁN</p>
        <h1>MiniVoting</h1>
        <p>Khung quan sát mạng bốn validator · Ngưỡng đồng thuận thiết kế: 3/4</p>
      </header>
      <section aria-label="Kết nối API các node" className="nodes">
        {nodes.map((id, index) => (
          <article key={id}>
            <p className="eyebrow">{index === 0 ? 'LEADER DỰ KIẾN' : 'VALIDATOR'}</p>
            <h2>{id}</h2>
            <p role="status">{health[id] ?? 'Đang kiểm tra…'}</p>
            <small>Cổng {8001 + index}</small>
          </article>
        ))}
      </section>
      <aside>
        <h2>Trạng thái bộ khung</h2>
        <p>API health chỉ xác nhận tiến trình đang phản hồi. Consensus, sổ cái,
          certificate và giao dịch sẽ được tích hợp theo các issue của nhóm.</p>
      </aside>
      <footer>TV4 · Dashboard, kiểm thử tích hợp và thực nghiệm</footer>
    </main>
  )
}
