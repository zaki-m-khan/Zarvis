const mono = "'Share Tech Mono',monospace"

export default function TodayBlocks({ blocks, blockNote }) {
  return (
    <div className="panel" style={{ flex: 1.25, minHeight: 0, display: 'flex', flexDirection: 'column', background: 'linear-gradient(180deg, rgba(13,26,38,.7), rgba(7,14,22,.85))', border: '1px solid rgba(53,224,255,.18)', borderRadius: 6, padding: '16px 18px', position: 'relative', animation: 'panelin .5s ease .15s both' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 12 }}>
        <div style={{ fontWeight: 700, fontSize: 13, letterSpacing: 3.5, color: 'var(--zac, #35E0FF)' }}>◢ TODAY'S BLOCKS</div>
        <div style={{ fontFamily: mono, fontSize: 10, color: 'rgba(140,190,215,.5)', letterSpacing: 1 }}>GOOGLE CAL · SYNCED</div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, overflowY: 'auto', minHeight: 0 }}>
        {blocks.map((b, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '9px 12px', border: `1px solid ${b.borderColor}`, borderRadius: 4, background: b.bg, opacity: b.opacity }}>
            <div style={{ fontFamily: mono, fontSize: 12, color: b.timeColor, whiteSpace: 'nowrap', letterSpacing: '.5px' }}>{b.time}</div>
            <div style={{ flex: 1, fontWeight: 600, fontSize: 15, letterSpacing: '.8px', color: '#dff4ff' }}>{b.name}</div>
            <div style={{ fontFamily: mono, fontSize: 10, letterSpacing: 1.5, color: b.statusColor, whiteSpace: 'nowrap' }}>{b.status}</div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 10, fontFamily: mono, fontSize: 10.5, color: 'rgba(140,190,215,.45)', letterSpacing: '.5px' }}>{blockNote}</div>
    </div>
  )
}
