import React from 'react'
import TopBar from './components/TopBar.jsx'
import TodayBlocks from './components/TodayBlocks.jsx'
import AgentStatus from './components/AgentStatus.jsx'
import Core from './components/Core.jsx'
import Scoreboard from './components/Scoreboard.jsx'
import CutTrajectory from './components/CutTrajectory.jsx'
import Comms from './components/Comms.jsx'
import TMinus from './components/TMinus.jsx'
import BootOverlay from './components/BootOverlay.jsx'
import Architecture from './components/Architecture.jsx'

// Dash token: ?key=… in the URL (stored once), else localStorage, else vite env (dev).
function resolveToken() {
  try {
    const url = new URL(window.location.href)
    const key = url.searchParams.get('key')
    if (key) {
      localStorage.setItem('zarvis_token', key)
      url.searchParams.delete('key')
      window.history.replaceState({}, '', url.toString())
    }
    return localStorage.getItem('zarvis_token') || import.meta.env.VITE_DASH_TOKEN || ''
  } catch {
    return ''
  }
}

export default class ZarvisDashboard extends React.Component {
  constructor(props) {
    super(props)
    this.token = resolveToken()
    this.state = {
      now: Date.now(),
      view: 'hud',         // 'hud' | 'arch' — top-bar tab selects the main view
      live: null,          // /api/state payload; null = demo fallback
      commsLoaded: false,
      booting: true,
      bootFading: false,
      bootN: 0,
      voiceLine: '',
      speaking: false,
      input: '',
      toolsUsed: 3,
      messages: [
        { who: 'ZARVIS', time: '07:00', text: "Morning, Zaki. Three blocks today — recruiting 12:30, gym 18:30, build 20:45 (Jarvis Phase 0).\nOutreach sits at 14/25. Five today keeps you green. That's the only ask." },
        { who: 'ZAKI', time: '07:41', text: 'on it. gym after work, build block is botfather setup + send_message' },
        { who: 'ZARVIS', time: '07:41', text: "Logged. I'll ask about all three at 21:00. Ship ugly." }
      ]
    }
    this.feedRef = React.createRef()
    this.timers = []
    this.bars = Array.from({ length: 26 }, (_, i) => ({
      dur: (0.7 + ((i * 7) % 5) * 0.12).toFixed(2) + 's',
      delay: ((i * 53) % 90) / 100 + 's'
    }))
    this.bootLines = [
      'ZARVIS v0.1 :: boot sequence initiated',
      'loading procedural memory .... plan.md ✓  personality.md ✓',
      'loading semantic memory ...... facts.md ✓',
      'episodic log ................. SQLite · 47 check-ins',
      'telegram uplink .............. SECURE · chat_id allowlisted',
      'calendar sync ................ zakikhan.contact ✓',
      'guardrails ................... ARMED · max 5 tool calls · 90s timeout',
      'ALL SYSTEMS NOMINAL'
    ]
    this.replyCycle = 0
  }

  fetchState = async () => {
    try {
      const r = await fetch('/api/state', { headers: { 'X-Dash-Token': this.token } })
      if (!r.ok) return
      const live = await r.json()
      // Real numbers into the boot sequence (only visible if it hasn't finished yet).
      this.bootLines[3] = `episodic log ................. LIVE DB · ${live.checkin_count} check-ins`
      this.bootLines[5] = live.blocks_source === 'google'
        ? 'calendar sync ................ google · LIVE ✓'
        : 'calendar sync ................ template fallback'
      this.setState(s => {
        const next = { live }
        if (!s.commsLoaded && live.comms && live.comms.length) {
          next.messages = live.comms.map(m => ({ who: m.who, time: m.time, text: m.text }))
          next.commsLoaded = true
        }
        if (live.last_run) next.toolsUsed = Math.min(5, live.last_run.tools_used ?? 0)
        return next
      })
    } catch { /* backend offline -> stay in demo mode */ }
  }

