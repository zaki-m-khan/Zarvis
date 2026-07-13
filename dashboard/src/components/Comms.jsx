const mono = "'Share Tech Mono',monospace"

export default function Comms({ messages, input, onInput, onKey, send, feedRef }) {
  return (
    <div className="panel" style={{ gridColumn: '1 / 3', display: 'flex', flexDirection: 'column', background: 'linear-gradient(180deg, rgba(13,26,38,.7), rgba(7,14,22,.85))', border: '1px solid rgba(53,224,255,.18)', borderRadius: 6, padding: '14px 18px', minHeight: 0, position: 'relative', animation: 'panelin .5s ease .35s both' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
        <div style={{ fontWeight: 700, fontSize: 13, letterSpacing: 3.5, color: 'var(--zac, #35E0FF)' }}>◢ COMMS · TELEGRAM UPLINK</div>
        <div style={{ fontFamily: mono, fontSize: 10, color: 'rgba(140,190,215,.5)', letterSpacing: 1 }}>CHAT_ID ALLOWLISTED · SECURE</div>
      </div>
      <div ref={feedRef} style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 7, minHeight: 0, paddingRight: 6 }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: msg.justify }}>
            <div style={{ maxWidth: '64%', padding: '7px 12px', borderRadius: 4, background: msg.bg, border: `1px solid ${msg.border}` }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'baseline', marginBottom: 2 }}>
                <span style={{ fontFamily: mono, fontSize: 9, letterSpacing: 2, color: msg.whoColor }}>{msg.who}</span>
                <span style={{ fontFamily: mono, fontSize: 9, color: 'rgba(140,190,215,.4)' }}>{msg.time}</span>
              </div>
              <div style={{ fontFamily: mono, fontSize: 12.5, lineHeight: 1.5, color: '#dff4ff', whiteSpace: 'pre-wrap' }}>{msg.text}</div>
            </div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <input
          className="zinput"
          value={input}
          onChange={onInput}
          onKeyDown={onKey}
          placeholder="Talk to ZARVIS — try 'status', 'log gym', 'log 5 outreach'…"
          style={{ flex: 1, background: 'rgba(4,10,16,.8)', border: '1px solid rgba(53,224,255,.3)', borderRadius: 4, padding: '10px 14px', color: '#eaf9ff', fontFamily: mono, fontSize: 13, outline: 'none', letterSpacing: '.5px' }}
        />
        <button
          className="zsend"
          onClick={send}
          style={{ background: 'rgba(53,224,255,.12)', border: '1px solid var(--zac, #35E0FF)', borderRadius: 4, padding: '0 26px', color: 'var(--zac, #35E0FF)', fontFamily: "'Rajdhani',sans-serif", fontWeight: 700, fontSize: 14, letterSpacing: 3, cursor: 'pointer' }}
        >SEND</button>
      </div>
    </div>
  )
}
