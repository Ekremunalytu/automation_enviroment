/**
 * ExTrace — Reports Page (v3)
 * Forensic worksheet layout: header plate, metric strip, interaction graph,
 * connection evidence, timeline, event ledger + inspector.
 */

const R_TABS = [
  { value:'overview',   label:'Overview' },
  { value:'network',    label:'Network' },
  { value:'file',       label:'File I/O' },
  { value:'activation', label:'Activation' },
];

const R_EVENTS = [
  { id:'e1', kind:'activation', summary:'onStartupFinished → ms-python activated',              risk:'low',    ts:'14:02:31', t:0  },
  { id:'e2', kind:'file',       summary:'Read /Users/analyst/.vscode/extensions/manifest.json', risk:'medium', ts:'14:02:33', t:2  },
  { id:'e3', kind:'network',    summary:'GET https://marketplace.visualstudio.com/api/stats',   risk:'low',    ts:'14:02:35', t:4  },
  { id:'e4', kind:'network',    summary:'POST https://dc.services.visualstudio.com/v2/track',   risk:'high',   ts:'14:02:41', t:10 },
  { id:'e5', kind:'file',       summary:'Write /tmp/extrace-sandbox/output.json',               risk:'low',    ts:'14:02:44', t:13 },
  { id:'e6', kind:'activation', summary:'onDidOpenTextDocument fired for untitled-1.py',        risk:'low',    ts:'14:02:48', t:17 },
  { id:'e7', kind:'network',    summary:'GET https://pypi.org/pypi/requests/json',              risk:'medium', ts:'14:02:52', t:21 },
  { id:'e8', kind:'file',       summary:'Read /usr/local/lib/python3.11/site-packages/',        risk:'low',    ts:'14:02:55', t:24 },
];

const R_GRAPH = {
  root: { id:'root', label:'ms-python.python', kind:'root', meta:'extension' },
  groups: [
    {
      id:'g1', label:'Outgoing · Network', count:7, pct:87, kind:'category', axis:'network',
      description:'Outbound network calls made during activation window.',
      children:[
        { id:'n1', label:'marketplace.visualstudio.com', count:3, kind:'host', risk:'low',    meta:'TLS · 443', path:'/api/stats' },
        { id:'n2', label:'pypi.org',                      count:2, kind:'host', risk:'medium', meta:'TLS · 443', path:'/pypi/requests/json' },
        { id:'n3', label:'dc.services.visualstudio.com',  count:2, kind:'host', risk:'high',   meta:'TLS · 443', path:'/v2/track' },
      ]
    },
    {
      id:'g2', label:'Incoming · File I/O', count:8, pct:100, kind:'category', axis:'fs',
      description:'File system accesses during scenario run.',
      children:[
        { id:'n4', label:'~/.vscode/extensions/', count:4, kind:'path', risk:'low',    meta:'read', path:'manifest.json' },
        { id:'n5', label:'/tmp/extrace-sandbox/', count:3, kind:'path', risk:'low',    meta:'write', path:'output.json' },
        { id:'n6', label:'site-packages/',        count:1, kind:'path', risk:'medium', meta:'read',  path:'requests/__init__.py' },
      ]
    },
    {
      id:'g3', label:'Activation', count:3, pct:38, kind:'category', axis:'activation',
      description:'Extension activation events triggered during startup.',
      children:[
        { id:'n7', label:'onStartupFinished',     count:1, kind:'hook', risk:'low',   meta:'eager' },
        { id:'n8', label:'onLanguage:python',     count:1, kind:'hook', risk:'low',   meta:'lazy' },
        { id:'n9', label:'onDidOpenTextDocument', count:1, kind:'hook', risk:'low',   meta:'lazy' },
      ]
    },
    {
      id:'g4', label:'Secrets & Env', count:4, pct:14, kind:'category', axis:'secret',
      description:'Attempts to read secrets or environment.',
      children:[
        { id:'n10', label:'process.env',   count:2, kind:'env', risk:'medium', meta:'HOME · USER' },
        { id:'n11', label:'keychain',      count:1, kind:'env', risk:'high',   meta:'get(vscode)' },
        { id:'n12', label:'~/.ssh/',       count:1, kind:'path', risk:'high',  meta:'stat' },
      ]
    },
  ],
  // cross-links between children (shown as secondary connections)
  crossLinks: [
    { from:'n6', to:'n2',  label:'triggers fetch' },
    { from:'n11', to:'n3', label:'correlates' },
  ],
  connections:[
    { label:'Network → Activation', description:'Network activity happened near the target activation but remains correlative only (3.21s delta).', pct:38, risk:'low' },
    { label:'Scenario → File', description:'File access event happened during scenario window project_exploration. 1,684 linked events.', pct:100, risk:'low' },
  ],
  directLinks:[
    { label:'Near Target Activation', description:'dc.services.visualstudio.com — network activity near target activation; correlative only (3.21s delta).', risk:'low' },
    { label:'Automation Noise', description:'marketplace.visualstudio.com — triggered by Playwright automation, not extension behaviour.', risk:'low' },
  ]
};

const R_RISK_TONE = { low:'ok', medium:'warn', high:'danger' };
const R_KIND_LABEL = { activation:'ACT', file:'FILE', network:'NET' };
const R_KIND_TONE = { activation:'accent', file:'neutral', network:'warn' };
const R_RISK_COLOR = { low:V2.ok, medium:V2.warn, high:V2.danger };

// ── Interaction Graph — sankey-style flow diagram ─────────────────────────
//   Layout: extension root (left) → category columns (middle) → endpoints (right)
//   Ribbons carry animated particles showing activity flow. Category cards are
//   click-to-isolate. Endpoint cards show risk, meta, hit count.

