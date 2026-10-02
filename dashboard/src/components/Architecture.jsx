import React, { useState } from 'react'

const mono = "'Share Tech Mono',monospace"
const svgStyle = "width:100%;height:auto;max-height:100%;display:block;color:#d9efff;font-family:'Share Tech Mono',monospace"

// Two hand-authored diagrams, injected as raw SVG so the exact markup (hyphenated
// SVG attrs) is reused verbatim. Static content, no interpolation.
const TOPOLOGY = `
<svg viewBox="0 0 880 470" role="img" aria-label="System topology: a cron scheduler and the phone both trigger the FastAPI server on Render; inside it the agent calls the model, reads the calendar, reads and writes Supabase, and sends to Telegram." style="${svgStyle}">
  <defs>
    <marker id="ar" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="currentColor"/></marker>
    <marker id="arc" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#35e0ff"/></marker>
  </defs>
  <g>
    <rect x="24" y="66" width="156" height="68" rx="7" fill="rgba(53,224,255,.05)" stroke="rgba(53,224,255,.34)"/>
    <text x="102" y="94" text-anchor="middle" font-size="13" fill="currentColor">YOUR PHONE</text>
    <text x="102" y="113" text-anchor="middle" font-size="11" fill="rgba(176,214,236,.8)">Telegram</text>
    <rect x="24" y="300" width="156" height="68" rx="7" fill="rgba(53,224,255,.03)" stroke="rgba(53,224,255,.2)"/>
    <text x="102" y="328" text-anchor="middle" font-size="12" fill="currentColor">GITHUB ACTIONS</text>
    <text x="102" y="347" text-anchor="middle" font-size="11" fill="rgba(176,214,236,.8)">cron scheduler</text>
  </g>
  <rect x="258" y="40" width="286" height="388" rx="10" fill="rgba(53,224,255,.03)" stroke="rgba(53,224,255,.2)" stroke-dasharray="3 4"/>
  <text x="272" y="62" font-size="12" fill="#35e0ff" letter-spacing="1">FastAPI &middot; Render</text>
  <g font-size="10.5" fill="rgba(176,214,236,.8)">
    <text x="272" y="88">/webhook/telegram</text>
    <text x="272" y="105">/api/run/&#123;morning|evening|sunday&#125;</text>
    <text x="272" y="122">/api/state &middot; /api/chat</text>
  </g>
  <rect x="286" y="188" width="230" height="86" rx="8" fill="rgba(53,224,255,.08)" stroke="#35e0ff" stroke-width="1.5"/>
  <text x="401" y="216" text-anchor="middle" font-size="14" fill="#eaf9ff" letter-spacing="1">THE AGENT</text>
  <text x="401" y="235" text-anchor="middle" font-size="10.5" fill="#35e0ff">LangGraph loop</text>
  <text x="401" y="252" text-anchor="middle" font-size="10.5" fill="rgba(176,214,236,.8)">memory + scoreboard + rails</text>
  <rect x="300" y="300" width="202" height="46" rx="7" fill="rgba(53,224,255,.04)" stroke="rgba(53,224,255,.2)"/>
  <text x="401" y="322" text-anchor="middle" font-size="12" fill="currentColor">ZARVIS HUD</text>
  <text x="401" y="338" text-anchor="middle" font-size="10" fill="rgba(176,214,236,.8)">live dashboard</text>
  <g>
    <rect x="712" y="120" width="150" height="56" rx="7" fill="rgba(53,224,255,.05)" stroke="rgba(53,224,255,.34)"/>
    <text x="787" y="144" text-anchor="middle" font-size="12" fill="currentColor">gpt-5.4-mini</text>
    <text x="787" y="162" text-anchor="middle" font-size="10" fill="rgba(176,214,236,.8)">the model</text>
    <rect x="712" y="208" width="150" height="56" rx="7" fill="rgba(53,224,255,.04)" stroke="rgba(53,224,255,.2)"/>
    <text x="787" y="232" text-anchor="middle" font-size="12" fill="currentColor">Google Calendar</text>
    <text x="787" y="250" text-anchor="middle" font-size="10" fill="rgba(176,214,236,.8)">today's blocks</text>
    <rect x="712" y="296" width="150" height="70" rx="7" fill="rgba(53,224,255,.04)" stroke="rgba(53,224,255,.2)"/>
    <text x="787" y="320" text-anchor="middle" font-size="12" fill="currentColor">Supabase</text>
    <text x="787" y="338" text-anchor="middle" font-size="9.5" fill="rgba(176,214,236,.8)">checkins &middot; scoreboard</text>
    <text x="787" y="352" text-anchor="middle" font-size="9.5" fill="rgba(176,214,236,.8)">users &middot; facts</text>
  </g>
  <g font-size="10">
    <line x1="182" y1="90" x2="256" y2="90" stroke="#35e0ff" marker-end="url(#arc)"/>
    <text x="219" y="82" text-anchor="middle" fill="#35e0ff">texts in</text>
    <line x1="256" y1="116" x2="182" y2="116" stroke="currentColor" opacity=".7" marker-end="url(#ar)"/>
    <text x="219" y="130" text-anchor="middle" fill="rgba(176,214,236,.8)">sends out</text>
    <line x1="182" y1="330" x2="256" y2="330" stroke="currentColor" marker-end="url(#ar)"/>
    <text x="219" y="322" text-anchor="middle" fill="rgba(176,214,236,.8)">curl</text>
    <text x="150" y="388" text-anchor="start" fill="rgba(150,196,222,.62)">7:00a &middot; 9:00p &middot; Sun 4:30p</text>
    <line x1="518" y1="205" x2="710" y2="150" stroke="#35e0ff" marker-start="url(#arc)" marker-end="url(#arc)"/>
    <text x="612" y="168" text-anchor="middle" fill="#35e0ff">tool-calling</text>
    <line x1="518" y1="232" x2="710" y2="234" stroke="currentColor" marker-end="url(#ar)"/>
    <text x="614" y="226" text-anchor="middle" fill="rgba(176,214,236,.8)">read</text>
    <line x1="518" y1="258" x2="710" y2="322" stroke="currentColor" marker-start="url(#ar)" marker-end="url(#ar)"/>
    <text x="612" y="303" text-anchor="middle" fill="rgba(176,214,236,.8)">read / write</text>
    <line x1="401" y1="274" x2="401" y2="298" stroke="currentColor" opacity=".6" marker-end="url(#ar)"/>
  </g>
</svg>`

