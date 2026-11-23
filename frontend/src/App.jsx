import { useEffect, useState } from 'react'
import { nodes, readNode } from './api'
import { exampleHash, roundStates, screens, txStates } from './wireframe'

function Fields({ rows }) {
  return <dl className="fields">{rows.map(([key, value]) => <div key={key}>
    <dt>{key}</dt><dd>{value ?? '—'}</dd>
  </div>)}</dl>
}

function Hash({ label = 'Block hash' }) {
  return <details className="hash"><summary>{label} · {exampleHash.slice(0, 12)}…</summary>
    <code>{exampleHash}</code><small>Giá trị bố cục mẫu, không phải bằng chứng.</small>
  </details>
}

function LiveNetwork() {
  const [health, setHealth] = useState({})
  const [refresh, setRefresh] = useState(0)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    let active = true
    const controller = new AbortController()
    async function load() {
      const entries = await Promise.all(nodes.map(async (id) => [id, await readNode(id, fetch, controller.signal)]))
      if (active) { setHealth(Object.fromEntries(entries)); setLoading(false) }
    }
    void load()
    return () => { active = false; controller.abort() }
  }, [refresh])
  return <>
    <div className="section-heading"><div><p className="eyebrow">NGUỒN · API LOCAL THẬT</p>
      <h2>Kết nối bốn node</h2></div>
      <button disabled={loading} onClick={() => { setLoading(true); setHealth({}); setRefresh(refresh + 1) }}>
        {loading ? 'Đang kiểm tra…' : 'Kiểm tra lại'}
      </button></div>
    <p className="muted">Health xác nhận tiến trình phản hồi. Quorum và tính đúng của ledger cần bằng chứng riêng.</p>
    <div className="nodes">{nodes.map((id, i) => {
      const result = health[id]
      return <article className="node" key={id}>
        <p className="eyebrow">{i === 0 ? 'LEADER CỐ ĐỊNH' : 'VALIDATOR'}</p>
        <h3>{id}<span className="port">:{8001 + i}</span></h3>
        <p role="status" className={`badge ${result?.health.data ? 'good' : 'neutral'}`}>
          {!result ? 'Đang kiểm tra' : result.health.data ? 'API phản hồi' : 'Không đọc được API'}
        </p>
        <Fields rows={[
          ['Consensus ready', result?.health.data ? String(result.health.data.consensus_ready) : '—'],
          ['Status API', result?.status.error ?? (result?.status.data ? 'Đã nhận /status' : '—')],
          ['Quan sát lúc', result ? new Date(result.observedAt).toLocaleTimeString('vi-VN') : '—'],
        ]} />
        {result?.health.error && <small>{result.health.error}</small>}
      </article>
    })}</div>
    <div className="notice"><strong>Phạm vi W1</strong><p>Kết nối thật chỉ đọc /health và /status khi mở màn hoặc kiểm tra lại.
      Explorer và timeline đang ở bước wireframe. Chuyển sang “Wireframe mẫu” để review bố cục.</p></div>
  </>
}

function NetworkExample({ round }) {
  const [phase, prepares, commits, description] = roundStates[round]
  return <><div className="nodes">{nodes.map((id, i) => <article className="node" key={id}>
    <p className="eyebrow">{i === 0 ? 'LEADER CỐ ĐỊNH' : 'VALIDATOR'}</p><h3>{id}</h3>
    <span className="badge neutral">MẪU · {round}</span>
    <Fields rows={[
      ['committed_height', round === 'DECIDED' ? 7 : 6],
      ['target_height', round === 'DECIDED' ? 8 : 7], ['phase', phase],
      ['sync_state', round === 'SYNCING' ? 'SYNCING' : 'SYNCED'],
    ]} /><Hash label="Tip hash mẫu" />
  </article>)}</div>
    <div className="round-summary"><div><p className="eyebrow">ROUND MẪU · HEIGHT 7 · NODE1</p>
      <h3>{round}</h3><p>{description}</p></div>
      <div className="vote-total"><strong>{prepares}<small>/3</small></strong><span>PREPARE mẫu</span></div>
      <div className="vote-total"><strong>{commits}<small>/3</small></strong><span>COMMIT mẫu</span></div>
    </div></>
}