  componentDidMount() {
    this.fetchState()
    this.timers.push(setInterval(this.fetchState, 60000))
    this.timers.push(setInterval(() => this.setState({ now: Date.now() }), 1000))
    if ((this.props.boot ?? true) === false) {
      this.setState({ booting: false })
      this.timers.push(setTimeout(() => this.greet(), 300))
      return
    }
    const step = () => {
      this.setState(s => {
        const n = s.bootN + 1
        if (n >= this.bootLines.length) {
          this.timers.push(setTimeout(() => this.setState({ bootFading: true }), 650))
          this.timers.push(setTimeout(() => { this.setState({ booting: false }); this.greet() }, 1250))
        } else {
          this.timers.push(setTimeout(step, 240))
        }
        return { bootN: n }
      })
    }
    this.timers.push(setTimeout(step, 500))
  }

  componentWillUnmount() {
    this.timers.forEach(t => { clearTimeout(t); clearInterval(t) })
    if (this.typer) clearInterval(this.typer)
  }

  componentDidUpdate() {
    const el = this.feedRef.current
    if (el) el.scrollTop = el.scrollHeight
  }

  skipBoot = () => {
    this.timers.forEach(t => { clearTimeout(t) })
    this.timers = [this.timers[0]].filter(Boolean)
    this.timers.push(setInterval(() => this.setState({ now: Date.now() }), 1000))
    this.setState({ booting: false, bootN: this.bootLines.length })
    this.greet()
  }

  greet() {
    const h = new Date().getHours()
    const tod = h < 12 ? 'Morning' : h < 18 ? 'Afternoon' : 'Evening'
    const live = this.state.live
    if (live && live.scoreboard) {
      const hit = Object.values(live.scoreboard).filter(m => m.value >= m.target).length
      const name = live.user || 'Zaki'
      this.typeVoice(`${tod}, ${name}. Systems online — live uplink to the real database. ${hit} of 6 metrics hit this week. Blocks are loaded below. Let's have a green week.`)
    } else {
      this.typeVoice(tod + ", Zaki. Systems online. Running on demo data — backend uplink not found. Start the API to go live.")
    }
  }

  typeVoice(text) {
    if (this.typer) clearInterval(this.typer)
    this.setState({ voiceLine: '', speaking: true })
    let i = 0
    this.typer = setInterval(() => {
      i++
      this.setState({ voiceLine: text.slice(0, i) })
      if (i >= text.length) {
        clearInterval(this.typer)
        this.timers.push(setTimeout(() => this.setState({ speaking: false }), 900))
      }
    }, 26)
  }

  nowTime() {
    const d = new Date()
    return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
  }

  reply(t) {
    const s = t.toLowerCase()
    if (s.includes('gym') || s.includes('lift')) return 'Logged. Lifts move to 4/5 — one more and that metric goes green. PPL waits for no one.'
    if (s.includes('outreach')) return 'Logged. Outreach climbs toward 25. At a 10–15% reply rate, conversations are already in the mail.'
    if (s.includes('clay')) return "Good. Table + 90-sec Loom + ONE question to a named person. Friday 17:15 — I'll hold you to it."
    if (s.includes('status')) return '4 of 6 on pace. Outreach 14/25, Clay table open, lifts 3/5. 90 days to the EY decision — pipeline beats panic.'
    if (s.includes('steps')) return 'Logged. Average holding at 9.2k — a 20-minute walk tonight clears the 10k floor.'
    if (s.includes('weight') || s.includes('weigh')) return '164.6 this morning. Down 0.4 from start, right on the −1 lb/wk line. Boring and effective.'
    const pool = [
      "Filed to episodic memory. Sunday's review will remember this.",
      'Noted and logged. Check-in at 21:00 — bring numbers, not vibes.',
      "On it. If it's not on the calendar it doesn't exist — want me to flag it for tonight?"
    ]
    return pool[this.replyCycle++ % pool.length]
  }

