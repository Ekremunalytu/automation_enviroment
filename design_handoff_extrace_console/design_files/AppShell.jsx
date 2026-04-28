/**
 * ExTrace — App Shell (Shift5 theme)
 * Dark canvas. Left rail black w/ coral accents.
 */
function AppShell({ page, onNavigate, children }) {
  const NAV = [
    { id:'reports',     label:'Reports',     hint:'Activation reports & artifacts' },
    { id:'simulation',  label:'Simulation',  hint:'Sandbox scenarios, live' },
    { id:'marketplace', label:'Marketplace', hint:'Extension intake' },
    { id:'settings',    label:'Settings',    hint:'Console preferences' },
    { id:'system',      label:'System',      hint:'Executor & telemetry' },
  ];

  const stored = (() => { try { return localStorage.getItem('extrace-v3-rail'); } catch { return null; } })();
  const [collapsed, setCollapsed] = React.useState(stored === '1');
  const toggle = () => {
    setCollapsed(c => {
      const n = !c;
      try { localStorage.setItem('extrace-v3-rail', n ? '1':'0'); } catch {}
      return n;
    });
  };

  const railWidth = collapsed ? 72 : 280;

  return (
    <div style={{
      display:'grid',
      gridTemplateColumns:`${railWidth}px 1fr`,
      minHeight:'100vh',
      fontFamily:"'Manrope', sans-serif",
      color:V2.ink,
      background:V2.paper,
      transition:'grid-template-columns 200ms ease'
    }}>
      {/* ── LEFT RAIL ────────────────────────────────────────────── */}
      <aside style={{
        position:'sticky', top:0, height:'100vh',
        borderRight:`1px solid ${V2.rule}`,
        background:'#000',
        display:'flex', flexDirection:'column',
        overflow:'hidden'
      }}>
        {/* Masthead — clicking the chevron logo toggles collapse */}
        <div
          onClick={toggle}
          title={collapsed?'Expand sidebar':'Collapse sidebar'}
          style={{
            padding: collapsed ? '24px 0 22px' : '26px 22px 22px',
            borderBottom:`1px solid ${V2.rule}`,
            display:'flex', alignItems:'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            cursor:'pointer',
            userSelect:'none',
          }}>
          <div style={{
            display:'flex', alignItems:'center', gap:12,
          }}>
            <LogoMark size={28}/>
            {!collapsed && (
              <div style={{ display:'flex', flexDirection:'column', lineHeight:1.05 }}>
                <span className="display" style={{
                  fontSize:22, fontWeight:800, letterSpacing:'-0.04em', color:V2.ink,
                  textTransform:'uppercase'
                }}>ExTrace</span>
              </div>
            )}
          </div>
        </div>

        {/* Eyebrow inside rail */}
        {!collapsed && (
          <div style={{ padding:'18px 22px 8px', display:'flex', alignItems:'center', gap:10 }}>
            <span style={{ width:14, height:1, background:V2.coral }}/>
            <span className="eyebrow" style={{ color:V2.ink4 }}>Index</span>
          </div>
        )}

        {/* Nav */}
        <nav style={{
          padding: collapsed ? '14px 10px' : '4px 14px',
          display:'flex', flexDirection:'column', gap:0
        }}>
          {NAV.map(item => (
            <NavItem key={item.id} collapsed={collapsed}
              active={page === item.id} item={item}
              onClick={()=>onNavigate(item.id)} />
          ))}
        </nav>

        <div style={{ flex:1 }}/>


      </aside>

      {/* ── MAIN ─────────────────────────────────────────────────── */}
      <main style={{ minWidth:0, display:'flex', flexDirection:'column', background:V2.paper, position:'relative' }}>
        <div style={{ padding:'48px 56px 96px', width:'100%' }}>
          {children}
        </div>
      </main>
    </div>
  );
}

function NavItem({ item, active, onClick, collapsed }) {
  const [hover, setHover] = React.useState(false);
  if (collapsed) {
    return (
      <button onClick={onClick} title={item.label}
        onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}
        style={{
          display:'flex', alignItems:'center', justifyContent:'center',
          background: active ? V2.coral : (hover ? V2.paper3 : 'transparent'),
          border:'none',
          padding:'14px 0', cursor:'pointer', borderRadius:0,
          transition:'all 140ms', width:'100%',
          fontFamily:'inherit',
        }}>
        <span style={{
          width:6, height:6, borderRadius:'50%',
          background: active ? '#0a0a0a' : (hover ? V2.coral : V2.ink3),
          transition:'background 140ms'
        }}/>
      </button>
    );
  }
  return (
    <button onClick={onClick}
      onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}
      style={{
        display:'grid', gridTemplateColumns:'1fr 12px', gap:10,
        alignItems:'center',
        background: active ? V2.coral : (hover ? V2.paper3 : 'transparent'),
        border:'none',
        padding:'14px 14px', cursor:'pointer', borderRadius:0,
        textAlign:'left', transition:'all 140ms', width:'100%',
        fontFamily:'inherit',
        position:'relative',
      }}>
      <div style={{ display:'flex', flexDirection:'column', gap:2, minWidth:0 }}>
        <span className="display" style={{
          fontSize:18, fontWeight:700,
          color: active ? '#0a0a0a' : V2.ink, letterSpacing:'-0.025em',
          textTransform:'uppercase'
        }}>{item.label}</span>
        <span className="mono" style={{
          fontSize:10, color: active ? 'rgba(0,0,0,0.6)' : V2.ink4, letterSpacing:'0.04em',
          whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis'
        }}>{item.hint}</span>
      </div>
      <span style={{
        fontSize:14, color: active ? '#0a0a0a' : (hover ? V2.coral : V2.ink4),
        fontWeight:700, transition:'color 140ms'
      }}>›</span>
    </button>
  );
}

Object.assign(window, { AppShell });
