const mono = "'Share Tech Mono',monospace"

export default function TMinus({ countdowns }) {
  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', background: 'linear-gradient(180deg, rgba(13,26,38,.7), rgba(7,14,22,.85))', border: '1px solid rgba(53,224,255,.18)', borderRadius: 6, padding: '14px 18px', minHeight: 0, position: 'relative', animation: 'panelin .5s ease .4s both' }}>
      <div style={{ fontWeight: 700, fontSize: 13, letterSpacing: 3.5, color: 'var(--zac, #35E0FF)', marginBottom: 10 }}>◢ T-MINUS</div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 7, overflowY: 'auto', minHeight: 0 }}>
        {countdowns.map(c => (
          <div key={c.label} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ fontFamily: mono, fontSize: 17, color: c.color, minWidth: 64, textShadow: '0 0 8px rgba(53,224,255,.3)' }}>{c.tm}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: 12.5, letterSpacing: 1, color: '#dff4ff' }}>{c.label}</div>
              <div style={{ fontFamily: mono, fontSize: 9, letterSpacing: 1, color: 'rgba(140,190,215,.45)' }}>{c.date}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