const LOOP = `
<svg viewBox="0 0 760 410" role="img" aria-label="Agent loop: a message enters the agent; it either replies and ends, calls a tool and loops, or exceeds five calls and hits the limit rail." style="${svgStyle}">
  <defs>
    <marker id="lar" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7.5" markerHeight="7.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="currentColor"/></marker>
    <marker id="larc" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#35e0ff"/></marker>
    <marker id="larg" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7.5" markerHeight="7.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#7cffa9"/></marker>
    <marker id="lara" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7.5" markerHeight="7.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#ffc14d"/></marker>
  </defs>
  <text x="380" y="26" text-anchor="middle" font-size="11" fill="rgba(176,214,236,.8)">message in  (nudge trigger, or your text)</text>
  <line x1="380" y1="34" x2="380" y2="62" stroke="currentColor" marker-end="url(#lar)"/>
  <rect x="268" y="64" width="224" height="60" rx="8" fill="rgba(53,224,255,.09)" stroke="#35e0ff" stroke-width="1.5"/>
  <text x="380" y="90" text-anchor="middle" font-size="14" fill="#eaf9ff">AGENT</text>
  <text x="380" y="109" text-anchor="middle" font-size="10.5" fill="rgba(176,214,236,.8)">model reads memory, decides next move</text>
  <rect x="70" y="250" width="200" height="60" rx="8" fill="rgba(53,224,255,.05)" stroke="rgba(53,224,255,.34)"/>
  <text x="170" y="276" text-anchor="middle" font-size="13" fill="currentColor">TOOLS</text>
  <text x="170" y="295" text-anchor="middle" font-size="10" fill="rgba(176,214,236,.8)">run it, return the result</text>
  <g font-size="10.5" fill="#35e0ff" text-anchor="middle">
    <text x="170" y="334">read_calendar</text>
    <text x="170" y="352">read_scoreboard</text>
    <text x="170" y="370">log_checkin</text>
  </g>
  <rect x="556" y="232" width="164" height="56" rx="8" fill="rgba(124,255,169,.08)" stroke="#7cffa9" stroke-width="1.4"/>
  <text x="638" y="256" text-anchor="middle" font-size="13" fill="#bfffd6">END</text>
  <text x="638" y="274" text-anchor="middle" font-size="10" fill="#7cffa9">reply &#8594; Telegram</text>
  <rect x="296" y="330" width="188" height="52" rx="8" fill="rgba(255,193,77,.07)" stroke="#ffc14d" stroke-width="1.3"/>
  <text x="390" y="352" text-anchor="middle" font-size="12" fill="#ffd98a">LIMIT RAIL</text>
  <text x="390" y="369" text-anchor="middle" font-size="9.5" fill="#ffc14d">canned fallback message</text>
  <g font-size="10.5">
    <path d="M300 124 C240 165, 190 200, 173 248" fill="none" stroke="#35e0ff" marker-end="url(#larc)"/>
    <text x="196" y="186" text-anchor="middle" fill="#35e0ff">calls a tool</text>
    <path d="M470 118 C540 150, 600 185, 630 230" fill="none" stroke="#7cffa9" marker-end="url(#larg)"/>
    <text x="588" y="170" text-anchor="middle" fill="#7cffa9">reply ready</text>
    <path d="M388 124 C388 210, 389 270, 389 328" fill="none" stroke="#ffc14d" stroke-dasharray="5 4" marker-end="url(#lara)"/>
    <text x="446" y="210" text-anchor="middle" fill="#ffc14d">&gt; 5 tool calls</text>
    <path d="M200 248 C230 180, 250 150, 288 124" fill="none" stroke="#35e0ff" stroke-width="2" marker-end="url(#larc)"/>
    <text x="300" y="150" text-anchor="start" fill="#35e0ff">result &#8594; think again</text>
    <path d="M484 352 C540 345, 575 320, 600 290" fill="none" stroke="#ffc14d" stroke-dasharray="5 4" marker-end="url(#larg)"/>
  </g>
</svg>`