function InteractionGraph({ data, selectedGroup, onSelectGroup }) {
  const W = 920, PAD = 20;
  const COL_X = { root: 60, cat: 320, leaf: 740 };
  const ROOT_W = 160, ROOT_H = 80;
  const CAT_W  = 200, CAT_H  = 56;
  const LEAF_W = 150, LEAF_H = 44;
  const LEAF_GAP = 10, CAT_GAP = 28;

  let catCursor = 0;
  const categoryLayout = data.groups.map((g) => {
    const leafCount = g.children.length;
    const blockH = leafCount * LEAF_H + (leafCount - 1) * LEAF_GAP;
    const topY = catCursor;
    catCursor += Math.max(blockH, CAT_H) + CAT_GAP;
    return { group: g, topY, blockH: Math.max(blockH, CAT_H), leafBlockH: blockH };
  });
  const totalH = catCursor - CAT_GAP + PAD * 2;
  const H = Math.max(totalH, 420);

  const catCenter = (cl) => PAD + cl.topY + cl.blockH / 2;
  const rootY = H / 2;

  const leafPos = {};
  categoryLayout.forEach(cl => {
    const innerStart = PAD + cl.topY + (cl.blockH - cl.leafBlockH) / 2;
    cl.group.children.forEach((c, ci) => {
      leafPos[c.id] = innerStart + ci * (LEAF_H + LEAF_GAP) + LEAF_H / 2;
    });
  });

  const isActive = (gid) => !selectedGroup || selectedGroup === gid;

  const ribbon = (x0, y0, x1, y1, thickness) => {
    const mx = (x0 + x1) / 2;
    const t = thickness / 2;
    return `M ${x0} ${y0 - t} C ${mx} ${y0 - t} ${mx} ${y1 - t} ${x1} ${y1 - t} L ${x1} ${y1 + t} C ${mx} ${y1 + t} ${mx} ${y0 + t} ${x0} ${y0 + t} Z`;
  };

  const flowLine = (x0, y0, x1, y1) => {
    const mx = (x0 + x1) / 2;
    return `M ${x0} ${y0} C ${mx} ${y0} ${mx} ${y1} ${x1} ${y1}`;
  };

  const [hoverId, setHoverId] = React.useState(null);

  return (
    <div style={{
      position:'relative', background:V2.paper,
      border:`1px solid ${V2.rule}`, borderRadius:2, overflow:'hidden'
    }}>
      <div style={{
        display:'flex', alignItems:'center', justifyContent:'space-between',
        padding:'10px 14px', borderBottom:`1px solid ${V2.rule}`, background:V2.paper2
      }}>
        <div style={{ display:'flex', alignItems:'center', gap:16 }}>
          <span className="eyebrow">Activity flow</span>
          <div style={{ display:'flex', alignItems:'center', gap:14 }}>
            <span className="mono" style={{ fontSize:10.5, color:V2.ink4, letterSpacing:'0.08em', textTransform:'uppercase' }}>extension</span>
            <span style={{ width:28, height:1, background:V2.rule2 }}/>
            <span className="mono" style={{ fontSize:10.5, color:V2.ink4, letterSpacing:'0.08em', textTransform:'uppercase' }}>category</span>
            <span style={{ width:28, height:1, background:V2.rule2 }}/>
            <span className="mono" style={{ fontSize:10.5, color:V2.ink4, letterSpacing:'0.08em', textTransform:'uppercase' }}>endpoint</span>
          </div>
        </div>
        <div style={{ display:'flex', gap:10, alignItems:'center' }}>
          <LegendPill color={V2.ok}     label="low"/>
          <LegendPill color={V2.warn}   label="medium"/>
          <LegendPill color={V2.danger} label="high"/>
        </div>
      </div>

      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display:'block' }}>
        <defs>
          <linearGradient id="ig-ribbon-a" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor={V2.accent} stopOpacity="0.28"/>
            <stop offset="1" stopColor={V2.accent} stopOpacity="0.12"/>
          </linearGradient>
          <linearGradient id="ig-ribbon-b" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor={V2.ink2} stopOpacity="0.22"/>
            <stop offset="1" stopColor={V2.ink2} stopOpacity="0.08"/>
          </linearGradient>
          <linearGradient id="ig-ribbon-dim" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor={V2.rule2} stopOpacity="0.35"/>
            <stop offset="1" stopColor={V2.rule2} stopOpacity="0.15"/>
          </linearGradient>
          <pattern id="ig-grid-flow" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke={V2.rule} strokeWidth="0.5" opacity="0.35"/>
          </pattern>
        </defs>

        <rect x="0" y="0" width={W} height={H} fill="url(#ig-grid-flow)"/>

        <g fontFamily="JetBrains Mono" fontSize="9.5" fill={V2.ink4} letterSpacing="0.1em">
          <text x={COL_X.root + ROOT_W/2} y={14} textAnchor="middle">01 · SOURCE</text>
          <text x={COL_X.cat  + CAT_W/2}  y={14} textAnchor="middle">02 · CATEGORY</text>
          <text x={COL_X.leaf + LEAF_W/2} y={14} textAnchor="middle">03 · ENDPOINT</text>
        </g>

        {[COL_X.root + ROOT_W, COL_X.cat, COL_X.cat + CAT_W, COL_X.leaf].map((x,i)=>(
          <line key={'cr'+i} x1={x} y1={22} x2={x} y2={H-14}
                stroke={V2.rule} strokeWidth="0.5" strokeDasharray="2 4"/>
        ))}

        {categoryLayout.map((cl, i) => {
          const g = cl.group;
          const active = isActive(g.id);
          const x0 = COL_X.root + ROOT_W;
          const x1 = COL_X.cat;
          const y0 = rootY;
          const y1 = catCenter(cl);
          const thickness = Math.max(8, Math.min(g.pct / 2.4, 42));
          const fill = active ? (i%2===0 ? 'url(#ig-ribbon-a)' : 'url(#ig-ribbon-b)')
                              : 'url(#ig-ribbon-dim)';
          return (
            <g key={'rib1-'+g.id} style={{ opacity: active?1:0.45, transition:'opacity 220ms' }}>
              <path d={ribbon(x0, y0, x1, y1, thickness)} fill={fill}/>
              <path id={'fl1-'+g.id} d={flowLine(x0, y0, x1, y1)} fill="none" stroke="none"/>
              {active && (
                <g>
                  <circle r="2.2" fill={V2.accent}>
                    <animateMotion dur={`${2.8 + i*0.4}s`} repeatCount="indefinite" rotate="auto">
                      <mpath href={'#fl1-'+g.id}/>
                    </animateMotion>
                  </circle>
                  <circle r="2.2" fill={V2.accent} opacity="0.55">
                    <animateMotion dur={`${2.8 + i*0.4}s`} begin={`${(2.8+i*0.4)*0.33}s`} repeatCount="indefinite">
                      <mpath href={'#fl1-'+g.id}/>
                    </animateMotion>
                  </circle>
                </g>
              )}
            </g>
          );
        })}

        {categoryLayout.map((cl) => {
          const g = cl.group;
          const active = isActive(g.id);
          return g.children.map((c, ci) => {
            const x0 = COL_X.cat + CAT_W;
            const x1 = COL_X.leaf;
            const y0 = catCenter(cl);
            const y1 = leafPos[c.id];
            const thickness = Math.max(5, Math.min(c.count * 4 + 6, 24));
            const riskCol = c.risk ? R_RISK_COLOR[c.risk] : V2.ink3;
            return (
              <g key={'rib2-'+c.id} style={{ opacity: active?1:0.35, transition:'opacity 220ms' }}>
                <path d={ribbon(x0, y0, x1, y1, thickness)}
                      fill={active ? riskCol : V2.rule2}
                      fillOpacity={active?0.18:0.5}/>
                <path id={'fl2-'+c.id} d={flowLine(x0, y0, x1, y1)} fill="none" stroke="none"/>
                {active && (
                  <circle r="1.8" fill={riskCol}>
                    <animateMotion dur={`${2 + ci*0.3}s`}
                                   begin={`${ci*0.2}s`}
                                   repeatCount="indefinite">
                      <mpath href={'#fl2-'+c.id}/>
                    </animateMotion>
                  </circle>
                )}
              </g>
            );
          });
        })}

        {(data.crossLinks || []).map((cl, i) => {
          const fromY = leafPos[cl.from];
          const toY = leafPos[cl.to];
          if (fromY == null || toY == null) return null;
          const x = COL_X.leaf - 4;
          const mx = x + 60;
          return (
            <g key={'cx'+i}>
              <path d={`M ${x} ${fromY} C ${mx} ${fromY} ${mx} ${toY} ${x} ${toY}`}
                    fill="none" stroke={V2.warn} strokeWidth="1.25"
                    strokeDasharray="3 3" opacity="0.7"/>
              <text x={mx - 6} y={(fromY + toY)/2 + 3} textAnchor="end"
                    fontSize="9" fontFamily="JetBrains Mono"
                    fill={V2.warn} letterSpacing="0.04em">
                {cl.label}
              </text>
            </g>
          );
        })}

        {(() => {
          const x = COL_X.root, y = rootY - ROOT_H/2;
          return (
            <g>
              <rect x={x-3} y={y-3} width={ROOT_W+6} height={ROOT_H+6}
                    fill="none" stroke={V2.accent} strokeWidth="0.75" strokeDasharray="3 3" opacity="0.6"/>
              <rect x={x} y={y} width={ROOT_W} height={ROOT_H}
                    fill={V2.ink} stroke={V2.ink}/>
              <rect x={x} y={y} width={ROOT_W} height="3" fill={V2.accent}/>
              <text x={x+12} y={y+22} fontSize="9.5" fill={V2.paper}
                    fontFamily="JetBrains Mono" letterSpacing="0.12em" opacity="0.7">
                EXTENSION
              </text>
              <text x={x+12} y={y+44} fontSize="13" fill={V2.paper}
                    fontFamily="Inter" fontWeight="600">
                {data.root.label}
              </text>
              <text x={x+12} y={y+62} fontSize="10" fill={V2.paper}
                    fontFamily="JetBrains Mono" opacity="0.6">
                {data.root.meta || 'source'}
              </text>
              <circle cx={x+ROOT_W} cy={y+ROOT_H/2} r="4" fill={V2.accent}/>
              <circle cx={x+ROOT_W} cy={y+ROOT_H/2} r="8"
                      fill="none" stroke={V2.accent} strokeWidth="0.75" className="ig-halo"/>
            </g>
          );
        })()}

        {categoryLayout.map((cl, i) => {
          const g = cl.group;
          const active = isActive(g.id);
          const sel = selectedGroup === g.id;
          const x = COL_X.cat, y = catCenter(cl) - CAT_H/2;
          return (
            <g key={'cat-'+g.id}
               onClick={() => onSelectGroup(sel ? null : g.id)}
               style={{ cursor:'pointer', opacity: active?1:0.4, transition:'opacity 220ms' }}>
              {sel && (
                <rect x={x-4} y={y-4} width={CAT_W+8} height={CAT_H+8}
                      fill="none" stroke={V2.accent} strokeWidth="1"/>
              )}
              <circle cx={x} cy={y+CAT_H/2} r="4" fill={V2.accent}/>
              <rect x={x} y={y} width={CAT_W} height={CAT_H}
                    fill={V2.paper} stroke={sel?V2.ink:V2.rule2} strokeWidth={sel?1.25:1}/>
              <rect x={x} y={y} width="3" height={CAT_H} fill={V2.accent}/>
              <rect x={x+3} y={y} width={CAT_W-3} height="2" fill={V2.rule}/>
              <rect x={x+3} y={y} width={(CAT_W-3)*(g.pct/100)} height="2" fill={V2.accent}/>
              <text x={x+12} y={y+16} fontSize="9.5" fill={V2.ink4}
                    fontFamily="JetBrains Mono" letterSpacing="0.12em">
                {String(i+1).padStart(2,'0')} · {(g.axis||'').toUpperCase()}
              </text>
              <text x={x+12} y={y+32} fontSize="12" fill={V2.ink}
                    fontFamily="Inter" fontWeight="600">
                {g.label.split(' · ').slice(-1)[0]}
              </text>
              <text x={x+12} y={y+47} fontSize="10" fill={V2.ink3}
                    fontFamily="JetBrains Mono">
                n = {g.count}  ·  weight {g.pct}%
              </text>
              <circle cx={x+CAT_W} cy={y+CAT_H/2} r="3" fill={active?V2.ink3:V2.rule2}/>
            </g>
          );
        })}

        {categoryLayout.map((cl) => {
          const g = cl.group;
          const active = isActive(g.id);
          return g.children.map((c) => {
            const x = COL_X.leaf, y = leafPos[c.id] - LEAF_H/2;
            const riskCol = c.risk ? R_RISK_COLOR[c.risk] : V2.ink3;
            const hov = hoverId === c.id;
            return (
              <g key={'lf-'+c.id}
                 onMouseEnter={()=>setHoverId(c.id)}
                 onMouseLeave={()=>setHoverId(h=>h===c.id?null:h)}
                 style={{ opacity: active?1:0.35, transition:'opacity 220ms', cursor:'default' }}>
                <circle cx={x} cy={y+LEAF_H/2} r="3" fill={riskCol}/>
                <rect x={x} y={y} width={LEAF_W} height={LEAF_H}
                      fill={V2.paper} stroke={hov?V2.ink:V2.rule2}
                      strokeWidth={hov?1.25:1}/>
                <rect x={x} y={y} width="3" height={LEAF_H} fill={riskCol}/>
                <text x={x+10} y={y+14} fontSize="9" fill={V2.ink4}
                      fontFamily="JetBrains Mono" letterSpacing="0.12em">
                  {(c.kind||'leaf').toUpperCase()}
                  {c.count > 1 ? `  ×${c.count}` : ''}
                </text>
                <text x={x+10} y={y+28} fontSize="10.5" fill={V2.ink}
                      fontFamily="JetBrains Mono" fontWeight="600">
                  {c.label.length > 20 ? c.label.slice(0,18)+'…' : c.label}
                </text>
                {c.meta && (
                  <text x={x+10} y={y+40} fontSize="9.5" fill={V2.ink3}
                        fontFamily="JetBrains Mono">
                    {c.meta.length > 24 ? c.meta.slice(0,22)+'…' : c.meta}
                  </text>
                )}
                {c.risk && c.risk !== 'low' && (
                  <g>
                    <rect x={x+LEAF_W-30} y={y+6} width="24" height="12" fill={riskCol}/>
                    <text x={x+LEAF_W-18} y={y+15} textAnchor="middle"
                          fontSize="8.5" fill={V2.paper}
                          fontFamily="JetBrains Mono" fontWeight="700"
                          letterSpacing="0.08em">
                      {c.risk[0].toUpperCase()}
                    </text>
                  </g>
                )}
              </g>
            );
          });
        })}
      </svg>

      <div style={{
        display:'flex', justifyContent:'space-between', alignItems:'center',
        padding:'8px 14px', borderTop:`1px solid ${V2.rule}`, background:V2.paper2
      }}>
        <span className="mono" style={{ fontSize:10.5, color:V2.ink3 }}>
          click a category card to isolate its flow · ribbon width ∝ volume · particles indicate activity
        </span>
        {selectedGroup && (
          <LinkButton onClick={()=>onSelectGroup(null)}>clear isolation ✕</LinkButton>
        )}
      </div>
    </div>
  );
}

