/**
 * ExTrace — System Page (Shift5 theme)
 * Status overview of executor, catalog, sandbox, telemetry — promoted from rail.
 */

const SYS_SERVICES = [
  {
    num:'01', name:'executor', status:'ready', tone:'ok',
    detail:'Dockerized VS Code · Playwright · Xvfb',
    metrics:[
      ['uptime', '14h 22m'],
      ['version', '0.14.3-rc1'],
      ['port', ':6080'],
      ['queue', '0 jobs'],
    ],
    log:['executor.boot · ok','xvfb :99 attached','playwright session bound','listener up on 6080']
  },
  {
    num:'02', name:'catalog', status:'synced', tone:'ok',
    detail:'Local extension index · 412 entries',
    metrics:[
      ['entries', '412'],
      ['last sync', '2m ago'],
      ['size', '1.84 GB'],
      ['drift', '0'],
    ],
    log:['catalog.sync · 412/412','manifest hash verified','no schema drift','idle']
  },
  {
    num:'03', name:'sandbox', status:'idle', tone:'neutral',
    detail:'Isolated container pool · 4 slots free',
    metrics:[
      ['slots', '4 / 4'],
      ['last run', '6m ago'],
      ['cpu', '2.1%'],
      ['ram', '184 MB'],
    ],
    log:['pool.scaled · 4 ready','last job · job-8f3a2c1','disposed in 412ms','awaiting intake']
  },
  {
    num:'04', name:'telemetry', status:'live', tone:'accent',
    detail:'Stream collector · 1,248 ev/min',
    metrics:[
      ['rate', '1,248 ev/min'],
      ['lag', '< 50ms'],
      ['buffer', '14%'],
      ['retention', '30d'],
    ],
    log:['stream.connect · ok','buffer drained','rate stable','flushing every 2s']
  },
];

