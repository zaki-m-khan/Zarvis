const mono = "'Share Tech Mono',monospace"

export default function BootOverlay({ bootShown, bootAnim, skipBoot }) {
  return (
    <div onClick={skipBoot} style={{ position: 'fixed', inset: 0, zIndex: 60, background: '#03060a', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', animation: bootAnim }}>
      <svg viewBox="0 0 200 200" style={{ width: 190, height: 190, marginBottom: 26 }}>
        <circle cx="100" cy="100" r="90" fill="none" stroke="rgba(53,224,255,.15)" strokeWidth="2" />
        <g style={{ transformOrigin: '100px 100px', animation: 'zspin 2.4s linear infinite' }}>
          <circle cx="100" cy="100" r="90" fill="none" stroke="var(--zac, #35E0FF)" strokeWidth="2" strokeDasharray="120 446" strokeLinecap="round" />
        </g>
        <g style={{ transformOrigin: '100px 100px', animation: 'zspinrev 3.6s linear infinite' }}>
          <circle cx="100" cy="100" r="72" fill="none" stroke="var(--zac, #35E0FF)" strokeWidth="4" strokeDasharray="40 80" opacity="0.4" />
        </g>
        <text x="100" y="112" textAnchor="middle" style={{ fontFamily: "'Rajdhani',sans-serif", fontWeight: 700, fontSize: 44, fill: '#eaf9ff', letterSpacing: 2 }}>Z</text>
      </svg>
      <div style={{ fontFamily: "'Rajdhani',sans-serif", fontWeight: 700, fontSize: 30, letterSpacing: 14, color: 'var(--zac, #35E0FF)', textShadow: '0 0 22px rgba(53,224,255,.6)', marginBottom: 24 }}>ZARVIS</div>
      <div style={{ minHeight: 170, width: 420 }}>
        {bootShown.map((ln, i) => (
          <div key={i} style={{ fontFamily: mono, fontSize: 12, lineHeight: 1.8, color: ln.color, letterSpacing: '.5px' }}>{ln.text}</div>
        ))}
      </div>
      <div style={{ position: 'absolute', bottom: 34, fontFamily: mono, fontSize: 10, letterSpacing: 3, color: 'rgba(140,190,215,.35)', animation: 'zblink 1.6s steps(1) infinite' }}>CLICK TO SKIP</div>
    </div>
  )
}