  send = () => {
    const t = this.state.input.trim()
    if (!t || this.chatTyping) return
    const who = (this.state.live && this.state.live.user ? this.state.live.user : 'ZAKI').toUpperCase()
    this.setState(s => ({ messages: [...s.messages, { who, time: this.nowTime(), text: t }], input: '' }))
    if (this.state.live) {
      // Live uplink: the real agent (LangGraph + tools) answers.
      fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Dash-Token': this.token },
        body: JSON.stringify({ text: t })
      })
        .then(r => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
        .then(({ reply }) => { this.typeChat(reply); this.fetchState() })
        .catch(() => this.typeChat('Uplink hiccup — that one did not reach the mainframe. Try again.'))
      return
    }
    const r = this.reply(t)
    this.timers.push(setTimeout(() => this.typeChat(r), 650))
  }

  typeChat(text) {
    this.chatTyping = true
    this.setState(s => ({ speaking: true, messages: [...s.messages, { who: 'ZARVIS', time: this.nowTime(), text: '' }] }))
    let i = 0
    const iv = setInterval(() => {
      i += 2
      this.setState(s => {
        const msgs = s.messages.slice()
        msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], text: text.slice(0, i) }
        return { messages: msgs }
      })
      if (i >= text.length) {
        clearInterval(iv)
        this.chatTyping = false
        this.timers.push(setTimeout(() => this.setState({ speaking: false }), 800))
      }
    }, 24)
    this.timers.push(iv)
  }

  onInput = (e) => this.setState({ input: e.target.value })
  onKey = (e) => { if (e.key === 'Enter') this.send() }
  setView = (view) => this.setState({ view })

  renderVals() {
    const accent = this.props.accent ?? '#35E0FF'
    const d = new Date(this.state.now)
    const pad = n => String(n).padStart(2, '0')
    const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    const timeStr = pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
    const dateStr = days[d.getDay()] + ' · ' + months[d.getMonth()] + ' ' + pad(d.getDate()) + ' · ' + d.getFullYear()

    const live = this.state.live

    // ---- today's blocks: live Google Calendar via /api/state, else SUMMER_PLAN weekly template ----
    const dow = d.getDay()
    const mins = d.getHours() * 60 + d.getMinutes()
    let defs = []
    if (live && live.blocks && live.blocks.length) {
      defs = live.blocks.map(b => {
        const times = (b.time.match(/(\d{1,2}):(\d{2})/g) || []).map(t => {
          const [h, m] = t.split(':').map(Number)
          return h * 60 + m
        })
        const start = times.length ? times[0] : 0
        const end = times.length > 1 ? times[1] : (times.length ? start + 60 : 1440)
        return { time: b.time, name: b.name.toUpperCase(), start, end }
      })
    } else if (dow >= 1 && dow <= 5) {
      defs.push({ time: '12:30–13:00', name: '🎯 RECRUITING BLOCK', sub: '5 outreaches', start: 750, end: 780 })
      defs.push({ time: '18:30–20:00', name: '💪 GYM · PPL', start: 1110, end: 1200 })
      if (dow === 2 || dow === 4) defs.push({ time: '20:45–22:45', name: '🛠️ BUILD BLOCK · JARVIS', start: 1245, end: 1365 })
      if (dow === 5) defs.push({ time: '17:15–18:00', name: '🧱 CLAY SEND RITUAL', start: 1035, end: 1080 })
    } else if (dow === 0) {
      defs = [
        { time: '10:00–14:00', name: '🧠 SUNDAY DEEP WORK', start: 600, end: 840 },
        { time: '17:00–17:30', name: '📊 WEEKLY REVIEW', start: 1020, end: 1050 },
        { time: '18:00–19:30', name: '🍗 MEAL PREP', start: 1080, end: 1170 }
      ]
    } else if (dow === 6) {
      defs = [{ time: 'ALL DAY', name: 'SOCIAL / FLEX — GUILT-FREE', start: 0, end: 1440 }]
    }
    const blocks = defs.map(b => {
      const done = mins > b.end, active = mins >= b.start && mins <= b.end
      return {
        time: b.time,
        name: b.name,
        status: active ? '▶ ACTIVE' : done ? '✓ CLEARED' : 'QUEUED',
        statusColor: active ? accent : done ? '#7CFFA9' : 'rgba(140,190,215,.5)',
        timeColor: active ? accent : 'rgba(160,210,235,.75)',
        borderColor: active ? accent : 'rgba(53,224,255,.14)',
        bg: active ? 'rgba(53,224,255,.08)' : 'rgba(53,224,255,.03)',
        opacity: done ? '0.5' : '1'
      }
    })
    const blockNote = dow === 6 ? 'RULE 5 · EVENT DAYS: ENJOY FULLY, RESUME NEXT MORNING' : 'RULE 3 · RECRUITING BLOCK IS SACRED — OUTREACH BEFORE BUILD'

    // ---- agent runs ----
    const morning = 7 * 60, evening = 21 * 60
    let lastRun, nextRun
    const toNext = target => {
      let dm = target - mins; if (dm <= 0) dm += 1440
      return 'T−' + pad(Math.floor(dm / 60)) + ':' + pad(dm % 60)
    }
    if (mins < morning) { lastRun = 'YESTERDAY 21:00 · EVENING ✓'; nextRun = '07:00 MORNING · ' + toNext(morning) }
    else if (mins < evening) { lastRun = '07:00 · MORNING NUDGE ✓'; nextRun = '21:00 CHECK-IN · ' + toNext(evening) }
    else { lastRun = '21:00 · CHECK-IN ✓'; nextRun = '07:00 MORNING · ' + toNext(morning) }
    if (live && live.last_run) {
      const lr = new Date(live.last_run.ts)
      lastRun = String(lr.getHours()).padStart(2, '0') + ':' + String(lr.getMinutes()).padStart(2, '0') +
        ' · ' + live.last_run.type.toUpperCase() + ' ✓'
    }

    const used = this.state.toolsUsed
    const toolSegs = Array.from({ length: 5 }, (_, i) => i < used
      ? { bg: accent, border: accent, glow: '0 0 8px rgba(53,224,255,.6)' }
      : { bg: 'rgba(53,224,255,.06)', border: 'rgba(53,224,255,.25)', glow: 'none' })

    const guards = [
      { name: 'end-loop · message_sent', state: 'ARMED', color: '#7CFFA9' },
      { name: 'hard rail · max 5 tool calls', state: 'ARMED', color: '#7CFFA9' },
      { name: 'timeout · 90s fallback', state: 'ARMED', color: '#7CFFA9' },
      { name: 'chat_id allowlist', state: 'LOCKED', color: accent },
      { name: 'fail-loud · telegram alert', state: 'ON', color: '#7CFFA9' }
    ]

    // ---- scoreboard ----
    const mk = (name, val, pct, status, tone) => ({
      name, val, width: Math.min(100, Math.round(pct * 100)) + '%', status,
      statusColor: tone, barColor: tone
    })
    const green = '#7CFFA9', amber = '#FFC14D'
    let metrics, onPaceLabel
    if (live && live.scoreboard) {
      const NAMES = {
        outreach: 'OUTREACH SENT', calls: 'CALLS BOOKED', clay: 'CLAY TABLE',
        lifts: 'LIFTS · PPL', steps: 'STEPS AVG', milestone: 'JARVIS MILESTONE'
      }
      const kfmt = n => n >= 1000 ? (n / 1000).toFixed(n % 1000 === 0 ? 0 : 1) + 'K' : String(Math.round(n * 10) / 10)
      metrics = Object.entries(NAMES).map(([key, name]) => {
        const m = live.scoreboard[key] || { value: 0, target: 1 }
        const pct = m.target > 0 ? m.value / m.target : 0
        const status = pct >= 1 ? 'HIT ✓' : pct >= 0.8 ? 'CLOSE' : pct > 0 ? 'ON PACE' : 'OPEN'
        const tone = pct >= 1 ? green : pct > 0 ? accent : amber
        return mk(name, `${kfmt(m.value)} / ${kfmt(m.target)}`, Math.max(pct, 0.02), status, tone)
      })
      const hit = metrics.filter(m => m.status === 'HIT ✓').length
      const ws = new Date(live.week_start + 'T12:00:00')
      onPaceLabel = 'WK OF ' + months[ws.getMonth()] + ' ' + pad(ws.getDate()) + ' · ' + hit + '/6 HIT · LIVE'
    } else {
      metrics = [
        mk('OUTREACH SENT', '14 / 25', 14 / 25, 'ON PACE', accent),
        mk('CALLS BOOKED', '2 / 3', 2 / 3, 'ON PACE', accent),
        mk('CLAY TABLE', '0 / 1', 0.04, 'DUE FRI', amber),
        mk('LIFTS · PPL', '3 / 5', 3 / 5, 'ON PACE', accent),
        mk('STEPS AVG', '9.2K / 10K', 0.92, 'CLOSE', accent),
        mk('JARVIS MILESTONE', '1 / 1', 1, 'HIT ✓', green)
      ]
      onPaceLabel = 'WK OF JUL 06 · 4/6 ON PACE · DEMO'
    }
    const weekSquares = metrics.map(m => m.status === 'HIT ✓'
      ? { bg: green, glow: '0 0 8px rgba(124,255,169,.6)' }
      : m.status === 'DUE FRI'
        ? { bg: 'rgba(255,193,77,.5)', glow: 'none' }
        : { bg: 'rgba(53,224,255,.35)', glow: 'none' })

    // ---- countdowns ----
    const cd = (label, y, mo, day, dateLabel) => {
      const t = Math.ceil((new Date(y, mo - 1, day).getTime() - this.state.now) / 86400000)
      return { label, days: t, tm: 'T−' + pad(Math.max(0, t)) + 'D', date: dateLabel }
    }
    const countdowns = [
      cd('SYSTEM GOES LIVE', 2026, 7, 6, 'MON JUL 06'),
      cd('JARVIS v0 SHIPS', 2026, 7, 12, 'SUN JUL 12 · ACCEPTANCE'),
      cd('AHMED & HUDA WEDDING', 2026, 7, 23, 'THU JUL 23 · LIGHT WEEK'),
      cd('CRUNCH ENDS · GYM GAP', 2026, 8, 1, 'SAT AUG 01'),
      cd('APPS OPEN · META RPM', 2026, 8, 24, '~LATE AUG'),
      cd('EY DECISION', 2026, 9, 30, 'END OF SEP · WITH LEVERAGE')
    ].filter(c => c.days >= 0).slice(0, 5).map((c, i) => ({ ...c, color: i === 0 ? accent : c.days <= 10 ? accent : 'rgba(190,230,250,.8)' }))

    // ---- messages ----
    const messages = this.state.messages.map(m => m.who === 'ZARVIS'
      ? { ...m, justify: 'flex-start', bg: 'rgba(53,224,255,.06)', border: 'rgba(53,224,255,.22)', whoColor: accent }
      : { ...m, justify: 'flex-end', bg: 'rgba(124,255,169,.05)', border: 'rgba(124,255,169,.2)', whoColor: green })

    // ---- boot ----
    const bootShown = this.bootLines.slice(0, this.state.bootN).map((t, i) => ({
      text: '> ' + t,
      color: i === this.bootLines.length - 1 ? accent : 'rgba(170,215,240,.75)'
    }))

    const C = 2 * Math.PI * 146
    return {
      accent,
      timeStr, dateStr,
      scanlines: this.props.scanlines ?? true,
      statusDots: [
        { label: live ? 'UPLINK · LIVE' : 'UPLINK · DEMO', color: live ? '#7CFFA9' : '#FFC14D' },
        { label: 'CAL', color: live && live.blocks_source === 'google' ? '#7CFFA9' : '#FFC14D' },
        { label: 'TRACE', color: accent }
      ],
      blocks, blockNote,
      lastRun, nextRun,
      toolLabel: used + ' / 5 LAST RUN',
      toolSegs, guards,
      promptVersion: live ? live.prompt_version : null,
      model: live ? live.model : null,
      langfuse: live ? live.langfuse : false,
      metrics, onPaceLabel, weekSquares,
      countdowns,
      messages,
      input: this.state.input,
      onInput: this.onInput, onKey: this.onKey, send: this.send,
      feedRef: this.feedRef,
      voiceLine: this.state.voiceLine,
      speaking: this.state.speaking,
      bars: this.bars,
      weekLabel: 'SETUP / 12',
      coreStatus: this.state.speaking ? '● SPEAKING' : 'ONLINE',
      ringDash: (C * 4 / 6).toFixed(0) + ' ' + C.toFixed(0),
      booting: this.state.booting,
      bootAnim: this.state.bootFading ? 'zfadeout .55s ease forwards' : 'none',
      bootShown,
      skipBoot: this.skipBoot
    }
  }

  render() {
    const v = this.renderVals()
    return (
      <div style={{ '--zac': v.accent, position: 'fixed', inset: 0, background: 'radial-gradient(ellipse 120% 90% at 50% 40%, #081420 0%, #04090f 55%, #02050a 100%)', color: '#cfeeff', fontFamily: "'Rajdhani',sans-serif", overflow: 'hidden' }}>

        {/* ambient grid */}
        <div style={{ position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(rgba(53,224,255,.03) 1px, transparent 1px),linear-gradient(90deg, rgba(53,224,255,.03) 1px, transparent 1px)', backgroundSize: '44px 44px', pointerEvents: 'none' }} />
        {v.scanlines && (
          <>
            <div style={{ position: 'absolute', inset: 0, background: 'repeating-linear-gradient(0deg, rgba(0,0,0,.13) 0px, rgba(0,0,0,.13) 1px, transparent 1px, transparent 3px)', pointerEvents: 'none', zIndex: 40 }} />
            <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 90, background: 'linear-gradient(180deg, transparent, rgba(53,224,255,.05), transparent)', animation: 'scanmove 9s linear infinite', pointerEvents: 'none', zIndex: 40 }} />
          </>
        )}
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 90% 80% at 50% 50%, transparent 55%, rgba(0,0,0,.55) 100%)', pointerEvents: 'none', zIndex: 41 }} />

        {/* ===== MAIN GRID ===== */}
        <div style={{ position: 'absolute', inset: 0, display: 'grid', gridTemplateColumns: '390px 1fr 390px', gridTemplateRows: '56px 1fr 244px', gap: 14, padding: 16, zIndex: 1 }}>

          <TopBar timeStr={v.timeStr} dateStr={v.dateStr} statusDots={v.statusDots} view={this.state.view} onView={this.setView} />

          {/* LEFT COLUMN */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, minHeight: 0 }}>
            <TodayBlocks blocks={v.blocks} blockNote={v.blockNote} />
            <AgentStatus lastRun={v.lastRun} nextRun={v.nextRun} toolLabel={v.toolLabel} toolSegs={v.toolSegs} guards={v.guards} promptVersion={v.promptVersion} model={v.model} langfuse={v.langfuse} />
          </div>

          <Core weekLabel={v.weekLabel} ringDash={v.ringDash} coreStatus={v.coreStatus} speaking={v.speaking} voiceLine={v.voiceLine} bars={v.bars} />

          {/* RIGHT COLUMN */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, minHeight: 0 }}>
            <Scoreboard metrics={v.metrics} onPaceLabel={v.onPaceLabel} weekSquares={v.weekSquares} />
            <CutTrajectory weights={this.state.live ? this.state.live.weights : null} />
          </div>

          <Comms messages={v.messages} input={v.input} onInput={v.onInput} onKey={v.onKey} send={v.send} feedRef={v.feedRef} />

          <TMinus countdowns={v.countdowns} />
        </div>

        {/* ===== ARCHITECTURE VIEW (top-bar tab) ===== */}
        {this.state.view === 'arch' && <Architecture />}

        {/* ===== BOOT OVERLAY ===== */}
        {v.booting && <BootOverlay bootShown={v.bootShown} bootAnim={v.bootAnim} skipBoot={v.skipBoot} />}
      </div>
    )
  }
}
