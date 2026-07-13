const mono = "'Share Tech Mono',monospace"

export default function TopBar({ timeStr, dateStr, statusDots }) {
  return (
    <div style={{ gridColumn: '1 / -1', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'linear-gradient(180deg, rgba(13,26,38,.7), rgba(7,14,22,.85))', border: '1px solid rgba(53,224,255,.18)', borderRadius: 6, padding: '0 22px', animation: 'panelin .5s ease .05s both' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 14 }}>
        <div style={{ fontWeight: 700, fontSize: 24, letterSpacing: 9, color: 'var(--zac, #35E0FF)', textShadow: '0 0 18px rgba(53,224,255,.55)' }}>ZARVIS</div>
        <div style={{ fontFamily: mono, fontSize: 11, color: 'rgba(140,190,215,.55)', letterSpacing: 1 }}>v0.1 · AGENTIC ACCOUNTABILITY SYSTEM</div>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, animation: 'zflicker 7s linear infinite' }}>
        <div style={{ fontFamily: mono, fontSize: 26, color: '#eaf9ff', letterSpacing: 2, textShadow: '0 0 14px rgba(53,224,255,.4)' }}>{timeStr}</div>
        <div style={{ fontFamily: mono, fontSize: 12, color: 'rgba(140,190,215,.6)', letterSpacing: 2 }}>{dateStr}</div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          {statusDots.map(d => (
            <div key={d.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 7, height: 7, borderRadius: '50%', background: d.color, boxShadow: `0 0 8px ${d.color}`, animation: 'zpulse 3s ease-in-out infinite' }} />
              <span style={{ fontFamily: mono, fontSize: 10, letterSpacing: 1.5, color: 'rgba(160,210,235,.65)' }}>{d.label}</span>
            </div>
          ))}
        </div>
        <div style={{ borderLeft: '1px solid rgba(53,224,255,.2)', paddingLeft: 18, fontWeight: 600, fontSize: 13, letterSpacing: 2.5, color: '#eaf9ff' }}>USER: ZAKI KHAN</div>
      </div>
    </div>
  )
}