function TransactionExample({ txState, setTxState }) {
  return <><label className="control">Trạng thái cần review
    <select value={txState} onChange={(e) => setTxState(e.target.value)}>
      {Object.entries(txStates).map(([id, [label]]) => <option key={id} value={id}>{id} · {label}</option>)}
    </select></label>
    <div className="notice"><span className="badge neutral">MẪU · {txState}</span>
      <h3>{txStates[txState][0]}</h3><p>{txStates[txState][1]}</p></div>
    <Fields rows={[
      ['observed_node_id', 'node1 (mẫu)'], ['tx_id', exampleHash],
      ['height', ['proposed', 'committed'].includes(txState) ? 7 : null],
      ['block_hash', ['proposed', 'committed'].includes(txState) ? exampleHash : null],
      ['reason', txState === 'rejected' ? 'MEMPOOL_EXPIRED (mẫu)' : null],
    ]} /><p className="muted">V1 dự kiến nhận giao dịch đã ký từ ví/CLI của TV1. W1 không gửi giao dịch hoặc lưu khóa.</p></>
}

function CertificateExample() {
  return <><div className="notice"><strong>Bố cục certificate · chưa có chứng cứ thật</strong>
    <p>Quorum yêu cầu ít nhất 3 validator khác danh tính, cùng context và chữ ký hợp lệ.
      Dashboard hiển thị bằng chứng từ node, không tự xác nhận certificate bằng số đếm.</p></div>
    <Fields rows={[
      ['protocol_version / chain_id', '1 / minivoting-demo (mẫu)'], ['height / view / phase', '7 / 0 / COMMIT'],
    ]} /><Hash />
    <div className="table-scroll"><table><caption>Vị trí hiển thị chữ ký (mẫu)</caption>
      <thead><tr><th>Validator</th><th>Chữ ký</th><th>Nguồn xác minh</th></tr></thead>
      <tbody>{nodes.slice(0, 3).map((id) => <tr key={id}><td>{id}</td>
        <td>Chưa có · không tạo chữ ký mẫu</td><td>Chờ backend kiểm chứng</td></tr>)}</tbody>
    </table></div></>
}

function TimelineExample() {
  return <><p>Quan sát mẫu tại node1 · height 7. Sự kiện lỗi có sender khai báo, chưa chắc là danh tính đã xác minh.</p>
    <div className="table-scroll"><table><caption>Thứ tự sự kiện minh họa, không phải log thực chạy</caption>
      <thead><tr><th>seq / observed_at_ms</th><th>peer_id</th><th>sender_id</th><th>Phase</th><th>Outcome</th><th>Reason</th></tr></thead>
      <tbody>{[
        [1, 'node2', 'PREPARE', 'valid', '—'], [2, 'node2', 'PREPARE', 'duplicate', 'Không tăng số danh tính'],
        [3, 'node3', 'COMMIT', 'buffered', 'Chờ proposal/prepared'],
        [4, 'node4 (khai báo)', 'COMMIT', 'invalid', 'INVALID_SIGNATURE'],
        [5, 'node2', 'PREPARE', 'equivocation', 'VOTE_CONFLICT'],
      ].map(([seq, sender, phase, outcome, reason]) => <tr key={seq}>
        <td>{seq} / {1700000000000 + seq}</td><td>{seq === 4 ? 'node3' : sender}</td><td>{sender}</td><td>{phase}</td>
        <td><span className="badge neutral">{outcome}</span></td><td>{reason}</td>
      </tr>)}</tbody></table></div><Hash />
    <p className="muted">V1 dự kiến giữ 100 event gần nhất của round; events có thể rỗng sau restart.
      Peer ID không thay thế sender đã kiểm chữ ký.</p></>
}

