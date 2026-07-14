const mono = "'Share Tech Mono',monospace"

function Stat({ label, value, valueStyle }) {
  return (
    <div>
      <div style={{ fontFamily: mono, fontSize: 9.5, letterSpacing: 1.5, color: 'rgba(140,190,215,.5)' }}>{label}</div>
      <div style={{ fontFamily: mono, fontSize: 17, ...valueStyle }}>{value}</div>
    </div>
  )
}

// Timeline: Jul 1 -> Sep 30 mapped to x 0..330; weight START..TARGET mapped to y 10..66.
const START_FALLBACK = 165.0
const TARGET = 157.0
const T0 = new Date('2026-07-01T00:00:00').getTime()
const T1 = new Date('2026-09-30T00:00:00').getTime()

export default function CutTrajectory({ weights }) {
  // weights: [{ts: 'YYYY-MM-DD', weight}] from /api/state, or null (demo)
  const series = (weights && weights.length) ? weights : null
  const start = series ? series[0].weight : START_FALLBACK
  const current = series ? series[series.length - 1].weight : 164.6
  const isLive = !!series

  const x = ts => Math.max(0, Math.min(330, ((new Date(ts + 'T12:00:00').getTime() - T0) / (T1 - T0)) * 330))
  const y = w => {
    const top = Math.max(start, TARGET + 1)
    return 10 + ((top - w) / (TARGET - top)) * -56 // start -> y10, target -> y66
  }

  let solid = '0,10 24,12 48,11 72,14'
  let cx = 72, cy = 14
  if (series) {
    solid = series.map(p => `${x(p.ts).toFixed(1)},${y(p.weight).toFixed(1)}`).join(' ')
    cx = x(series[series.length - 1].ts); cy = y(current)
    if (series.length === 1) solid = `${cx - 4},${cy} ${cx},${cy}`
  }
  const projected = `${cx},${cy} 330,66`

  const onPace = current <= start - ((new Date().getTime() - T0) / (T1 - T0)) * (start - TARGET) + 0.5
  return (
    <div className="panel" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', background: 'linear-gradient(180deg, rgba(13,26,38,.7), rgba(7,14,22,.85))', border: '1px solid rgba(53,224,255,.18)', borderRadius: 6, padding: '16px 18px', position: 'relative', animation: 'panelin .5s ease .3s both' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10 }}>
        <div style={{ fontWeight: 700, fontSize: 13, letterSpacing: 3.5, color: 'var(--zac, #35E0FF)' }}>◢ CUT TRAJECTORY</div>
        <div style={{ fontFamily: mono, fontSize: 10, color: onPace ? '#7CFFA9' : '#FFC14D', letterSpacing: 1 }}>
          {isLive ? (onPace ? '−1 LB/WK · ON PACE' : 'BEHIND PACE') : '−1 LB/WK · DEMO'}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 20, marginBottom: 8 }}>
        <Stat label="START" value={start.toFixed(1)} valueStyle={{ color: 'rgba(180,220,240,.7)' }} />
        <Stat label="CURRENT" value={current.toFixed(1)} valueStyle={{ color: '#eaf9ff', textShadow: '0 0 10px rgba(53,224,255,.4)' }} />
        <Stat label="TARGET · SEP" value={TARGET.toFixed(1)} valueStyle={{ color: '#7CFFA9' }} />
      </div>
      <svg viewBox="0 0 330 78" preserveAspectRatio="none" style={{ flex: 1, width: '100%', minHeight: 0 }}>
        <line x1="0" y1="66" x2="330" y2="66" stroke="#7CFFA9" strokeWidth="1" strokeDasharray="4 5" opacity="0.5" />
        <text x="2" y="62" style={{ fontFamily: mono, fontSize: 8, fill: '#7CFFA9', opacity: .7 }}>157 TARGET</text>
        <polyline points={solid} fill="none" stroke="var(--zac, #35E0FF)" strokeWidth="2" style={{ filter: 'drop-shadow(0 0 5px rgba(53,224,255,.7))' }} />
        <polyline points={projected} fill="none" stroke="var(--zac, #35E0FF)" strokeWidth="1.5" strokeDasharray="5 5" opacity="0.5" />
        <circle cx={cx} cy={cy} r="3.5" fill="var(--zac, #35E0FF)" style={{ filter: 'drop-shadow(0 0 6px rgba(53,224,255,.9))' }} />
        <text x={Math.min(cx + 8, 250)} y={Math.max(cy - 4, 8)} style={{ fontFamily: mono, fontSize: 8, fill: '#cfeeff' }}>YOU ARE HERE</text>
      </svg>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
        <span style={{ fontFamily: mono, fontSize: 9.5, color: 'rgba(140,190,215,.5)', letterSpacing: 1 }}>JUL</span>
        <span style={{ fontFamily: mono, fontSize: 9.5, color: 'rgba(140,190,215,.5)', letterSpacing: 1 }}>AUG</span>
        <span style={{ fontFamily: mono, fontSize: 9.5, color: 'rgba(140,190,215,.5)', letterSpacing: 1 }}>SEP</span>
      </div>
    </div>
  )
}