function LegendPill({ color, label }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:5 }}>
      <span style={{ width:8, height:8, borderRadius:'50%', background:color }}/>
      <span className="mono" style={{ fontSize:10, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.08em' }}>{label}</span>
    </div>
  );
}

// ── Timeline — swimlanes, animated playhead, risk pulses ────────────────────
const R_LANES = [
  { id:'activation', label:'Activation', color:V2.accent, y:56 },
  { id:'file',       label:'File I/O',   color:V2.ink2,   y:116 },
  { id:'network',    label:'Network',    color:V2.warn,   y:176 },
];

function EventTimeline({ events, allEvents, selectedId, onSelect }) {
  const W = 960, H = 240;
  const PAD_L = 110, PAD_R = 28, PAD_T = 16, PAD_B = 40;
  const innerW = W - PAD_L - PAD_R;
  const maxT = Math.max(...allEvents.map(e=>e.t), 1) + 2;

  const [playing, setPlaying] = React.useState(false);
  const [cursor, setCursor]   = React.useState(0); // 0..1
  const [hoverId, setHoverId] = React.useState(null);
  const rafRef = React.useRef(null);
  const startedRef = React.useRef(null);

  React.useEffect(() => {
    if (!playing) { cancelAnimationFrame(rafRef.current); return; }
    const DURATION = 6000; // ms to scan full range
    const step = (ts) => {
      if (startedRef.current == null) startedRef.current = ts - cursor * DURATION;
      const t = Math.min(1, (ts - startedRef.current) / DURATION);
      setCursor(t);
      if (t >= 1) { setPlaying(false); startedRef.current = null; return; }
      rafRef.current = requestAnimationFrame(step);
    };
    rafRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafRef.current);
  }, [playing]);

  const xOf = (t) => PAD_L + (t / maxT) * innerW;
  const playX = PAD_L + cursor * innerW;

  // Flowing connectors between sequential events to suggest causality
  const ordered = [...allEvents].sort((a,b) => a.t - b.t);

  const onPlayToggle = () => {
    if (cursor >= 0.999) { setCursor(0); startedRef.current = null; }
    setPlaying(p => !p);
  };

  const handleSeek = (e) => {
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const ratio = px / rect.width;
    const x = ratio * W;
    const t = Math.max(0, Math.min(1, (x - PAD_L) / innerW));
    setCursor(t);
    startedRef.current = null;
  };

  return (
    <div style={{ position:'relative', background:V2.paper, border:`1px solid ${V2.rule}`, borderRadius:2 }}>
      {/* toolbar */}
      <div style={{
        display:'flex', alignItems:'center', justifyContent:'space-between',
        padding:'10px 14px', borderBottom:`1px solid ${V2.rule}`, background:V2.paper2
      }}>
        <div style={{ display:'flex', alignItems:'center', gap:14 }}>
          <button onClick={onPlayToggle}
            style={{
              fontFamily:"'JetBrains Mono', monospace", fontSize:11,
              padding:'5px 10px', background:playing?V2.ink:V2.paper,
              color:playing?V2.paper:V2.ink,
              border:`1px solid ${V2.ink}`, cursor:'pointer', borderRadius:2,
              letterSpacing:'0.08em', textTransform:'lowercase', minWidth:78
            }}>
            {playing?'❚❚ pause':'▶ scan'}
          </button>
          <span className="mono" style={{ fontSize:10.5, color:V2.ink3, letterSpacing:'0.06em' }}>
            t = {(cursor*maxT).toFixed(1)}s / {maxT}s
          </span>
          <span style={{ width:1, height:14, background:V2.rule2 }}/>
          <span className="mono" style={{ fontSize:10.5, color:V2.ink3 }}>
            {allEvents.length} events · {allEvents.filter(e=>e.risk==='high').length} high-risk
          </span>
        </div>
        <div style={{ display:'flex', gap:10 }}>
          {R_LANES.map(l => (
            <div key={l.id} style={{ display:'flex', alignItems:'center', gap:5 }}>
              <span style={{ width:10, height:3, background:l.color }}/>
              <span className="mono" style={{ fontSize:10, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.08em' }}>
                {l.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      <svg width="100%" viewBox={`0 0 ${W} ${H}`} onClick={handleSeek}
        style={{ display:'block', cursor:'crosshair' }}>
        <defs>
          <linearGradient id="tl-wash" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor={V2.accent} stopOpacity="0"/>
            <stop offset="1" stopColor={V2.accent} stopOpacity="0.08"/>
          </linearGradient>
          <filter id="tl-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2.2"/>
          </filter>
          <pattern id="tl-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">
            <line x1="0" y1="0" x2="0" y2="6" stroke={V2.rule} strokeWidth="1"/>
          </pattern>
        </defs>

        {/* scanned region wash */}
        <rect x={PAD_L} y={PAD_T} width={Math.max(0,playX-PAD_L)} height={H-PAD_T-PAD_B}
              fill="url(#tl-wash)"/>

        {/* lanes */}
        {R_LANES.map((lane) => (
          <g key={lane.id}>
            {/* lane label */}
            <rect x={4} y={lane.y-18} width={PAD_L-14} height={36}
                  fill={V2.paper2} stroke={V2.rule}/>
            <text x={14} y={lane.y-4} fontSize="10.5"
                  fill={V2.ink} fontFamily="JetBrains Mono" fontWeight="600" letterSpacing="0.06em">
              {lane.label.toUpperCase()}
            </text>
            <text x={14} y={lane.y+10} fontSize="9.5"
                  fill={V2.ink3} fontFamily="JetBrains Mono">
              n={allEvents.filter(e=>e.kind===lane.id).length}
            </text>
            {/* lane rail */}
            <line x1={PAD_L} y1={lane.y} x2={W-PAD_R} y2={lane.y}
                  stroke={V2.rule2} strokeWidth="1"/>
            {/* lane zone (subtle fill for rail bg) */}
            <rect x={PAD_L} y={lane.y-14} width={innerW} height={28}
                  fill="none" stroke={V2.rule} strokeDasharray="2 4" opacity="0.5"/>
          </g>
        ))}

        {/* time grid + labels */}
        {Array.from({length:7}).map((_,i)=>{
          const p = i/6;
          const x = PAD_L + p * innerW;
          return (
            <g key={i}>
              <line x1={x} y1={PAD_T} x2={x} y2={H-PAD_B}
                    stroke={V2.rule} strokeWidth="0.5" opacity="0.6"/>
              <line x1={x} y1={H-PAD_B} x2={x} y2={H-PAD_B+5}
                    stroke={V2.ink3} strokeWidth="1"/>
              <text x={x} y={H-PAD_B+18} textAnchor="middle"
                    fontSize="9.5" fill={V2.ink3}
                    fontFamily="JetBrains Mono" letterSpacing="0.06em">
                {(p*maxT).toFixed(0)}s
              </text>
            </g>
          );
        })}

        {/* causal connectors */}
        {ordered.slice(0, -1).map((ev, i) => {
          const next = ordered[i+1];
          const laneA = R_LANES.find(l=>l.id===ev.kind);
          const laneB = R_LANES.find(l=>l.id===next.kind);
          if (!laneA || !laneB) return null;
          const x0 = xOf(ev.t), y0 = laneA.y;
          const x1 = xOf(next.t), y1 = laneB.y;
          const dx = (x1 - x0) * 0.4;
          const path = `M ${x0} ${y0} C ${x0+dx} ${y0} ${x1-dx} ${y1} ${x1} ${y1}`;
          const visible = (x0 <= playX);
          return (
            <path key={'conn'+i} d={path}
                  stroke={V2.ink3} strokeWidth="1"
                  fill="none" strokeDasharray="3 3"
                  opacity={visible ? 0.35 : 0.12}
                  style={{ transition:'opacity 240ms' }}/>
          );
        })}

        {/* EVENT markers */}
        {allEvents.map((ev) => {
          const lane = R_LANES.find(l=>l.id===ev.kind);
          if (!lane) return null;
          const x = xOf(ev.t), y = lane.y;
          const col = R_RISK_COLOR[ev.risk];
          const sel = selectedId === ev.id;
          const hov = hoverId === ev.id;
          const scanned = xOf(ev.t) <= playX + 0.5;
          const dimmed = playing && !scanned;

          return (
            <g key={ev.id} style={{ cursor:'pointer' }}
               onMouseEnter={()=>setHoverId(ev.id)}
               onMouseLeave={()=>setHoverId(h=>h===ev.id?null:h)}
               onClick={(e)=>{ e.stopPropagation(); onSelect(ev.id); }}>
              {/* vertical drop to time axis */}
              <line x1={x} y1={y} x2={x} y2={H-PAD_B}
                    stroke={sel || hov ? col : V2.rule2}
                    strokeWidth={sel?1.25:1}
                    strokeDasharray={sel?'0':'2 3'}
                    opacity={dimmed?0.25:(sel||hov?0.8:0.5)}
                    style={{ transition:'opacity 180ms' }}/>

              {/* risk pulse for high/medium, only when scanned */}
              {ev.risk !== 'low' && scanned && (
                <circle cx={x} cy={y} r="6"
                        fill="none" stroke={col} strokeWidth="1"
                        className="tl-pulse" style={{ animationDelay: `${ev.t*0.1}s` }}/>
              )}

              {/* glow under point */}
              {(sel || hov) && (
                <circle cx={x} cy={y} r="11" fill={col} opacity="0.25" filter="url(#tl-glow)"/>
              )}

              {/* point marker — shape by kind */}
              {ev.kind==='activation' ? (
                <rect x={x-4.5} y={y-4.5} width="9" height="9"
                      fill={V2.paper} stroke={col} strokeWidth={sel||hov?2:1.5}
                      transform={`rotate(45 ${x} ${y})`}
                      opacity={dimmed?0.4:1}
                      style={{ transition:'opacity 200ms' }}/>
              ) : ev.kind==='file' ? (
                <rect x={x-4.5} y={y-4.5} width="9" height="9"
                      fill={V2.paper} stroke={col} strokeWidth={sel||hov?2:1.5}
                      opacity={dimmed?0.4:1}
                      style={{ transition:'opacity 200ms' }}/>
              ) : (
                <circle cx={x} cy={y} r={sel||hov?5.5:4.5}
                        fill={V2.paper} stroke={col} strokeWidth={sel||hov?2:1.5}
                        opacity={dimmed?0.4:1}
                        style={{ transition:'all 200ms' }}/>
              )}
              <circle cx={x} cy={y} r={sel||hov?2:1.5} fill={col}
                      opacity={dimmed?0.4:1}/>

              {/* hover/selected callout */}
              {(sel || hov) && (
                <g>
                  <line x1={x} y1={y-8} x2={x} y2={y-22} stroke={col} strokeWidth="1"/>
                  <rect x={x-3} y={y-25} width="6" height="6" fill={col}/>
                  <g transform={`translate(${Math.min(x, W-PAD_R-230)}, ${y-PAD_T < 60 ? y+24 : 8})`}>
                    <rect x="0" y="0" width="230" height="36"
                          fill={V2.ink} stroke={V2.ink}/>
                    <rect x="0" y="0" width="3" height="36" fill={col}/>
                    <text x="10" y="15" fontSize="10.5" fill={V2.paper}
                          fontFamily="JetBrains Mono" fontWeight="600" letterSpacing="0.04em">
                      {ev.ts} · +{ev.t}s · {ev.kind.toUpperCase()}
                    </text>
                    <text x="10" y="29" fontSize="10" fill={V2.paper}
                          fontFamily="JetBrains Mono" opacity="0.8">
                      {ev.summary.length>32?ev.summary.slice(0,30)+'…':ev.summary}
                    </text>
                  </g>
                </g>
              )}
            </g>
          );
        })}

        {/* playhead */}
        <g style={{ pointerEvents:'none' }}>
          <line x1={playX} y1={PAD_T-4} x2={playX} y2={H-PAD_B+4}
                stroke={V2.accent} strokeWidth="1.25"
                strokeDasharray={playing?'0':'4 3'}/>
          <polygon points={`${playX-5},${PAD_T-4} ${playX+5},${PAD_T-4} ${playX},${PAD_T+3}`}
                   fill={V2.accent}/>
          <rect x={playX-28} y={H-PAD_B+4} width="56" height="16" fill={V2.accent}/>
          <text x={playX} y={H-PAD_B+16} textAnchor="middle"
                fontSize="10" fontFamily="JetBrains Mono" fontWeight="600"
                fill={V2.paper} letterSpacing="0.04em">
            {(cursor*maxT).toFixed(1)}s
          </text>
        </g>
      </svg>

      <div style={{
        display:'flex', justifyContent:'space-between', alignItems:'center',
        padding:'8px 14px', borderTop:`1px solid ${V2.rule}`, background:V2.paper2
      }}>
        <span className="mono" style={{ fontSize:10.5, color:V2.ink3 }}>
          click to seek · hover a marker for detail · play to scan chronologically
        </span>
        <div style={{ display:'flex', gap:14 }}>
          {[['low',V2.ok],['medium',V2.warn],['high',V2.danger]].map(([r,c])=>(
            <div key={r} style={{ display:'flex', alignItems:'center', gap:5 }}>
              <span style={{ width:8, height:8, borderRadius:'50%', background:c }}/>
              <span className="mono" style={{ fontSize:10, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.08em' }}>{r}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Breakdown ───────────────────────────────────────────────────────────────
function KindBreakdown({ activeKind }) {
  const all = { activation:0, file:0, network:0 };
  R_EVENTS.forEach(e => all[e.kind]++);
  const total = R_EVENTS.length;
  const kindColor = { activation: V2.accent, file: V2.ink2, network: V2.warn };
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:14 }}>
      {Object.entries(all).map(([kind, n]) => {
        const active = activeKind === 'overview' || activeKind === kind;
        return (
          <div key={kind} style={{
            opacity: active ? 1 : 0.35, transition:'opacity 200ms'
          }}>
            <div style={{
              display:'flex', justifyContent:'space-between', alignItems:'baseline',
              marginBottom:6
            }}>
              <div className="mono" style={{
                fontSize:11, fontWeight:600, textTransform:'uppercase',
                letterSpacing:'0.1em',
                color: active ? kindColor[kind] : V2.ink3
              }}>{kind}</div>
              <div className="mono" style={{
                fontSize:13, color:V2.ink2, fontVariantNumeric:'tabular-nums'
              }}>{n} / {total}</div>
            </div>
            <div style={{
              height:4, background:V2.paper3, position:'relative',
              border:`1px solid ${V2.rule}`
            }}>
              <div style={{
                position:'absolute', left:0, top:0, bottom:0,
                width:`${(n/total)*100}%`, background:kindColor[kind],
                transition:'width 600ms ease'
              }}/>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Inspector ───────────────────────────────────────────────────────────────
function Inspector({ event }) {
  if (!event) return (
    <div style={{ padding:'24px 16px', textAlign:'center' }}>
      <div className="stripes" style={{
        padding:'32px 16px', border:`1px dashed ${V2.rule2}`, borderRadius:2
      }}>
        <div className="mono" style={{ fontSize:11, color:V2.ink3, letterSpacing:'0.08em' }}>
          no selection
        </div>
        <div style={{ fontSize:13, color:V2.ink3, marginTop:8, lineHeight:1.6 }}>
          Select an event from the ledger or timeline.
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
          borderLeft:`2px solid ${R_RISK_COLOR[event.risk]}`
        }}>{event.summary}</div>
      </div>

      <KVRow k="id" v={event.id}/>
      <KVRow k="kind" v={<Badge tone={R_KIND_TONE[event.kind]}>{R_KIND_LABEL[event.kind]}</Badge>} mono={false}/>
      <KVRow k="risk" v={<span style={{ display:'inline-flex', alignItems:'center', gap:6 }}><RiskDot risk={event.risk}/><Badge tone={R_RISK_TONE[event.risk]}>{event.risk}</Badge></span>} mono={false}/>
      <KVRow k="timestamp" v={event.ts}/>
      <KVRow k="offset" v={`+${event.t}s`}/>

      <div style={{ marginTop:14, padding:'4px 4px' }}>
        <div className="eyebrow" style={{ marginBottom:8 }}>Attribution</div>
        <div className="mono" style={{
          fontSize:12, color:V2.ink2, lineHeight:1.7,
          padding:'10px 12px', background:V2.paper, border:`1px solid ${V2.rule}`
        }}>
          ms-python.python<br/>
          scenario-1 / warmup<br/>
          kind: {event.kind}
        </div>
      </div>
    </div>
  );
}

// ── Risk breakdown — stratified bar chart with spark trends ─────────────────
const RISK_AXES = [
  { id:'network',   label:'Network reach',    score:68, benchmark:35, trend:[22,31,45,58,68], weight:'heavy', note:'5 hosts · 3 external' },
  { id:'fs',        label:'Filesystem scope', score:54, benchmark:40, trend:[18,24,30,44,54], weight:'med',   note:'412 read · 175 write' },
  { id:'secret',    label:'Secret access',    score:41, benchmark:15, trend:[6,12,22,34,41],  weight:'med',   note:'keychain · env vars' },
  { id:'exfil',     label:'Exfiltration',     score:36, benchmark:20, trend:[4,8,18,28,36],   weight:'med',   note:'3 outbound POSTs' },
  { id:'exec',      label:'Process spawn',    score:22, benchmark:25, trend:[8,12,14,18,22],  weight:'light', note:'2 child · shell=false' },
  { id:'persist',   label:'Persistence',      score:12, benchmark:10, trend:[2,4,6,9,12],     weight:'light', note:'no autoload hooks' },
];

function RiskRadar({ axes = RISK_AXES }) {
  const overall = Math.round(axes.reduce((s,a)=>s+a.score,0) / axes.length);
  const tone = overall>60?'danger':overall>35?'warn':'ok';
  const toneColor = tone==='danger'?V2.danger:tone==='warn'?V2.warn:V2.ok;

  // gauge arc: 180° semicircle
  const GW = 220, GH = 140, CX = GW/2, CY = GH-10, RAD = 88;
  const arcPoint = (t) => {
    const a = Math.PI + Math.PI*t;
    return [CX + Math.cos(a)*RAD, CY + Math.sin(a)*RAD];
  };
  const arc = (t0, t1) => {
    const [x0,y0] = arcPoint(t0), [x1,y1] = arcPoint(t1);
    const large = (t1-t0) > 0.5 ? 1 : 0;
    return `M ${x0} ${y0} A ${RAD} ${RAD} 0 ${large} 1 ${x1} ${y1}`;
  };
  const needleT = overall/100;
  const [nx, ny] = arcPoint(needleT);

  // sparkline
  const sparkPath = (trend) => {
    const W = 48, H = 16;
    const max = Math.max(...trend);
    return trend.map((v,i)=>{
      const x = (i/(trend.length-1))*W;
      const y = H - (v/max)*H;
      return (i===0?'M':'L') + ` ${x.toFixed(1)} ${y.toFixed(1)}`;
    }).join(' ');
  };

  return (
    <div style={{
      background:V2.paper, border:`1px solid ${V2.rule}`, borderRadius:2,
      display:'grid', gridTemplateColumns:'260px 1fr', gap:0,
      overflow:'hidden'
    }}>
      {/* ── LEFT: gauge + summary ─────────────────────────────────── */}
      <div style={{
        borderRight:`1px solid ${V2.rule}`, background:V2.paper2,
        padding:'20px 20px 18px',
        display:'flex', flexDirection:'column', gap:14
      }}>
        <div className="eyebrow">Composite score</div>

        {/* Semicircle gauge */}
        <div style={{ display:'flex', justifyContent:'center' }}>
          <svg width={GW} height={GH} viewBox={`0 0 ${GW} ${GH}`} style={{ overflow:'visible' }}>
            {/* tick zones */}
            <path d={arc(0, 0.35)}   stroke={V2.ok}     strokeWidth="10" fill="none" opacity="0.25"/>
            <path d={arc(0.35, 0.6)} stroke={V2.warn}   strokeWidth="10" fill="none" opacity="0.25"/>
            <path d={arc(0.6, 1)}    stroke={V2.danger} strokeWidth="10" fill="none" opacity="0.25"/>

            {/* progress arc (animated length to score) */}
            <path d={arc(0, needleT)} stroke={toneColor} strokeWidth="10" fill="none" strokeLinecap="butt"
                  style={{ transition:'all 600ms ease' }}/>

            {/* ticks every 10 */}
            {Array.from({length:11},(_,i)=>i/10).map((t,i)=>{
              const [x0,y0] = arcPoint(t);
              const [x1,y1] = [CX + Math.cos(Math.PI+Math.PI*t)*(RAD-6),
                               CY + Math.sin(Math.PI+Math.PI*t)*(RAD-6)];
              return <line key={i} x1={x0} y1={y0} x2={x1} y2={y1}
                          stroke={V2.paper} strokeWidth={i%5===0?1.5:1}/>;
            })}

            {/* needle */}
            <line x1={CX} y1={CY} x2={nx} y2={ny}
                  stroke={V2.ink} strokeWidth="2" strokeLinecap="round"/>
            <circle cx={CX} cy={CY} r={5} fill={V2.ink}/>
            <circle cx={CX} cy={CY} r={2} fill={V2.paper}/>

            {/* scale labels */}
            <text x={arcPoint(0)[0]-2} y={arcPoint(0)[1]+14} textAnchor="end"
                  fontSize="9.5" fill={V2.ink4} fontFamily="JetBrains Mono">0</text>
            <text x={arcPoint(0.5)[0]} y={arcPoint(0.5)[1]-10} textAnchor="middle"
                  fontSize="9.5" fill={V2.ink4} fontFamily="JetBrains Mono">50</text>
            <text x={arcPoint(1)[0]+2} y={arcPoint(1)[1]+14} textAnchor="start"
                  fontSize="9.5" fill={V2.ink4} fontFamily="JetBrains Mono">100</text>
          </svg>
        </div>

        {/* Big score */}
        <div style={{ textAlign:'center', marginTop:-6 }}>
          <div style={{ display:'flex', justifyContent:'center', alignItems:'baseline', gap:6 }}>
            <span className="serif" style={{
              fontSize:52, fontWeight:600, color:V2.ink, letterSpacing:'-0.03em', lineHeight:1
            }}>{overall}</span>
            <span className="mono" style={{ fontSize:12, color:V2.ink3 }}>/100</span>
          </div>
          <div style={{ marginTop:8, display:'flex', justifyContent:'center', gap:8, alignItems:'center' }}>
            <Badge tone={tone==='danger'?'danger':tone==='warn'?'warn':'ok'}>
              {tone==='danger'?'high':tone==='warn'?'medium':'low'} risk
            </Badge>
            <span className="mono" style={{ fontSize:10.5, color:V2.ink3 }}>
              +14 vs baseline
            </span>
          </div>
        </div>

        {/* Tier counts */}
        <div style={{ height:1, background:V2.rule, margin:'4px 0' }}/>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:8 }}>
          {[
            { lbl:'high',   n:axes.filter(a=>a.score>60).length, c:V2.danger },
            { lbl:'medium', n:axes.filter(a=>a.score>35&&a.score<=60).length, c:V2.warn },
            { lbl:'low',    n:axes.filter(a=>a.score<=35).length, c:V2.ok },
          ].map(t=>(
            <div key={t.lbl} style={{ textAlign:'center' }}>
              <div className="serif" style={{ fontSize:22, fontWeight:600, color:V2.ink, lineHeight:1 }}>{t.n}</div>
              <div style={{ display:'flex', alignItems:'center', gap:5, justifyContent:'center', marginTop:6 }}>
                <span style={{ width:6, height:6, borderRadius:'50%', background:t.c }}/>
                <span className="mono" style={{ fontSize:10, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.08em' }}>
                  {t.lbl}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── RIGHT: stratified bars ───────────────────────────────── */}
      <div style={{ padding:'20px 24px 18px' }}>
        {/* header */}
        <div style={{
          display:'grid',
          gridTemplateColumns:'160px 1fr 60px 70px 60px',
          columnGap:16, alignItems:'center',
          paddingBottom:8, marginBottom:10, borderBottom:`1px solid ${V2.rule}`
        }}>
          <span className="eyebrow">Axis</span>
          <span className="eyebrow">Score · vs benchmark</span>
          <span className="eyebrow" style={{ textAlign:'right' }}>Trend</span>
          <span className="eyebrow" style={{ textAlign:'right' }}>Weight</span>
          <span className="eyebrow" style={{ textAlign:'right' }}>Value</span>
        </div>

        <div style={{ display:'flex', flexDirection:'column' }}>
          {axes.map((a,i)=>{
            const barColor = a.score>60?V2.danger:a.score>35?V2.warn:V2.accent;
            return (
              <div key={a.id} style={{
                display:'grid',
                gridTemplateColumns:'160px 1fr 60px 70px 60px',
                columnGap:16, alignItems:'center',
                padding:'11px 0',
                borderBottom: i<axes.length-1 ? `1px dashed ${V2.rule}` : 'none'
              }}>
                {/* label + note */}
                <div>
                  <div style={{ fontSize:13, fontWeight:600, color:V2.ink, letterSpacing:'-0.005em', lineHeight:1.25 }}>
                    {a.label}
                  </div>
                  <div className="mono" style={{ fontSize:10.5, color:V2.ink3, marginTop:3 }}>
                    {a.note}
                  </div>
                </div>

                {/* bar + benchmark */}
                <div style={{ position:'relative', height:20 }}>
                  <div style={{
                    position:'absolute', inset:'6px 0', background:V2.rule,
                  }}/>
                  <div style={{
                    position:'absolute', left:0, top:6, bottom:6,
                    width:`${a.score}%`, background:barColor,
                    transition:'width 700ms ease',
                  }}/>
                  {/* benchmark marker */}
                  <div style={{
                    position:'absolute', left:`calc(${a.benchmark}% - 1px)`, top:0, bottom:0,
                    width:2, background:V2.ink, opacity:0.55,
                  }}/>
                  <div style={{
                    position:'absolute', left:`${a.benchmark}%`, top:-2,
                    transform:'translateX(-50%)',
                  }}>
                    <div style={{
                      width:0, height:0, borderLeft:'3px solid transparent',
                      borderRight:'3px solid transparent', borderTop:`4px solid ${V2.ink}`,
                      opacity:0.7
                    }}/>
                  </div>
                  {/* scale ticks */}
                  {[25,50,75].map(t=>(
                    <div key={t} style={{
                      position:'absolute', left:`${t}%`, top:4, bottom:4, width:1,
                      background:V2.paper, opacity:0.8
                    }}/>
                  ))}
                </div>

                {/* sparkline */}
                <div style={{ textAlign:'right' }}>
                  <svg width="48" height="16" viewBox="0 0 48 16" style={{ overflow:'visible', display:'inline-block' }}>
                    <path d={sparkPath(a.trend)} fill="none" stroke={barColor} strokeWidth="1.25"
                          strokeLinejoin="miter" strokeLinecap="butt"/>
                    {/* end dot */}
                    {(() => {
                      const last = a.trend[a.trend.length-1];
                      const max = Math.max(...a.trend);
                      const x = 48, y = 16 - (last/max)*16;
                      return <circle cx={x} cy={y} r={1.75} fill={barColor}/>;
                    })()}
                  </svg>
                </div>

                {/* weight */}
                <div style={{ textAlign:'right' }}>
                  <span className="mono" style={{
                    fontSize:10.5, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.08em',
                    padding:'3px 6px', border:`1px solid ${V2.rule2}`,
                    background:V2.paper
                  }}>{a.weight}</span>
                </div>

                {/* score */}
                <div style={{ textAlign:'right' }}>
                  <span className="mono" style={{ fontSize:14, fontWeight:600, color:V2.ink, fontVariantNumeric:'tabular-nums' }}>
                    {a.score}
                  </span>
                  <span className="mono" style={{ fontSize:10, color: a.score>a.benchmark?V2.danger:V2.ink3, marginLeft:4 }}>
                    {a.score>a.benchmark?'+':''}{a.score-a.benchmark}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* legend */}
        <div style={{
          display:'flex', gap:18, marginTop:14, paddingTop:12,
          borderTop:`1px solid ${V2.rule}`, flexWrap:'wrap'
        }}>
          <LegendSwatch color={V2.ok} label="low · 0–35"/>
          <LegendSwatch color={V2.warn} label="medium · 36–60"/>
          <LegendSwatch color={V2.danger} label="high · 61–100"/>
          <div style={{ display:'flex', alignItems:'center', gap:6 }}>
            <div style={{ width:0, height:0, borderLeft:'3px solid transparent',
                          borderRight:'3px solid transparent', borderTop:`5px solid ${V2.ink}`, opacity:0.7 }}/>
            <span className="mono" style={{ fontSize:10.5, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.08em' }}>
              population benchmark
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function LegendSwatch({ color, label }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:6 }}>
      <span style={{ width:14, height:4, background:color }}/>
      <span className="mono" style={{ fontSize:10.5, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.08em' }}>
        {label}
      </span>
    </div>
  );
}

// ── Sub-page: OVERVIEW ──────────────────────────────────────────────────────
function OverviewSection() {
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:32 }}>
      <section style={{
        display:'grid', gridTemplateColumns:'repeat(4, 1fr)',
        border:`1px solid ${V2.rule}`, background:V2.card, borderRadius:2
      }}>
        {[
          { label:'Total events', value:'1,248', sub:'across 3 kinds' },
          { label:'Network',      value:'349',   sub:'incl. 18 flagged', tone:'warn' },
          { label:'File I/O',     value:'587',   sub:'read 412 · write 175' },
          { label:'Flagged',      value:'57',    sub:'4.6% of total', tone:'danger' },
        ].map((m,i)=>(
          <div key={i} style={{
            padding:'22px 22px',
            borderRight: i<3 ? `1px solid ${V2.rule}` : 'none',
          }}>
            <MetricCell {...m}/>
          </div>
        ))}
      </section>

      <section style={{ display:'grid', gridTemplateColumns:'1fr 280px', gap:20 }}>
        <Panel num="01" label="By kind">
          <KindBreakdown activeKind="overview"/>
        </Panel>
        <Panel num="02" label="Risk mix">
          <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
            {[['low', 1180, V2.ok],['medium', 48, V2.warn],['high', 20, V2.danger]].map(([r,n,c])=>(
              <div key={r} style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                  <span style={{ width:8, height:8, borderRadius:'50%', background:c }}/>
                  <span className="mono" style={{ fontSize:11, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.1em' }}>{r}</span>
                </div>
                <span className="mono" style={{ fontSize:13, color:V2.ink2, fontVariantNumeric:'tabular-nums' }}>{n}</span>
              </div>
            ))}
          </div>
        </Panel>
      </section>

      <section>
        <RiskRadar/>
      </section>
    </div>
  );
}

// ── Sub-page: INTERACTIONS ──────────────────────────────────────────────────
function InteractionsSection({ selectedGroup, setSelectedGroup }) {
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:32 }}>
      <section>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-end', marginBottom:16, gap:16, flexWrap:'wrap' }}>
          <div>
            <Eyebrow num={1}>Interaction graph</Eyebrow>
            <SectionTitle style={{ marginTop:10 }}>How this extension connects</SectionTitle>
          </div>
          {selectedGroup && (
            <LinkButton onClick={()=>setSelectedGroup(null)}>Clear selection ✕</LinkButton>
          )}
        </div>
        <InteractionGraph data={R_GRAPH} selectedGroup={selectedGroup} onSelectGroup={setSelectedGroup}/>
      </section>

      <section style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
        <div>
          <Eyebrow num={2} style={{ marginBottom:12 }}>Relation groups</Eyebrow>
          <div style={{ display:'flex', flexDirection:'column', gap:0, border:`1px solid ${V2.rule}`, background:V2.card, borderRadius:2 }}>
            {R_GRAPH.groups.map((g,i)=>{
              const sel = selectedGroup===g.id;
              return (
                <div key={g.id} onClick={()=>setSelectedGroup(sel?null:g.id)}
                  style={{
                    padding:'14px 16px', cursor:'pointer',
                    background: sel ? V2.paper2 : 'transparent',
                    borderBottom: i<R_GRAPH.groups.length-1 ? `1px solid ${V2.rule}` : 'none',
                    borderLeft: sel ? `3px solid ${V2.accent}` : '3px solid transparent',
                    paddingLeft: sel ? 13 : 16,
                    transition:'all 140ms'
                  }}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', gap:12 }}>
                    <div style={{ fontSize:14, fontWeight:600, color:V2.ink }}>{g.label}</div>
                    <div className="mono" style={{ fontSize:11, color:V2.ink3 }}>n={g.count} · {g.pct}%</div>
                  </div>
                  <div className="mono" style={{ fontSize:11, color:V2.ink3, marginTop:4 }}>
                    {g.children.map(c=>c.label).slice(0,2).join('  ·  ')}{g.children.length>2?`  ·  +${g.children.length-2}`:''}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        <div>
          <Eyebrow num={3} style={{ marginBottom:12 }}>Connection summary</Eyebrow>
          <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
            {R_GRAPH.connections.map((c,i)=>(
              <div key={i} style={{
                padding:'14px 16px', background:V2.card,
                border:`1px solid ${V2.rule}`, borderRadius:2
              }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', gap:12, marginBottom:6 }}>
                  <div style={{ fontSize:14, fontWeight:600, color:V2.ink }}>{c.label}</div>
                  <Badge tone="accent">{c.pct}%</Badge>
                </div>
                <div style={{ fontSize:12.5, color:V2.ink3, lineHeight:1.55 }}>{c.description}</div>
              </div>
            ))}
            {R_GRAPH.directLinks.map((l,i)=>(
              <div key={'d'+i} style={{
                padding:'14px 16px', background:V2.paper,
                border:`1px dashed ${V2.rule2}`, borderRadius:2
              }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', gap:12, marginBottom:4 }}>
                  <div style={{ fontSize:13, fontWeight:600, color:V2.ink, display:'flex', alignItems:'center', gap:8 }}>
                    <RiskDot risk={l.risk}/> {l.label}
                  </div>
                  <Badge tone={R_RISK_TONE[l.risk]}>{l.risk}</Badge>
                </div>
                <div className="mono" style={{ fontSize:11.5, color:V2.ink3, lineHeight:1.55 }}>{l.description}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

// ── Sub-page: TIMELINE ──────────────────────────────────────────────────────
function TimelineSection({ selectedId, setSelectedId }) {
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
      <Panel num="01" label="Event timeline · chronological scan">
        <EventTimeline events={R_EVENTS} allEvents={R_EVENTS} selectedId={selectedId} onSelect={setSelectedId}/>
      </Panel>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
        <Panel num="02" label="Distribution by kind">
          <KindBreakdown activeKind="overview"/>
        </Panel>
        <Panel num="03" label="Event density · 1s buckets">
          <EventDensityStrip events={R_EVENTS} selectedId={selectedId} onSelect={setSelectedId}/>
        </Panel>
      </div>
    </div>
  );
}

function EventDensityStrip({ events, selectedId, onSelect }) {
  const maxT = Math.max(...events.map(e=>e.t), 1) + 1;
  const buckets = Array.from({length: Math.ceil(maxT)+1}, ()=>[]);
  events.forEach(e => { buckets[Math.floor(e.t)].push(e); });
  const maxCount = Math.max(...buckets.map(b=>b.length), 1);
  return (
    <div>
      <div style={{ display:'flex', alignItems:'flex-end', gap:2, height:84, padding:'4px 0' }}>
        {buckets.map((b, i) => {
          const hasSel = b.some(e=>e.id===selectedId);
          const riskTop = b.reduce((acc, e) => {
            const rank = e.risk==='high'?3:e.risk==='medium'?2:1;
            return rank > acc.rank ? { rank, col: R_RISK_COLOR[e.risk] } : acc;
          }, { rank:0, col:V2.rule2 });
          const h = b.length === 0 ? 2 : (b.length/maxCount)*64 + 6;
          return (
            <div key={i}
                 onClick={()=> b[0] && onSelect(b[0].id)}
                 style={{
                   flex:1, height:h, background: b.length? riskTop.col : V2.rule,
                   opacity: b.length? (hasSel?1:0.85):0.35,
                   borderTop: hasSel?`2px solid ${V2.ink}`:'none',
                   cursor: b.length?'pointer':'default',
                   transition:'all 180ms'
                 }}
                 title={`${i}s: ${b.length} events`}/>
          );
        })}
      </div>
      <div style={{ display:'flex', justifyContent:'space-between', marginTop:6 }}>
        <span className="mono" style={{ fontSize:10, color:V2.ink4 }}>0s</span>
        <span className="mono" style={{ fontSize:10, color:V2.ink4 }}>{Math.ceil(maxT)}s</span>
      </div>
      <div style={{ marginTop:10, fontSize:11.5, color:V2.ink3, lineHeight:1.5 }}>
        Peak concentration at <span className="mono" style={{ color:V2.ink }}>t={buckets.indexOf(buckets.reduce((a,b)=>b.length>a.length?b:a))}s</span> with {maxCount} event{maxCount>1?'s':''}. Click a bar to inspect.
      </div>
    </div>
  );
}

// ── Page ────────────────────────────────────────────────────────────────────
const MAIN_TABS = [
  { value:'overview',     label:'Overview' },
  { value:'interactions', label:'Interactions' },
  { value:'timeline',     label:'Timeline' },
  { value:'ledger',       label:'Event ledger' },
];

function ReportsPage() {
  const stored = (() => { try { return localStorage.getItem('extrace-v2-r-tab'); } catch { return null; } })();
  const [mainTab, setMainTab] = React.useState(stored || 'overview');
  const nav = t => { setMainTab(t); try { localStorage.setItem('extrace-v2-r-tab', t); } catch {} };

  const [tab, setTab] = React.useState('overview');
  const [search, setSearch] = React.useState('');
  const [selectedId, setSelectedId] = React.useState(null);
  const [selectedGroup, setSelectedGroup] = React.useState(null);

  const filteredByTab = R_EVENTS.filter(e => {
    if (tab==='network')    return e.kind==='network';
    if (tab==='file')       return e.kind==='file';
    if (tab==='activation') return e.kind==='activation';
    return true;
  });
  const events = filteredByTab.filter(e => !search || e.summary.toLowerCase().includes(search.toLowerCase()));
  const selectedEvent = R_EVENTS.find(e => e.id === selectedId) || null;

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:40 }}>
      {/* ── HEADER PLATE ─────────────────────────────────────────────── */}
      <header style={{
        display:'grid', gridTemplateColumns:'1fr auto', gap:24,
        alignItems:'flex-start',
        paddingBottom:24, borderBottom:`1px solid ${V2.rule2}`,
      }}>
        <div style={{ minWidth:0 }}>
          <Eyebrow num={1}>Activation report</Eyebrow>
          <PageTitle style={{ marginTop:14, fontSize:44, wordBreak:'break-word' }}>
            ms-python.python
          </PageTitle>
          <div style={{ marginTop:14, display:'flex', gap:18, flexWrap:'wrap', alignItems:'center' }}>
            <span className="mono" style={{ fontSize:12, color:V2.ink2, fontWeight:500 }}>v2024.4.1</span>
            <span style={{ width:1, height:12, background:V2.rule2 }}/>
            <span className="mono" style={{ fontSize:12, color:V2.ink3 }}>report-8f3a2c1</span>
            <span style={{ width:1, height:12, background:V2.rule2 }}/>
            <span className="mono" style={{ fontSize:12, color:V2.ink3 }}>apr 21 2026 · 14:02</span>
            <span style={{ width:1, height:12, background:V2.rule2 }}/>
            <span style={{ display:'inline-flex', alignItems:'center', gap:6 }}>
              <RiskDot risk="medium"/>
              <span className="mono" style={{ fontSize:12, color:V2.ink2 }}>risk · medium</span>
            </span>
          </div>
        </div>
        <div style={{ display:'flex', gap:8, paddingTop:14 }}>
          <GhostButton>Export</GhostButton>
          <GhostButton>Re-run</GhostButton>
        </div>
      </header>

      {/* ── SUB-NAV ──────────────────────────────────────────────────── */}
      <nav style={{
        display:'flex', gap:0,
        borderBottom:`1px solid ${V2.rule2}`,
        marginTop:-24, marginBottom:8
      }}>
        {MAIN_TABS.map(t => {
          const active = t.value === mainTab;
          return (
            <button key={t.value} onClick={()=>nav(t.value)}
              style={{
                border:'none', background:'transparent', cursor:'pointer',
                padding:'14px 20px', fontFamily:'inherit',
                fontSize:13, letterSpacing:'-0.005em',
                fontWeight: active ? 600 : 500,
                color: active ? V2.ink : V2.ink3,
                borderBottom: active ? `2px solid ${V2.accent}` : '2px solid transparent',
                marginBottom:-1, transition:'color 140ms',
              }}
              onMouseEnter={e=>{ if(!active) e.currentTarget.style.color=V2.ink2; }}
              onMouseLeave={e=>{ if(!active) e.currentTarget.style.color=V2.ink3; }}>
              {t.label}
            </button>
          );
        })}
      </nav>

      {mainTab==='overview'     && <OverviewSection/>}
      {mainTab==='interactions' && <InteractionsSection selectedGroup={selectedGroup} setSelectedGroup={setSelectedGroup}/>}
      {mainTab==='timeline'     && <TimelineSection selectedId={selectedId} setSelectedId={setSelectedId}/>}
      {mainTab==='ledger'       && <LedgerSection tab={tab} setTab={setTab} search={search} setSearch={setSearch} selectedId={selectedId} setSelectedId={setSelectedId} events={events} selectedEvent={selectedEvent}/>}
    </div>
  );
}

function LedgerSection({ tab, setTab, search, setSearch, selectedId, setSelectedId, events, selectedEvent }) {
  return (
    <div>
      {/* ── EVENT LEDGER + INSPECTOR ─────────────────────────────────── */}
      <section>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-end', marginBottom:16, gap:16, flexWrap:'wrap' }}>
          <div>
            <Eyebrow num={1}>Event ledger</Eyebrow>
            <SectionTitle style={{ marginTop:10 }}>Every captured event, raw</SectionTitle>
          </div>
          <div style={{ display:'flex', alignItems:'flex-end', gap:12 }}>
            <Field placeholder="Search events…" value={search} onChange={setSearch} mono style={{ width:260 }}/>
          </div>
        </div>

        <Tabs tabs={R_TABS} value={tab} onChange={t=>{ setTab(t); setSelectedId(null); }} style={{ marginBottom:16 }}/>

        <div style={{ background:V2.card, border:`1px solid ${V2.rule}`, borderRadius:2 }}>
          {/* header row */}
          <div className="mono" style={{
            display:'grid', gridTemplateColumns:'56px 80px 1fr 100px 90px 28px',
            gap:12, padding:'10px 16px',
            borderBottom:`1px solid ${V2.rule}`, background:V2.paper2,
            fontSize:10, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.08em'
          }}>
            <span>#</span>
            <span>kind</span>
            <span>evidence</span>
            <span>risk</span>
            <span style={{ textAlign:'right' }}>t</span>
            <span/>
          </div>

          {events.length===0
            ? <EmptyState eyebrow="Empty" title="No events match" body="Try a broader filter or different query."/>
            : events.map((ev,i)=>{
                const sel = ev.id === selectedId;
                return (
                  <React.Fragment key={ev.id}>
                    <div onClick={()=>setSelectedId(sel?null:ev.id)}
                      style={{
                        display:'grid', gridTemplateColumns:'56px 80px 1fr 100px 90px 28px',
                        gap:12, padding:'12px 16px', alignItems:'center',
                        borderBottom: (i<events.length-1 || sel) ? `1px solid ${V2.rule}` : 'none',
                        cursor:'pointer',
                        background: sel ? V2.accentBg : 'transparent',
                        borderLeft: sel ? `3px solid ${V2.accent}` : '3px solid transparent',
                        paddingLeft: sel ? 13 : 16,
                        transition:'background 120ms',
                      }}
                      onMouseEnter={e=>{ if(!sel) e.currentTarget.style.background = V2.paper2; }}
                      onMouseLeave={e=>{ if(!sel) e.currentTarget.style.background = 'transparent'; }}>
                      <span className="mono" style={{ fontSize:10.5, color:V2.ink4 }}>
                        {String(i+1).padStart(3,'0')}
                      </span>
                      <Badge tone={R_KIND_TONE[ev.kind]}>{R_KIND_LABEL[ev.kind]}</Badge>
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
                      <span className="mono" style={{
                        fontSize:11, color:V2.ink4, textAlign:'center',
                        transform: sel ? 'rotate(90deg)' : 'rotate(0deg)',
                        transition:'transform 180ms'
                      }}>›</span>
                    </div>

                    {sel && (
                      <div style={{
                        background: V2.paper2,
                        borderBottom: i<events.length-1 ? `1px solid ${V2.rule}` : 'none',
                        borderLeft: `3px solid ${V2.accent}`,
                        padding: '16px 16px 20px 13px',
                      }}>
                        <ExpandedInspector event={ev}/>
                      </div>
                    )}
                  </React.Fragment>
                );
              })
          }
        </div>
      </section>
    </div>
  );
}

// ── Expanded row inspector: horizontal 3-col layout ─────────────────────────
function ExpandedInspector({ event }) {
  return (
    <div style={{
      display:'grid', gridTemplateColumns:'1.4fr 1fr 1fr', gap:20,
    }}>
      {/* Evidence */}
      <div>
        <div className="eyebrow" style={{ marginBottom:8 }}>Evidence</div>
        <div className="mono" style={{
          fontSize:12.5, color:V2.ink, lineHeight:1.6, wordBreak:'break-all',
          padding:'10px 12px', background:V2.paper, border:`1px solid ${V2.rule}`,
          borderLeft:`2px solid ${R_RISK_COLOR[event.risk]}`
        }}>{event.summary}</div>
        <div style={{ marginTop:12 }}>
          <div className="eyebrow" style={{ marginBottom:6 }}>Attribution</div>
          <div className="mono" style={{ fontSize:11.5, color:V2.ink2, lineHeight:1.7 }}>
            ms-python.python · scenario-1 / warmup · kind: {event.kind}
          </div>
        </div>
      </div>

      {/* Metadata grid */}
      <div>
        <div className="eyebrow" style={{ marginBottom:8 }}>Metadata</div>
        <div style={{
          display:'grid', gridTemplateColumns:'auto 1fr', columnGap:14, rowGap:6,
          padding:'10px 12px', background:V2.paper, border:`1px solid ${V2.rule}`
        }}>
          <InlineKV k="id"        v={event.id}/>
          <InlineKV k="kind"      v={R_KIND_LABEL[event.kind]}/>
          <InlineKV k="risk"      v={event.risk} dot={R_RISK_COLOR[event.risk]}/>
          <InlineKV k="timestamp" v={event.ts}/>
          <InlineKV k="offset"    v={`+${event.t}s`}/>
        </div>
      </div>

      {/* Actions */}
      <div>
        <div className="eyebrow" style={{ marginBottom:8 }}>Actions</div>
        <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
          <GhostButton>Copy event JSON</GhostButton>
          <GhostButton>Add to watchlist</GhostButton>
          <GhostButton>Filter by this kind</GhostButton>
        </div>
        <div style={{ marginTop:12 }}>
          <div className="eyebrow" style={{ marginBottom:6 }}>Signature</div>
          <div className="mono" style={{
            fontSize:11, color:V2.ink3, lineHeight:1.6,
            padding:'8px 10px', background:V2.paper,
            border:`1px dashed ${V2.rule2}`, wordBreak:'break-all'
          }}>
            sha256:8f3a2c1···{event.id.slice(-4)}
          </div>
        </div>
      </div>
    </div>
  );
}

function InlineKV({ k, v, dot }) {
  return (
    <React.Fragment>
      <span className="mono" style={{
        fontSize:10.5, color:V2.ink3, textTransform:'uppercase', letterSpacing:'0.08em',
        alignSelf:'center'
      }}>{k}</span>
      <span className="mono" style={{
        fontSize:12, color:V2.ink, display:'inline-flex', alignItems:'center', gap:6,
        wordBreak:'break-all'
      }}>
        {dot && <span style={{ width:6, height:6, borderRadius:'50%', background:dot }}/>}
        {v}
      </span>
    </React.Fragment>
  );
}
Object.assign(window, { ReportsPage });