function Toggle({ label, on, onClick }) {
  return (
    <button onClick={onClick} style={{
      fontFamily: mono, fontSize: 11, letterSpacing: 1.5, cursor: 'pointer', padding: '7px 16px', borderRadius: 5,
      border: '1px solid ' + (on ? 'var(--zac,#35E0FF)' : 'rgba(53,224,255,.22)'),
      background: on ? 'rgba(53,224,255,.15)' : 'transparent',
      color: on ? '#eaf9ff' : 'rgba(160,210,235,.68)'
    }}>{label}</button>
  )
}

export default function Architecture() {
  const [tab, setTab] = useState('connect')
  const svg = tab === 'connect' ? TOPOLOGY : LOOP
  return (
    <div style={{
      position: 'absolute', top: 86, left: 16, right: 16, bottom: 16, zIndex: 45,
      display: 'flex', flexDirection: 'column',
      // fully opaque base (solid gradient) + faint grid on top, so the HUD behind never bleeds through
      background: 'linear-gradient(rgba(53,224,255,.03) 1px, transparent 1px), linear-gradient(90deg, rgba(53,224,255,.03) 1px, transparent 1px), linear-gradient(180deg, #0b1a29 0%, #060f1a 100%)',
      backgroundSize: '44px 44px, 44px 44px, 100% 100%',
      border: '1px solid rgba(53,224,255,.22)', borderRadius: 8, padding: '16px 24px 18px',
      animation: 'panelin .4s ease both'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 12 }}>
        <div style={{ fontWeight: 700, fontSize: 15, letterSpacing: 3.5, color: 'var(--zac, #35E0FF)' }}>◢ SYSTEM ARCHITECTURE</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Toggle label="HOW IT CONNECTS" on={tab === 'connect'} onClick={() => setTab('connect')} />
          <Toggle label="THE AGENT LOOP" on={tab === 'loop'} onClick={() => setTab('loop')} />
        </div>
      </div>
      <div style={{ flex: 1, minHeight: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'auto' }}
           dangerouslySetInnerHTML={{ __html: svg }} />
      <div style={{ fontFamily: mono, fontSize: 12, letterSpacing: 0.4, color: 'rgba(150,196,222,.6)', textAlign: 'center', marginTop: 12 }}>
        {tab === 'connect'
          ? 'two triggers  →  one server  →  the agent reaches out to what it needs'
          : 'cyan = think → act → observe cycle   ·   green = normal exit   ·   amber = it can\'t run forever'}
      </div>
    </div>
  )
}
