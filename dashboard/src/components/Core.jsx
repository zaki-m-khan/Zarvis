const mono = "'Share Tech Mono',monospace"

function Readout({ pos, label, value }) {
  return (
    <div style={{ position: 'absolute', ...pos }}>
      <div style={{ fontFamily: mono, fontSize: 9.5, letterSpacing: 2, color: 'rgba(140,190,215,.45)' }}>{label}</div>
      <div style={{ fontFamily: mono, fontSize: 16, color: '#dff4ff' }}>{value}</div>
    </div>
  )
}

export default function Core({ weekLabel, ringDash, coreStatus, speaking, voiceLine, bars }) {
  return (
    <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 0, animation: 'panelin .6s ease .2s both' }}>

      {/* corner readouts */}
      <Readout pos={{ top: 8, left: 14, textAlign: 'left' }} label="WEEK" value={weekLabel} />
      <Readout pos={{ top: 8, right: 14, textAlign: 'right' }} label="GREEN WEEKS" value="0 / 12" />
      <Readout pos={{ bottom: 8, left: 14, textAlign: 'left' }} label="CAL / PROTEIN" value="1750 · 160–180g" />
      <Readout pos={{ bottom: 8, right: 14, textAlign: 'right' }} label="MISSION" value="3 GOALS · 1 SUMMER" />

      {/* core */}
      <svg viewBox="0 0 500 500" style={{ width: 'min(44vh, 480px)', height: 'min(44vh, 480px)', overflow: 'visible' }}>
        <defs>
          <radialGradient id="zcoreglow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--zac, #35E0FF)" stopOpacity="0.55" />
            <stop offset="55%" stopColor="var(--zac, #35E0FF)" stopOpacity="0.12" />
            <stop offset="100%" stopColor="var(--zac, #35E0FF)" stopOpacity="0" />
          </radialGradient>
        </defs>
        <circle cx="250" cy="250" r="238" fill="none" stroke="rgba(53,224,255,.1)" strokeWidth="1" />
        <circle cx="250" cy="250" r="228" fill="none" stroke="rgba(53,224,255,.35)" strokeWidth="2" strokeDasharray="2 10" />
        <g style={{ transformOrigin: '250px 250px', animation: 'zspin 70s linear infinite' }}>
          <circle cx="250" cy="250" r="204" fill="none" stroke="var(--zac, #35E0FF)" strokeWidth="3" strokeDasharray="46 30" opacity="0.5" />
        </g>
        <g style={{ transformOrigin: '250px 250px', animation: 'zspinrev 46s linear infinite' }}>
          <circle cx="250" cy="250" r="182" fill="none" stroke="var(--zac, #35E0FF)" strokeWidth="8" strokeDasharray="100 190" opacity="0.28" />
        </g>
        <g style={{ transformOrigin: '250px 250px', animation: 'zspin 26s linear infinite' }}>
          <circle cx="250" cy="250" r="164" fill="none" stroke="rgba(53,224,255,.5)" strokeWidth="1.5" strokeDasharray="12 8 3 8" />
        </g>
        <circle cx="250" cy="250" r="146" fill="none" stroke="rgba(53,224,255,.14)" strokeWidth="7" />
        <circle cx="250" cy="250" r="146" fill="none" stroke="var(--zac, #35E0FF)" strokeWidth="7" strokeLinecap="round" strokeDasharray={ringDash} transform="rotate(-90 250 250)" style={{ filter: 'drop-shadow(0 0 6px rgba(53,224,255,.8))' }} />
        {speaking && (
          <circle cx="250" cy="250" r="132" fill="none" stroke="var(--zac, #35E0FF)" strokeWidth="2" style={{ animation: 'zping .9s ease-in-out infinite' }} />
        )}
        <circle cx="250" cy="250" r="120" fill="url(#zcoreglow)" style={{ animation: 'zpulse 4.5s ease-in-out infinite' }} />
        <circle cx="250" cy="250" r="120" fill="none" stroke="rgba(53,224,255,.4)" strokeWidth="1.5" />
        <text x="250" y="252" textAnchor="middle" style={{ fontFamily: "'Rajdhani',sans-serif", fontWeight: 700, fontSize: 110, fill: '#eaf9ff', letterSpacing: 2 }}>Z</text>
        <text x="250" y="300" textAnchor="middle" style={{ fontFamily: mono, fontSize: 15, fill: 'var(--zac, #35E0FF)', letterSpacing: 6 }}>{coreStatus}</text>
      </svg>

      {/* voice line */}
      <div style={{ marginTop: 6, minHeight: 52, maxWidth: 560, textAlign: 'center', fontFamily: mono, fontSize: 14.5, lineHeight: 1.55, color: '#d8f2ff', textShadow: '0 0 10px rgba(53,224,255,.25)', padding: '0 20px' }}>
        <span>{voiceLine}</span>
        {speaking && (
          <span style={{ display: 'inline-block', width: 9, height: 16, background: 'var(--zac, #35E0FF)', marginLeft: 3, verticalAlign: 'middle', animation: 'zblink 1s steps(1) infinite' }} />
        )}
      </div>

      {/* waveform */}
      <div style={{ height: 30, display: 'flex', alignItems: 'center', gap: 4, marginTop: 4 }}>
        {speaking && bars.map((w, i) => (
          <div key={i} style={{ width: 4, height: 26, borderRadius: 2, background: 'var(--zac, #35E0FF)', boxShadow: '0 0 6px rgba(53,224,255,.6)', transformOrigin: 'center', animation: `zbar ${w.dur} ease-in-out infinite`, animationDelay: w.delay }} />
        ))}
      </div>
    </div>
  )
}
