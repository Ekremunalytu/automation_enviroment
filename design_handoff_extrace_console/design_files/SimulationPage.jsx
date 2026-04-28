/**
 * ExTrace — Simulation Page (v3)
 * Live sandbox run: progress plate, activity bars + risk strip, live ledger + inspector.
 */

const SIM_EVS = [
  { id:'s1', kind:'activation', summary:'onStartupFinished → github.copilot activated',               risk:'low',    ts:'14:11:02', t:0  },
  { id:'s2', kind:'network',    summary:'POST https://copilot-proxy.githubusercontent.com/v1/engines', risk:'high',   ts:'14:11:05', t:3  },
  { id:'s3', kind:'file',       summary:'Read ~/.config/gh/hosts.yml',                                risk:'medium', ts:'14:11:07', t:5  },
  { id:'s4', kind:'network',    summary:'GET https://api.github.com/copilot_internal/v2/token',       risk:'high',   ts:'14:11:09', t:7  },
  { id:'s5', kind:'activation', summary:'onDidOpenTextDocument fired for untitled-1.ts',               risk:'low',    ts:'14:11:13', t:11 },
  { id:'s6', kind:'file',       summary:'Write /tmp/extrace-sandbox/github.copilot-output.json',      risk:'low',    ts:'14:11:18', t:16 },
];
const S_RISK_TONE = { low:'ok', medium:'warn', high:'danger' };
const S_KIND_LABEL = { activation:'ACT', file:'FILE', network:'NET' };
const S_KIND_TONE = { activation:'accent', file:'neutral', network:'warn' };
const S_RISK_COLOR = { low:V2.ok, medium:V2.warn, high:V2.danger };

// Activity as stacked histogram over 20 bins ── cleaner, more deliberate
function ActivityBars({ pct, selectedId }) {
  const bars = [12,28,18,44,22,36,55,48,62,38,70,52,80,60,74,58,88,66,92,78];
  const filled = Math.floor((pct/100) * bars.length);
  const eventBars = { s1:0, s2:3, s3:5, s4:7, s5:11, s6:16 };
  const selBar = selectedId ? eventBars[selectedId] : null;
  const W = 520, H = 120, BW = 20;
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display:'block' }}>
      {/* baseline */}
      <line x1={0} y1={H-18} x2={W} y2={H-18} stroke={V2.rule2} strokeWidth="1"/>
      {bars.map((h, i) => {
        const bh = h * 0.85;
        const x = i * (BW+4) + 4;
        const y = H - 18 - bh;
        const isSel = selBar === i;
        const isFilled = i < filled;
        const fill = isSel ? V2.accent :
                     isFilled ? (i === filled - 1 ? V2.ink : V2.ink2) :
                     V2.rule2;
        return (
          <g key={i}>
            <rect x={x} y={y} width={BW} height={bh}
                  fill={fill} style={{ transition:'fill 200ms' }}/>
            {isSel && (
              <rect x={x-2} y={y-2} width={BW+4} height={bh+4}
                    fill="none" stroke={V2.accent} strokeWidth="1"/>
            )}
          </g>
        );
      })}
      {/* playhead marker */}
      {filled < bars.length && (
        <line x1={filled * (BW+4) + 4 + BW + 2} y1={6}
              x2={filled * (BW+4) + 4 + BW + 2} y2={H-14}
              stroke={V2.accent} strokeWidth="1" strokeDasharray="3 2"/>
      )}
    </svg>
  );
}

