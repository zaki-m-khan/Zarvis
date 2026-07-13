const mono = "'Share Tech Mono',monospace"

function Stat({ label, value, valueStyle }) {
  return (
    <div>
      <div style={{ fontFamily: mono, fontSize: 9.5, letterSpacing: 1.5, color: 'rgba(140,190,215,.5)' }}>{label}</div>
      <div style={{ fontFamily: mono, fontSize: 17, ...valueStyle }}>{value}</div>
    </div>
  )
}

export default function CutTrajectory() {
  return (
    <div className="panel" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', background: 'linear-gradient(180deg, rgba(13,26,38,.7), rgba(7,14,22,.85))', border: '1px solid rgba(53,224,255,.18)', borderRadius: 6, padding: '16px 18px', position: 'relative', animation: 'panelin .5s ease .3s both' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10 }}>
        <div style={{ fontWeight: 700, fontSize: 13, letterSpacing: 3.5, color: 'var(--zac, #35E0FF)' }}>◢ CUT TRAJECTORY</div>
        <div style={{ fontFamily: mono, fontSize: 10, color: '#7CFFA9', letterSpacing: 1 }}>−1 LB/WK · ON PACE</div>
      </div>
      <div style={{ display: 'flex', gap: 20, marginBottom: 8 }}>
        <Stat label="START" value="165.0" valueStyle={{ color: 'rgba(180,220,240,.7)' }} />
        <Stat label="CURRENT" value="164.6" valueStyle={{ color: '#eaf9ff', textShadow: '0 0 10px rgba(53,224,255,.4)' }} />
        <Stat label="TARGET · SEP" value="157.0" valueStyle={{ color: '#7CFFA9' }} />
      </div>
      <svg viewBox="0 0 330 78" preserveAspectRatio="none" style={{ flex: 1, width: '100%', minHeight: 0 }}>
        <line x1="0" y1="66" x2="330" y2="66" stroke="#7CFFA9" strokeWidth="1" strokeDasharray="4 5" opacity="0.5" />
        <text x="2" y="62" style={{ fontFamily: mono, fontSize: 8, fill: '#7CFFA9', opacity: .7 }}>157 TARGET</text>
        <polyline points="0,10 24,12 48,11 72,14" fill="none" stroke="var(--zac, #35E0FF)" strokeWidth="2" style={{ filter: 'drop-shadow(0 0 5px rgba(53,224,255,.7))' }} />
        <polyline points="72,14 120,20 168,28 216,38 264,50 312,60 330,63" fill="none" stroke="var(--zac, #35E0FF)" strokeWidth="1.5" strokeDasharray="5 5" opacity="0.5" />
        <circle cx="72" cy="14" r="3.5" fill="var(--zac, #35E0FF)" style={{ filter: 'drop-shadow(0 0 6px rgba(53,224,255,.9))' }} />
        <text x="80" y="10" style={{ fontFamily: mono, fontSize: 8, fill: '#cfeeff' }}>YOU ARE HERE</text>
      </svg>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
        <span style={{ fontFamily: mono, fontSize: 9.5, color: 'rgba(140,190,215,.5)', letterSpacing: 1 }}>JUL</span>
        <span style={{ fontFamily: mono, fontSize: 9.5, color: 'rgba(140,190,215,.5)', letterSpacing: 1 }}>AUG</span>
        <span style={{ fontFamily: mono, fontSize: 9.5, color: 'rgba(140,190,215,.5)', letterSpacing: 1 }}>SEP</span>
      </div>
    </div>
  )
}
