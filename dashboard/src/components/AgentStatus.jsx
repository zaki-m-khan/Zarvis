const mono = "'Share Tech Mono',monospace"

export default function AgentStatus({ lastRun, nextRun, toolLabel, toolSegs, guards }) {
  return (
    <div className="panel" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', background: 'linear-gradient(180deg, rgba(13,26,38,.7), rgba(7,14,22,.85))', border: '1px solid rgba(53,224,255,.18)', borderRadius: 6, padding: '16px 18px', position: 'relative', animation: 'panelin .5s ease .25s both' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 12 }}>
        <div style={{ fontWeight: 700, fontSize: 13, letterSpacing: 3.5, color: 'var(--zac, #35E0FF)' }}>◢ AGENT STATUS</div>
        <div style={{ fontFamily: mono, fontSize: 10, color: '#7CFFA9', letterSpacing: 1 }}>● NOMINAL</div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 14px', marginBottom: 12 }}>
        <div>
          <div style={{ fontFamily: mono, fontSize: 9.5, letterSpacing: 1.5, color: 'rgba(140,190,215,.5)' }}>LAST RUN</div>
          <div style={{ fontFamily: mono, fontSize: 13, color: '#dff4ff', marginTop: 2 }}>{lastRun}</div>
        </div>
        <div>
          <div style={{ fontFamily: mono, fontSize: 9.5, letterSpacing: 1.5, color: 'rgba(140,190,215,.5)' }}>NEXT RUN</div>
          <div style={{ fontFamily: mono, fontSize: 13, color: 'var(--zac, #35E0FF)', marginTop: 2 }}>{nextRun}</div>
        </div>
      </div>
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
          <span style={{ fontFamily: mono, fontSize: 9.5, letterSpacing: 1.5, color: 'rgba(140,190,215,.5)' }}>TOOL CALLS · HARD RAIL 5</span>
          <span style={{ fontFamily: mono, fontSize: 10, color: 'rgba(160,210,235,.7)' }}>{toolLabel}</span>
        </div>
        <div style={{ display: 'flex', gap: 5 }}>
          {toolSegs.map((t, i) => (
            <div key={i} style={{ flex: 1, height: 8, borderRadius: 2, background: t.bg, border: `1px solid ${t.border}`, boxShadow: t.glow }} />
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 5, overflowY: 'auto', minHeight: 0 }}>
        {guards.map(g => (
          <div key={g.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontFamily: mono, fontSize: 10.5, color: 'rgba(180,220,240,.75)', letterSpacing: '.5px' }}>{g.name}</span>
            <span style={{ fontFamily: mono, fontSize: 9.5, letterSpacing: 1.5, color: g.color }}>{g.state}</span>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 'auto', paddingTop: 10, display: 'flex', gap: 14, borderTop: '1px solid rgba(53,224,255,.12)' }}>
        <span style={{ fontFamily: mono, fontSize: 9.5, color: 'rgba(140,190,215,.5)', letterSpacing: 1 }}>PROMPT v1</span>
        <span style={{ fontFamily: mono, fontSize: 9.5, color: 'rgba(140,190,215,.5)', letterSpacing: 1 }}>SONNET-4-6</span>
        <span style={{ fontFamily: mono, fontSize: 9.5, color: 'rgba(140,190,215,.5)', letterSpacing: 1 }}>LANGFUSE ●</span>
      </div>
    </div>
  )
}