// Risk strip — ticks along a line
function RiskStrip({ events, selectedId, onSelect }) {
  const W=520, H=80, PAD=16;
  const maxT = Math.max(...events.map(e=>e.t),1);
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display:'block', overflow:'visible' }}>
      {/* baseline */}
      <line x1={PAD} y1={H-22} x2={W-PAD} y2={H-22} stroke={V2.rule2} strokeWidth="1"/>
      {/* time ticks */}
      {[0,0.5,1].map((p,i)=>{
        const x = PAD + p*(W-PAD*2);
        return (
          <g key={i}>
            <line x1={x} y1={H-25} x2={x} y2={H-19} stroke={V2.rule2} strokeWidth="1"/>
            <text x={x} y={H-6} textAnchor="middle" fontSize="9"
                  fill={V2.ink4} fontFamily="JetBrains Mono">
              {Math.round(p*maxT)}s
            </text>
          </g>
        );
      })}
      {events.map(ev => {
        const x = PAD + (ev.t/maxT)*(W-PAD*2);
        const sel = ev.id === selectedId;
        const col = S_RISK_COLOR[ev.risk];
        return (
          <g key={ev.id} onClick={()=>onSelect(sel?null:ev.id)} style={{ cursor:'pointer' }}>
            <line x1={x} y1={H-22} x2={x} y2={sel?10:24}
                  stroke={col} strokeWidth={sel?2:1} strokeOpacity={sel?1:0.7}/>
            {sel && (
              <>
                <rect x={x-16} y={0} width={32} height={14} fill={V2.ink}/>
                <text x={x} y={10} textAnchor="middle" fontSize="9"
                      fill={V2.paper} fontFamily="JetBrains Mono" fontWeight="500">
                  {ev.ts.slice(6)}
                </text>
              </>
            )}
            <circle cx={x} cy={H-22} r={sel?5:3.5} fill={col}
                    stroke={V2.paper} strokeWidth="1.5"/>
          </g>
        );
      })}
    </svg>
  );
}

function SimInspector({ event }) {
  if (!event) return (
    <div style={{ padding:'24px 16px', textAlign:'center' }}>
      <div className="stripes" style={{
        padding:'32px 16px', border:`1px dashed ${V2.rule2}`, borderRadius:2
      }}>
        <div className="mono" style={{ fontSize:11, color:V2.ink3, letterSpacing:'0.08em' }}>
          no selection
        </div>
        <div style={{ fontSize:13, color:V2.ink3, marginTop:8, lineHeight:1.6 }}>
          Click a dot on the risk strip or a row to inspect.
        </div>
      </div>
    </div>
  );
  return (
    <div style={{ padding:'4px 0' }}>
      <div style={{ padding:'4px 4px 12px' }}>
        <div className="eyebrow" style={{ marginBottom:8 }}>Evidence</div>
        <div className="mono" style={{
          fontSize:12.5, color:V2.ink, lineHeight:1.55, wordBreak:'break-all',
          padding:'10px 12px', background:V2.paper, border:`1px solid ${V2.rule}`,
          borderLeft:`2px solid ${S_RISK_COLOR[event.risk]}`
        }}>{event.summary}</div>
      </div>

      <KVRow k="id" v={event.id}/>
      <KVRow k="kind" v={<Badge tone={S_KIND_TONE[event.kind]}>{S_KIND_LABEL[event.kind]}</Badge>} mono={false}/>
      <KVRow k="risk" v={<span style={{ display:'inline-flex', alignItems:'center', gap:6 }}><RiskDot risk={event.risk}/><Badge tone={S_RISK_TONE[event.risk]}>{event.risk}</Badge></span>} mono={false}/>
      <KVRow k="timestamp" v={event.ts}/>
      <KVRow k="offset" v={`+${event.t}s`}/>

      <div style={{ marginTop:14, padding:'4px 4px' }}>
        <div className="eyebrow" style={{ marginBottom:8 }}>Attribution</div>
        <div className="mono" style={{
          fontSize:12, color:V2.ink2, lineHeight:1.7,
          padding:'10px 12px', background:V2.paper, border:`1px solid ${V2.rule}`
        }}>
          github.copilot<br/>
          scenario-{event.t < 8 ? '1':'2'} / trigger-loop<br/>
          kind: {event.kind}
        </div>
      </div>
    </div>
  );
}