export default function App() {
  const [mode, setMode] = useState('live')
  const [screen, setScreen] = useState('network')
  const [round, setRound] = useState('COMMITTING')
  const [txState, setTxState] = useState('pending')
  const title = screens.find(([id]) => id === screen)[2]
  return <div className="app-shell">
    <a className="skip-link" href="#content">Đến nội dung</a>
    <aside className="sidebar"><a className="brand" href="#content"><span className="brand-mark">M</span>MiniVoting</a>
      <p className="sidebar-label">WORKSPACE / TV4 · W1</p>
      <nav aria-label="Các màn hình wireframe">{screens.map(([id, number, label]) =>
        <button key={id} aria-current={screen === id ? 'page' : undefined} onClick={() => setScreen(id)}>
          <span>{number}</span>{label}
        </button>)}</nav>
      <div className="sidebar-note"><strong>04 validator / 03 quorum</strong>
        <p>PROPOSE → PREPARE → COMMIT</p><small>Leader cố định. Lấy cảm hứng PBFT; chưa có view change.</small></div>
    </aside>
    <main id="content"><header className="page-header"><div><p className="eyebrow">PERMISSIONED BLOCKCHAIN / W1</p>
      <h1>{title}</h1><p className="muted">Quan sát rõ nguồn dữ liệu, trạng thái và bằng chứng.</p></div>
      <div className="mode-switch" role="group" aria-label="Nguồn dữ liệu">
        <button aria-pressed={mode === 'live'} onClick={() => setMode('live')}>Kết nối thật</button>
        <button aria-pressed={mode === 'wireframe'} onClick={() => setMode('wireframe')}>Wireframe mẫu</button>
      </div></header>
      {mode === 'wireframe' ? <>
        <div className="source-banner" role="status"><strong>WIREFRAME MẪU · DỮ LIỆU MINH HỌA</strong>
          <span>Không gọi API, không ký phiếu, không chốt block. Thay đổi kịch bản chỉ đổi bản xem mẫu.</span></div>
        {screen === 'network' && <label className="control">Kịch bản round
          <select value={round} onChange={(e) => setRound(e.target.value)}>
            {Object.keys(roundStates).map((id) => <option key={id}>{id}</option>)}
          </select></label>}
        <section className="panel" aria-label={title}>
          {screen === 'network' && <NetworkExample round={round} />}
          {screen === 'transaction' && <TransactionExample txState={txState} setTxState={setTxState} />}
          {screen === 'account' && <><h2>Committed account snapshot · mẫu</h2>
            <p>Số dư và nonce lấy từ ledger đã chốt tại node nguồn. Pending/proposed không làm đổi snapshot.</p>
            <Fields rows={[
              ['observed_node_id', 'node1 (mẫu)'], ['address', exampleHash], ['balance', '1000 coin nguyên (mẫu)'],
              ['nonce', 2], ['committed_height', 6],
            ]} /><Hash label="Tip hash" /></>}
          {screen === 'block' && <><h2>Block explorer · mẫu</h2>
            <p>Danh sách theo height tăng; from_height bao gồm điểm bắt đầu. Giới hạn trang 1–50, mặc định 20.</p>
            <Fields rows={[
              ['observed_node_id', 'node1 (mẫu)'], ['height', 7], ['proposer_id', 'node1'],
              ['timestamp_ms', 1700000000000], ['transaction_count', 1], ['next_from_height', null],
            ]} /><Hash /><Hash label="prev_hash" /><Hash label="state_hash" />
            <p>Chi tiết block dương: proposal + transactions + commit certificate. Height 0 dùng GenesisRecord.</p>
            <button onClick={() => setScreen('certificate')}>Xem bố cục certificate →</button></>}
          {screen === 'certificate' && <CertificateExample />}
          {screen === 'timeline' && <TimelineExample />}
        </section>
      </> : screen === 'network' ? <LiveNetwork /> : <section className="panel empty">
        <p className="eyebrow">KẾT NỐI THẬT / CHƯA TÍCH HỢP</p><h2>{title} đang ở bước wireframe</h2>
        <p>W1 chưa đọc dữ liệu ledger cho màn này. Dùng chế độ mẫu để review trường dữ liệu và trạng thái.</p>
        <button onClick={() => setMode('wireframe')}>Mở wireframe mẫu</button>
      </section>}
      <footer><span>MiniVoting · Đồ án Chuỗi khối & công nghệ sổ cái phân tán</span><span>TV4 / W1 · Chờ review nhóm</span></footer>
    </main>
  </div>
}