function SystemPage() {
  const [selected, setSelected] = React.useState('01');
  const svc = SYS_SERVICES.find(s => s.num === selected) || SYS_SERVICES[0];

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:48 }}>
      {/* HEADER */}
      <header style={{ paddingBottom:32, borderBottom:`1px solid ${V2.rule}` }}>
        <Eyebrow num={4}>System status</Eyebrow>
        <PageTitle style={{ marginTop:18 }}>All systems<br/>operational.</PageTitle>
        <p style={{
          fontSize:15, color:V2.ink3, marginTop:18, maxWidth:560, lineHeight:1.6
        }}>
          Live state of the appliance. Executor, catalog, sandbox pool and telemetry stream — sampled every 2 seconds.
        </p>
      </header>

      {/* OVERVIEW STRIP */}
      <section style={{
        display:'grid', gridTemplateColumns:'repeat(4,1fr)',
        border:`1px solid ${V2.rule}`,
        background:V2.paper2,
      }}>
        {SYS_SERVICES.map((s,i)=>{
          const sel = s.num === selected;
          const dot = s.tone==='ok'?V2.ok : s.tone==='accent'?V2.coral : V2.ink3;
          return (
            <button key={s.num} onClick={()=>setSelected(s.num)}
              style={{
                background: sel ? V2.coral : 'transparent',
                color: sel ? '#0a0a0a' : V2.ink,
                border:'none',
                borderRight: i<SYS_SERVICES.length-1 ? `1px solid ${V2.rule}` : 'none',
                padding:'24px 22px', textAlign:'left', cursor:'pointer',
                display:'flex', flexDirection:'column', gap:14,
                fontFamily:'inherit', transition:'background 140ms',
                position:'relative'
              }}>
              <div style={{ display:'flex', alignItems:'center', justifyContent:'flex-end' }}>
                <span style={{
                  width:8, height:8, borderRadius:'50%',
                  background: sel ? '#0a0a0a' : dot,
                  boxShadow: sel ? 'none' : `0 0 8px ${dot}`
                }}/>
              </div>
              <div className="display" style={{
                fontSize:32, fontWeight:800, letterSpacing:'-0.04em', lineHeight:0.95,
                textTransform:'uppercase',
                color: sel ? '#0a0a0a' : V2.ink
              }}>{s.name}</div>
              <div className="mono" style={{
                fontSize:11, fontWeight:600, letterSpacing:'0.12em', textTransform:'uppercase',
                color: sel ? 'rgba(0,0,0,0.7)' : (s.tone==='ok'?V2.ok : s.tone==='accent'?V2.coral : V2.ink3)
              }}>· {s.status}</div>
            </button>
          );
        })}
      </section>

      {/* DETAIL */}
      <section style={{ display:'grid', gridTemplateColumns:'1fr 360px', gap:28 }}>
        <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
          <div style={{ display:'flex', alignItems:'baseline', gap:14 }}>
            <Eyebrow>Service</Eyebrow>
            <span className="mono" style={{ fontSize:11, color:V2.ink3 }}>›</span>
            <span className="mono" style={{ fontSize:12, color:V2.coral, letterSpacing:'0.1em', textTransform:'uppercase' }}>
              {svc.name}
            </span>
          </div>
          <SectionTitle>{svc.detail}</SectionTitle>

          {/* metrics grid */}
          <div style={{
            display:'grid', gridTemplateColumns:'repeat(4,1fr)',
            border:`1px solid ${V2.rule}`,
            background:V2.paper2
          }}>
            {svc.metrics.map(([k,v],i)=>(
              <div key={k} style={{
                padding:'22px 20px',
                borderRight: i<svc.metrics.length-1 ? `1px solid ${V2.rule}` : 'none',
              }}>
                <Eyebrow>{k}</Eyebrow>
                <div className="display" style={{
                  fontSize:30, fontWeight:800, color:V2.ink,
                  letterSpacing:'-0.035em', marginTop:10, lineHeight:1
                }}>{v}</div>
              </div>
            ))}
          </div>

          {/* live log */}
          <div style={{
            border:`1px solid ${V2.rule}`, background:'#000',
            padding:'18px 20px',
          }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:14 }}>
              <Eyebrow>Live log</Eyebrow>
              <span style={{ display:'flex', alignItems:'center', gap:6 }}>
                <span style={{ width:6, height:6, borderRadius:'50%', background:V2.coral, animation:'pulse 1.4s ease-in-out infinite' }}/>
                <span className="mono" style={{ fontSize:10, color:V2.ink3, letterSpacing:'0.12em', textTransform:'uppercase' }}>streaming</span>
              </span>
            </div>
            <div className="mono" style={{ fontSize:12, lineHeight:1.9, color:V2.ink2, letterSpacing:'0.02em' }}>
              {svc.log.map((line,i)=>(
                <div key={i} style={{ display:'grid', gridTemplateColumns:'70px 12px 1fr', gap:10 }}>
                  <span style={{ color:V2.ink4 }}>14:{String(11+i).padStart(2,'0')}:{String(2+i*7).padStart(2,'0')}</span>
                  <span style={{ color:V2.coral }}>›</span>
                  <span>{line}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* SIDEBAR — system inventory */}
        <aside style={{ display:'flex', flexDirection:'column', gap:0,
          border:`1px solid ${V2.rule}`, background:V2.paper2 }}>
          <div style={{ padding:'18px 20px', borderBottom:`1px solid ${V2.rule}`, background:V2.paper3 }}>
            <Eyebrow>Inventory</Eyebrow>
          </div>
          {[
            ['hostname','extrace.local'],
            ['platform','linux/x86_64'],
            ['kernel','6.6.12-amd64'],
            ['docker','25.0.3'],
            ['python','3.11.7'],
            ['node','20.11.1'],
            ['disk','64% / 256 GB'],
            ['session','single-user'],
          ].map(([k,v])=>(
            <div key={k} style={{
              display:'grid', gridTemplateColumns:'1fr auto', gap:10,
              padding:'12px 20px', borderBottom:`1px dashed ${V2.rule}`,
              alignItems:'baseline'
            }}>
              <span className="eyebrow">{k}</span>
              <span className="mono" style={{ fontSize:12, color:V2.ink, letterSpacing:'0.02em' }}>{v}</span>
            </div>
          ))}
          <div style={{ padding:'18px 20px', display:'flex', flexDirection:'column', gap:10 }}>
            <GhostButton style={{ width:'100%', justifyContent:'center' }}>Restart executor</GhostButton>
            <GhostButton style={{ width:'100%', justifyContent:'center' }}>Re-sync catalog</GhostButton>
          </div>
        </aside>
      </section>
    </div>
  );
}

Object.assign(window, { SystemPage });