function SimulationPage() {
  const [pct, setPct] = React.useState(62);
  const [selectedId, setSelectedId] = React.useState(null);
  const status = pct >= 99 ? 'completed' : 'running';

  React.useEffect(() => {
    if (pct >= 99) return;
    const id = setInterval(() => setPct(p => Math.min(p+1, 99)), 700);
    return () => clearInterval(id);
  }, [pct]);

  const selectedEvent = SIM_EVS.find(e => e.id === selectedId) || null;

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:40 }}>
      {/* ── HEADER ─────────────────────────────────────────────────── */}
      <header style={{
        display:'grid', gridTemplateColumns:'1fr auto', gap:24,
        alignItems:'flex-start',
        paddingBottom:24, borderBottom:`1px solid ${V2.rule2}`,
      }}>
        <div style={{ minWidth:0 }}>
          <Eyebrow num={1}>Simulation · live</Eyebrow>
          <PageTitle style={{ marginTop:14, fontSize:44, wordBreak:'break-word' }}>
            github.copilot
          </PageTitle>
          <div style={{ marginTop:14, display:'flex', gap:18, flexWrap:'wrap', alignItems:'center' }}>
            <span className="mono" style={{ fontSize:12, color:V2.ink2, fontWeight:500 }}>v1.214.0</span>
            <span style={{ width:1, height:12, background:V2.rule2 }}/>
            <span className="mono" style={{ fontSize:12, color:V2.ink3 }}>job-8f3a2c1</span>
            <span style={{ width:1, height:12, background:V2.rule2 }}/>
            <span style={{ display:'inline-flex', alignItems:'center', gap:6 }}>
              <span style={{
                width:8, height:8, borderRadius:'50%',
                background: status==='running' ? V2.accent : V2.ok,
                animation: status==='running' ? 'pulse 1.4s ease-in-out infinite' : 'none'
              }}/>
              <span className="mono" style={{ fontSize:12, color:V2.ink2 }}>
                {status}
              </span>
            </span>
            <span style={{ width:1, height:12, background:V2.rule2 }}/>
            <span className="mono" style={{ fontSize:12, color:V2.ink3 }}>{SIM_EVS.length} events</span>
          </div>
        </div>
        <div style={{ display:'flex', gap:8, paddingTop:14 }}>
          <GhostButton>Pause</GhostButton>
          <GhostButton>Abort</GhostButton>
        </div>
      </header>

      <style>{`@keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.3 } }`}</style>

      {/* ── PROGRESS PLATE ─────────────────────────────────────────── */}
      <section style={{
        border:`1px solid ${V2.rule}`, background:V2.card, borderRadius:2,
        padding:'20px 22px',
      }}>
        <div style={{
          display:'grid', gridTemplateColumns:'repeat(4, 1fr) auto',
          gap:24, alignItems:'center'
        }}>
          <div>
            <Eyebrow>Status</Eyebrow>
            <div className="mono" style={{ fontSize:14, color:V2.ink, marginTop:6, fontWeight:500 }}>{status}</div>
          </div>
          <div>
            <Eyebrow>Phase</Eyebrow>
            <div className="mono" style={{ fontSize:14, color:V2.ink, marginTop:6, fontWeight:500 }}>scenario-2 / trigger-loop</div>
          </div>
          <div>
            <Eyebrow>Last update</Eyebrow>
            <div className="mono" style={{ fontSize:14, color:V2.ink, marginTop:6, fontWeight:500 }}>14:11:18</div>
          </div>
          <div>
            <Eyebrow>Progress</Eyebrow>
            <div className="serif" style={{
              fontSize:28, color:V2.ink, marginTop:2, fontWeight:500,
              letterSpacing:'-0.02em', fontVariantNumeric:'tabular-nums'
            }}>{pct}<span style={{ fontSize:16, color:V2.ink3 }}>%</span></div>
          </div>
        </div>
        <div style={{ marginTop:18 }}>
          <ProgressBar pct={pct}/>
        </div>
      </section>

      {/* ── ACTIVITY + RISK ───────────────────────────────────────── */}
      <section style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
        <Panel num="02" label="Activity volume" right={
          <span className="mono" style={{ fontSize:10.5, color:V2.ink3 }}>events / sec</span>
        }>
          <ActivityBars pct={pct} selectedId={selectedId}/>
        </Panel>
        <Panel num="03" label="Risk distribution" right={
          <span className="mono" style={{ fontSize:10.5, color:V2.ink3 }}>by event</span>
        }>
          <RiskStrip events={SIM_EVS} selectedId={selectedId} onSelect={setSelectedId}/>
          <div style={{ display:'flex', gap:20, marginTop:12, paddingTop:12, borderTop:`1px solid ${V2.rule}` }}>
            {[['low',V2.ok],['medium',V2.warn],['high',V2.danger]].map(([r,c])=>(
              <div key={r} style={{ display:'flex', alignItems:'center', gap:6 }}>
                <span style={{ width:8, height:8, borderRadius:'50%', background:c }}/>
                <span className="mono" style={{ fontSize:10.5, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.1em' }}>{r}</span>
              </div>
            ))}
          </div>
        </Panel>
      </section>

      {/* ── LIVE LEDGER + INSPECTOR ───────────────────────────────── */}
      <section>
        <div style={{ marginBottom:16 }}>
          <Eyebrow num={4}>Live evidence</Eyebrow>
          <SectionTitle style={{ marginTop:10 }}>Events, streamed</SectionTitle>
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'1fr 320px', gap:20, alignItems:'start' }}>
          <div style={{ background:V2.card, border:`1px solid ${V2.rule}`, borderRadius:2 }}>
            <div className="mono" style={{
              display:'grid', gridTemplateColumns:'48px 1fr 80px 80px',
              gap:12, padding:'10px 16px',
              borderBottom:`1px solid ${V2.rule}`, background:V2.paper2,
              fontSize:10, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.08em'
            }}>
              <span>kind</span>
              <span>evidence</span>
              <span>risk</span>
              <span style={{ textAlign:'right' }}>t</span>
            </div>
            {SIM_EVS.map((ev,i)=>{
              const sel = ev.id === selectedId;
              return (
                <div key={ev.id} onClick={()=>setSelectedId(sel?null:ev.id)}
                  style={{
                    display:'grid', gridTemplateColumns:'48px 1fr 80px 80px',
                    gap:12, padding:'12px 16px', alignItems:'center',
                    borderBottom: i<SIM_EVS.length-1 ? `1px solid ${V2.rule}` : 'none',
                    cursor:'pointer',
                    background: sel ? V2.accentBg : 'transparent',
                    borderLeft: sel ? `3px solid ${V2.accent}` : '3px solid transparent',
                    paddingLeft: sel ? 13 : 16,
                    transition:'all 120ms',
                  }}
                  onMouseEnter={e=>{ if(!sel) e.currentTarget.style.background = V2.paper2; }}
                  onMouseLeave={e=>{ if(!sel) e.currentTarget.style.background = 'transparent'; }}>
                  <Badge tone={S_KIND_TONE[ev.kind]}>{S_KIND_LABEL[ev.kind]}</Badge>
                  <div className="mono" style={{
                    fontSize:12.5, color: sel ? V2.ink : V2.ink2,
                    overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'
                  }}>{ev.summary}</div>
                  <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                    <RiskDot risk={ev.risk}/>
                    <span className="mono" style={{ fontSize:11, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.06em' }}>{ev.risk}</span>
                  </div>
                  <div className="mono" style={{
                    fontSize:11, color:V2.ink3, textAlign:'right'
                  }}>{ev.ts}</div>
                </div>
              );
            })}
          </div>

          <div style={{ position:'sticky', top:80 }}>
            <Panel num="05" label="Inspector" padded={false}>
              <div style={{ padding:'12px 14px' }}>
                <SimInspector event={selectedEvent}/>
              </div>
            </Panel>
          </div>
        </div>
      </section>
    </div>
  );
}
Object.assign(window, { SimulationPage });
