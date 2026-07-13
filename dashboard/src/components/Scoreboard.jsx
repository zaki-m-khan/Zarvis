const mono = "'Share Tech Mono',monospace"

export default function Scoreboard({ metrics, onPaceLabel, weekSquares }) {
  return (
    <div className="panel" style={{ flex: 1.45, minHeight: 0, display: 'flex', flexDirection: 'column', background: 'linear-gradient(180deg, rgba(13,26,38,.7), rgba(7,14,22,.85))', border: '1px solid rgba(53,224,255,.18)', borderRadius: 6, padding: '16px 18px', position: 'relative', animation: 'panelin .5s ease .2s both' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 12 }}>
        <div style={{ fontWeight: 700, fontSize: 13, letterSpacing: 3.5, color: 'var(--zac, #35E0FF)' }}>◢ WEEKLY SCOREBOARD</div>
        <div style={{ fontFamily: mono, fontSize: 10, color: 'rgba(140,190,215,.55)', letterSpacing: 1 }}>{onPaceLabel}</div>
      </div>
      <div style={{ display: 'flex', gap: 5, marginBottom: 14 }}>
        {weekSquares.map((q, i) => (
          <div key={i} style={{ flex: 1, height: 6, borderRadius: 2, background: q.bg, boxShadow: q.glow }} />
        ))}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 11, overflowY: 'auto', minHeight: 0 }}>
        {metrics.map(m => (
          <div key={m.name}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
              <span style={{ fontWeight: 600, fontSize: 13.5, letterSpacing: 1.5, color: '#dff4ff' }}>{m.name}</span>
              <span style={{ display: 'flex', gap: 10, alignItems: 'baseline' }}>
                <span style={{ fontFamily: mono, fontSize: 12, color: '#eaf9ff' }}>{m.val}</span>
                <span style={{ fontFamily: mono, fontSize: 9, letterSpacing: 1, color: m.statusColor }}>{m.status}</span>
              </span>
            </div>
            <div style={{ height: 5, background: 'rgba(53,224,255,.1)', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: m.width, background: m.barColor, borderRadius: 2, boxShadow: `0 0 8px ${m.barColor}` }} />
            </div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid rgba(53,224,255,.12)', fontFamily: mono, fontSize: 10, color: 'rgba(140,190,215,.5)', letterSpacing: '.5px' }}>GREEN WEEK = 5 OF 6 · SCORED SUNDAY 17:00</div>
    </div>
  )
}
