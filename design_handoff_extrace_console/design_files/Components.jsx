/**
 * ExTrace — Shared UI Components (Shift5 theme)
 * Bold display typography, coral accent on near-black canvas with bone-grey blocks.
 */

const V2 = {
  // surfaces
  paper:    '#0a0a0a',   // canvas (deep black)
  paper2:   '#141414',   // raised
  paper3:   '#1c1c1c',   // wells
  card:     '#0f0f0f',
  // bone (light grey panel — Shift5 right-side block)
  bone:     '#d6d4d0',
  bone2:    '#c5c2bd',
  // coral signature
  coral:    '#ff5c42',
  coralDeep:'#e84a31',
  coralSoft:'#ffe4dd',
  // ink → text on dark
  ink:      '#f4f1ea',   // primary text
  ink2:     '#cfcbc2',
  ink3:     '#8a8780',
  ink4:     '#5a5750',
  // rules
  rule:     '#2b2b2b',
  rule2:    '#3a3a3a',
  // accent aliases
  accent:   '#ff5c42',
  accentInk:'#0a0a0a',
  accentBg: '#1c1c1c',
  // status
  danger:   '#ff5c42',
  dangerBg: '#2a1612',
  warn:     '#d4a85a',
  warnBg:   '#2a200f',
  ok:       '#7ab088',
  okBg:     '#13231a',
};

// ── Primitive typography ────────────────────────────────────────────────────
function Eyebrow({ children, num, style }) {
  return (
    <div className="eyebrow" style={{ display:'flex', alignItems:'center', gap:10, ...style }}>
      <span>{children}</span>
    </div>
  );
}

function PageTitle({ children, style }) {
  return (
    <h1 className="display" style={{
      fontSize:88, fontWeight:800, letterSpacing:'-0.045em', lineHeight:0.92,
      color:V2.ink, textWrap:'balance', ...style
    }}>{children}</h1>
  );
}

function SectionTitle({ children, style }) {
  return (
    <h2 style={{
      fontFamily:"'Manrope', sans-serif",
      fontSize:28, fontWeight:700, letterSpacing:'-0.025em', color:V2.ink,
      lineHeight:1.05, ...style
    }}>{children}</h2>
  );
}

// ── Buttons ─────────────────────────────────────────────────────────────────
function SolidButton({ children, onClick, disabled, style }) {
  const [hover, setHover] = React.useState(false);
  return (
    <button onClick={onClick} disabled={disabled}
      onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}
      style={{
        display:'inline-flex', alignItems:'center', gap:8,
        background: disabled ? V2.rule : (hover ? V2.coralDeep : V2.coral),
        color: V2.ink2 === '#cfcbc2' ? '#0a0a0a' : V2.paper,
        border:'none', padding:'12px 18px',
        fontSize:12, fontWeight:700, letterSpacing:'0.04em',
        textTransform:'uppercase',
        cursor:disabled?'not-allowed':'pointer',
        transition:'background 140ms', borderRadius:0,
        ...style
      }}>
      {children}
    </button>
  );
}

function GhostButton({ children, onClick, style }) {
  const [hover, setHover] = React.useState(false);
  return (
    <button onClick={onClick}
      onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}
      style={{
        display:'inline-flex', alignItems:'center', gap:8,
        background: hover ? V2.paper3 : 'transparent',
        color: hover ? V2.coral : V2.ink,
        border:`1px solid ${hover ? V2.coral : V2.rule2}`,
        padding:'11px 16px', fontSize:11, fontWeight:600, letterSpacing:'0.06em',
        textTransform:'uppercase',
        cursor:'pointer', transition:'all 140ms', borderRadius:0,
        ...style
      }}>
      {children}
    </button>
  );
}

function LinkButton({ children, onClick, style }) {
  const [hover, setHover] = React.useState(false);
  return (
    <button onClick={onClick}
      onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}
      style={{
        background:'transparent', border:'none', padding:0,
        color: hover ? V2.coralDeep : V2.coral,
        fontSize:12, fontWeight:600, cursor:'pointer',
        textDecoration: hover ? 'underline' : 'none',
        textUnderlineOffset:'3px', letterSpacing:'0.02em',
        fontFamily:"'JetBrains Mono', monospace",
        ...style
      }}>
      {children}
    </button>
  );
}

// ── Badges ──────────────────────────────────────────────────────────────────
const BADGE = {
  neutral: { bg: V2.paper3, fg: V2.ink2,   bd: V2.rule2 },
  accent:  { bg: V2.coralSoft, fg: V2.coralDeep, bd: V2.coral },
  ok:      { bg: V2.okBg,   fg: V2.ok,     bd: '#2a4a36' },
  warn:    { bg: V2.warnBg, fg: V2.warn,   bd: '#5c4a22' },
  danger:  { bg: V2.coral,  fg: V2.paper,  bd: V2.coral },
};

function Badge({ children, tone='neutral', style }) {
  const t = BADGE[tone] || BADGE.neutral;
  return (
    <span className="mono" style={{
      display:'inline-flex', alignItems:'center',
      background:t.bg, color:t.fg, border:`1px solid ${t.bd}`,
      padding:'3px 8px', fontSize:10, fontWeight:600, letterSpacing:'0.08em',
      textTransform:'uppercase', borderRadius:0, ...style
    }}>{children}</span>
  );
}

// ── Risk dot ────────────────────────────────────────────────────────────────
function RiskDot({ risk, size=10 }) {
  const map = { low:V2.ok, medium:V2.warn, high:V2.coral };
  return (
    <span style={{
      width:size, height:size, borderRadius:0,
      background:map[risk], display:'inline-block', flexShrink:0
    }}/>
  );
}

// ── Field ───────────────────────────────────────────────────────────────────
function Field({ label, placeholder, value, onChange, mono, style, inputStyle }) {
  const [f, setF] = React.useState(false);
  const [hover, setHover] = React.useState(false);
  const bd = f ? V2.coral : (hover ? V2.rule2 : V2.rule);
  return (
    <label style={{ display:'flex', flexDirection:'column', gap:6, ...style }}>
      {label && <Eyebrow>{label}</Eyebrow>}
      <input placeholder={placeholder} value={value||''}
        onChange={e=>onChange&&onChange(e.target.value)}
        onFocus={()=>setF(true)} onBlur={()=>setF(false)}
        onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}
        style={{
          width:'100%', background:V2.paper2, color:V2.ink,
          border:`1px solid ${bd}`, borderRadius:0,
          padding:'12px 14px', fontSize:14, outline:'none',
          fontFamily: mono ? "'JetBrains Mono', monospace" : "'Manrope', sans-serif",
          transition:'border-color 140ms',
          ...inputStyle
        }}/>
    </label>
  );
}

// ── Panel / Card ────────────────────────────────────────────────────────────
function Panel({ children, label, num, right, padded=true, style }) {
  return (
    <section style={{
      background:V2.paper2, border:`1px solid ${V2.rule}`, borderRadius:0,
      position:'relative', ...style
    }}>
      {(label || right) && (
        <header style={{
          display:'flex', alignItems:'center', justifyContent:'space-between',
          padding:'14px 16px', borderBottom:`1px solid ${V2.rule}`, gap:12,
          background:V2.paper3,
        }}>
          {label && <Eyebrow num={num}>{label}</Eyebrow>}
          {right && <div>{right}</div>}
        </header>
      )}
      <div style={padded ? { padding:16 } : undefined}>{children}</div>
    </section>
  );
}

// ── Tabs ────────────────────────────────────────────────────────────────────
function Tabs({ tabs, value, onChange, style }) {
  return (
    <div style={{
      display:'flex', gap:0, borderBottom:`1px solid ${V2.rule2}`,
      ...style
    }}>
      {tabs.map(t => {
        const a = t.value === value;
        return (
          <button key={t.value} onClick={()=>onChange(t.value)}
            style={{
              background:'none', border:'none', padding:'12px 18px 13px',
              fontSize:11, fontWeight:a?700:500, letterSpacing:'0.1em',
              textTransform:'uppercase',
              color: a ? V2.ink : V2.ink3,
              cursor:'pointer', position:'relative',
              transition:'color 140ms',
              fontFamily:"'JetBrains Mono', monospace",
            }}>
            {t.label}
            {a && <span style={{
              position:'absolute', left:0, right:0, bottom:-1, height:3,
              background:V2.coral
            }}/>}
          </button>
        );
      })}
    </div>
  );
}

// ── Metric cell ─────────────────────────────────────────────────────────────
function MetricCell({ label, value, sub, tone='neutral', align='left' }) {
  const t = BADGE[tone] || BADGE.neutral;
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:8, textAlign:align }}>
      <Eyebrow>{label}</Eyebrow>
      <div className="display" style={{
        fontSize:48, fontWeight:800, letterSpacing:'-0.04em', lineHeight:0.95,
        color: tone==='neutral' ? V2.ink : (tone==='danger' ? V2.coral : t.fg),
        fontVariantNumeric:'tabular-nums'
      }}>{value}</div>
      {sub && <div className="mono" style={{ fontSize:11, color:V2.ink3, letterSpacing:'0.04em' }}>{sub}</div>}
    </div>
  );
}

// ── Key/Value ───────────────────────────────────────────────────────────────
function KVRow({ k, v, mono=true }) {
  return (
    <div style={{
      display:'grid', gridTemplateColumns:'120px 1fr', gap:12,
      padding:'10px 0', borderBottom:`1px dashed ${V2.rule2}`,
      alignItems:'baseline'
    }}>
      <div className="eyebrow">{k}</div>
      <div className={mono?'mono':''} style={{
        fontSize: mono ? 12.5 : 13, color:V2.ink2, wordBreak:'break-all'
      }}>{v}</div>
    </div>
  );
}

// ── Empty state ─────────────────────────────────────────────────────────────
function EmptyState({ eyebrow, title, body, action }) {
  return (
    <div style={{
      padding:'56px 24px', textAlign:'center',
      border:`1px dashed ${V2.rule2}`, borderRadius:0,
      background:V2.paper2,
      display:'flex', flexDirection:'column', alignItems:'center', gap:12
    }}>
      {eyebrow && <Eyebrow>{eyebrow}</Eyebrow>}
      <div className="display" style={{
        fontSize:32, fontWeight:700, color:V2.ink, letterSpacing:'-0.03em', lineHeight:1
      }}>{title}</div>
      {body && <div style={{ fontSize:13, color:V2.ink3, maxWidth:380, lineHeight:1.6 }}>{body}</div>}
      {action}
    </div>
  );
}

// ── Progress bar ────────────────────────────────────────────────────────────
function ProgressBar({ pct=0, tone='ink' }) {
  const col = tone==='ink' ? V2.coral : (BADGE[tone] || BADGE.neutral).fg;
  return (
    <div style={{
      height:6, background:V2.paper3, borderRadius:0,
      position:'relative', overflow:'hidden',
      border:`1px solid ${V2.rule}`
    }}>
      <div style={{
        position:'absolute', left:0, top:0, bottom:0,
        width:`${pct}%`, background:col,
        transition:'width 600ms ease'
      }}/>
    </div>
  );
}

// ── Crosshair ───────────────────────────────────────────────────────────────
function Crosshair({ size=8, color=V2.ink, style }) {
  return (
    <svg width={size*2} height={size*2} style={style}>
      <line x1={0} y1={size} x2={size*2} y2={size} stroke={color} strokeWidth="1"/>
      <line x1={size} y1={0} x2={size} y2={size*2} stroke={color} strokeWidth="1"/>
    </svg>
  );
}

// ── Logo: Shift5-inspired chevron mark ──────────────────────────────────────
function LogoMark({ size=28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" fill="none">
      {/* chevron pair */}
      <path d="M3 6 L11 14 L3 22" stroke={V2.coral} strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter" fill="none"/>
      <path d="M14 6 L22 14 L14 22" stroke={V2.ink} strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter" fill="none"/>
    </svg>
  );
}

Object.assign(window, {
  V2,
  Eyebrow, PageTitle, SectionTitle,
  SolidButton, GhostButton, LinkButton,
  Badge, RiskDot,
  Field,
  Panel, Tabs,
  MetricCell, KVRow,
  EmptyState, ProgressBar, Crosshair, LogoMark,
});
