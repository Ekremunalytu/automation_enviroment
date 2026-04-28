/**
 * ExTrace — Settings Page (Shift5 theme)
 * Single-user appliance settings: profile, executor, telemetry, danger zone.
 */

function SettingsPage() {
  const [sec, setSec] = React.useState('general');
  const [autoAnalyze, setAutoAnalyze] = React.useState(true);
  const [retainArtifacts, setRetainArtifacts] = React.useState(true);
  const [verboseLogs, setVerboseLogs] = React.useState(false);
  const [strictNet, setStrictNet] = React.useState(true);
  const [theme, setTheme] = React.useState('shift5');

  const SECTIONS = [
    { id:'general',   num:'01', label:'General',  hint:'Console & appearance' },
    { id:'executor',  num:'02', label:'Executor', hint:'Sandbox runtime' },
    { id:'telemetry', num:'03', label:'Telemetry',hint:'Stream & retention' },
    { id:'danger',    num:'04', label:'Danger',   hint:'Reset & purge' },
  ];

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:48 }}>
      {/* HEADER */}
      <header style={{ paddingBottom:32, borderBottom:`1px solid ${V2.rule}` }}>
        <Eyebrow num={5}>Settings</Eyebrow>
        <PageTitle style={{ marginTop:18 }}>Configure<br/>the appliance.</PageTitle>
        <p style={{
          fontSize:15, color:V2.ink3, marginTop:18, maxWidth:560, lineHeight:1.6
        }}>
          Single-operator preferences. Changes are local to this instance and persist across sessions.
        </p>
      </header>

      <section style={{ display:'grid', gridTemplateColumns:'260px 1fr', gap:32, alignItems:'start' }}>
        {/* SECTION RAIL */}
        <nav style={{
          border:`1px solid ${V2.rule}`, background:V2.paper2,
          display:'flex', flexDirection:'column'
        }}>
          {SECTIONS.map((s, i)=>{
            const a = sec === s.id;
            return (
              <button key={s.id} onClick={()=>setSec(s.id)}
                style={{
                  background: a ? V2.coral : 'transparent',
                  color: a ? '#0a0a0a' : V2.ink,
                  border:'none',
                  borderBottom: i<SECTIONS.length-1 ? `1px solid ${V2.rule}` : 'none',
                  padding:'18px 18px', textAlign:'left', cursor:'pointer',
                  display:'flex', alignItems:'center', gap:14,
                  fontFamily:'inherit', transition:'background 140ms'
                }}>
                <div style={{ display:'flex', flexDirection:'column', gap:3 }}>
                  <span className="display" style={{
                    fontSize:18, fontWeight:700, letterSpacing:'-0.025em',
                    textTransform:'uppercase', lineHeight:1
                  }}>{s.label}</span>
                  <span className="mono" style={{
                    fontSize:10, letterSpacing:'0.06em',
                    color: a ? 'rgba(0,0,0,0.6)' : V2.ink4
                  }}>{s.hint}</span>
                </div>
              </button>
            );
          })}
        </nav>

        {/* CONTENT */}
        <div style={{ display:'flex', flexDirection:'column', gap:24 }}>
          {sec === 'general' && (
            <>
              <SectionTitle>General</SectionTitle>
              <Group label="Profile">
                <FormRow k="Operator name" desc="Stamped on exported reports.">
                  <Field placeholder="analyst-01" inputStyle={{ maxWidth:340 }}/>
                </FormRow>
                <FormRow k="Time zone" desc="All timestamps render in this zone.">
                  <SelectStub value="UTC+03:00 · Istanbul"/>
                </FormRow>
              </Group>
              <Group label="Appearance">
                <FormRow k="Theme" desc="Visual treatment of the console.">
                  <Segmented value={theme} onChange={setTheme}
                    options={[['shift5','Shift5'],['parchment','Parchment'],['terminal','Terminal']]}/>
                </FormRow>
                <FormRow k="Density" desc="Row height across tables and ledgers.">
                  <Segmented value="comfortable" onChange={()=>{}}
                    options={[['compact','Compact'],['comfortable','Comfortable'],['spacious','Spacious']]}/>
                </FormRow>
              </Group>
            </>
          )}

          {sec === 'executor' && (
            <>
              <SectionTitle>Executor runtime</SectionTitle>
              <Group label="Sandbox">
                <Toggle k="Auto-analyze on download" desc="Pipe new catalog entries straight into a sandbox run."
                  checked={autoAnalyze} onChange={setAutoAnalyze}/>
                <Toggle k="Strict network mode" desc="Block all outbound requests except to whitelisted hosts."
                  checked={strictNet} onChange={setStrictNet}/>
                <FormRow k="Pool size" desc="Concurrent sandbox containers.">
                  <Segmented value="4" onChange={()=>{}}
                    options={[['2','2'],['4','4'],['8','8'],['16','16']]}/>
                </FormRow>
                <FormRow k="Job timeout" desc="Auto-abort after this duration.">
                  <Field placeholder="600s" inputStyle={{ maxWidth:200 }}/>
                </FormRow>
              </Group>
            </>
          )}

          {sec === 'telemetry' && (
            <>
              <SectionTitle>Telemetry stream</SectionTitle>
              <Group label="Collection">
                <Toggle k="Verbose logs" desc="Keep raw process traces (ptrace, syscall) on disk."
                  checked={verboseLogs} onChange={setVerboseLogs}/>
                <Toggle k="Retain artifacts" desc="Persist downloaded extension binaries after analysis."
                  checked={retainArtifacts} onChange={setRetainArtifacts}/>
                <FormRow k="Retention" desc="Auto-purge events older than this.">
                  <Segmented value="30" onChange={()=>{}}
                    options={[['7','7d'],['30','30d'],['90','90d'],['inf','∞']]}/>
                </FormRow>
                <FormRow k="Buffer" desc="Memory window before flush.">
                  <Field placeholder="2048 events" inputStyle={{ maxWidth:240 }}/>
                </FormRow>
              </Group>
            </>
          )}

          {sec === 'danger' && (
            <>
              <SectionTitle>Danger zone</SectionTitle>
              <div style={{
                border:`1px solid ${V2.coral}`,
                background:'rgba(255,92,66,0.05)',
                padding:'24px 26px',
                display:'flex', flexDirection:'column', gap:18
              }}>
                <Eyebrow style={{ color:V2.coral }}>Irreversible</Eyebrow>
                <DangerRow
                  k="Clear catalog"
                  desc="Drop all 412 catalog entries and downloaded artifacts. Reports are kept."
                  cta="Clear"/>
                <DangerRow
                  k="Wipe reports"
                  desc="Delete all activation reports. Catalog entries remain available for re-analysis."
                  cta="Wipe"/>
                <DangerRow
                  k="Factory reset"
                  desc="Return appliance to first-boot state. Catalog, reports, settings — all gone."
                  cta="Reset"/>
              </div>
            </>
          )}

          <div style={{ display:'flex', justifyContent:'flex-end', gap:10, paddingTop:14, borderTop:`1px solid ${V2.rule}` }}>
            <GhostButton>Discard</GhostButton>
            <SolidButton>Save changes</SolidButton>
          </div>
        </div>
      </section>
    </div>
  );
}

function Group({ label, children }) {
  return (
    <div style={{
      border:`1px solid ${V2.rule}`, background:V2.paper2,
    }}>
      <div style={{ padding:'14px 20px', borderBottom:`1px solid ${V2.rule}`, background:V2.paper3 }}>
        <Eyebrow>{label}</Eyebrow>
      </div>
      <div style={{ display:'flex', flexDirection:'column' }}>
        {React.Children.map(children, (c, i) => (
          <div style={{ borderBottom: i < React.Children.count(children)-1 ? `1px solid ${V2.rule}` : 'none' }}>
            {c}
          </div>
        ))}
      </div>
    </div>
  );
}

function FormRow({ k, desc, children }) {
  return (
    <div style={{
      display:'grid', gridTemplateColumns:'1fr auto', gap:24,
      padding:'18px 20px', alignItems:'center'
    }}>
      <div>
        <div className="display" style={{
          fontSize:15, fontWeight:700, color:V2.ink, letterSpacing:'-0.015em'
        }}>{k}</div>
        <div style={{ fontSize:12.5, color:V2.ink3, marginTop:4, maxWidth:420, lineHeight:1.5 }}>{desc}</div>
      </div>
      <div>{children}</div>
    </div>
  );
}

function Toggle({ k, desc, checked, onChange }) {
  return (
    <div style={{
      display:'grid', gridTemplateColumns:'1fr auto', gap:24,
      padding:'18px 20px', alignItems:'center'
    }}>
      <div>
        <div className="display" style={{
          fontSize:15, fontWeight:700, color:V2.ink, letterSpacing:'-0.015em'
        }}>{k}</div>
        <div style={{ fontSize:12.5, color:V2.ink3, marginTop:4, maxWidth:480, lineHeight:1.5 }}>{desc}</div>
      </div>
      <button onClick={()=>onChange(!checked)} aria-pressed={checked}
        style={{
          width:52, height:28, padding:0, border:`1px solid ${checked?V2.coral:V2.rule2}`,
          background: checked ? V2.coral : V2.paper3,
          position:'relative', cursor:'pointer', borderRadius:0,
          transition:'all 140ms'
        }}>
        <span style={{
          position:'absolute', top:2, left: checked ? 26 : 2,
          width:22, height:22, background: checked ? '#0a0a0a' : V2.ink2,
          transition:'left 160ms'
        }}/>
      </button>
    </div>
  );
}

function Segmented({ value, onChange, options }) {
  return (
    <div style={{ display:'inline-flex', border:`1px solid ${V2.rule2}` }}>
      {options.map(([v,l],i)=>{
        const a = v === value;
        return (
          <button key={v} onClick={()=>onChange(v)}
            style={{
              background: a ? V2.coral : 'transparent',
              color: a ? '#0a0a0a' : V2.ink,
              border:'none',
              borderLeft: i>0 ? `1px solid ${V2.rule2}` : 'none',
              padding:'9px 14px', cursor:'pointer',
              fontFamily:"'JetBrains Mono', monospace",
              fontSize:11, fontWeight:600, letterSpacing:'0.08em', textTransform:'uppercase',
              transition:'background 140ms'
            }}>
            {l}
          </button>
        );
      })}
    </div>
  );
}

function SelectStub({ value }) {
  return (
    <div style={{
      display:'inline-flex', alignItems:'center', justifyContent:'space-between', gap:14,
      padding:'10px 14px', minWidth:280,
      border:`1px solid ${V2.rule2}`, background:V2.paper3,
      fontFamily:"'JetBrains Mono', monospace", fontSize:12.5, color:V2.ink,
      cursor:'pointer'
    }}>
      <span>{value}</span>
      <span style={{ color:V2.coral }}>▾</span>
    </div>
  );
}

function DangerRow({ k, desc, cta }) {
  return (
    <div style={{
      display:'grid', gridTemplateColumns:'1fr auto', gap:18,
      paddingTop:14, alignItems:'center',
      borderTop:`1px dashed rgba(255,92,66,0.3)`
    }}>
      <div>
        <div className="display" style={{
          fontSize:15, fontWeight:700, color:V2.ink, letterSpacing:'-0.015em'
        }}>{k}</div>
        <div style={{ fontSize:12.5, color:V2.ink3, marginTop:4, maxWidth:480, lineHeight:1.5 }}>{desc}</div>
      </div>
      <button style={{
        background:'transparent', border:`1px solid ${V2.coral}`, color:V2.coral,
        padding:'10px 18px', fontSize:11, fontWeight:700, letterSpacing:'0.1em',
        textTransform:'uppercase', cursor:'pointer', borderRadius:0,
        fontFamily:'inherit', transition:'all 140ms'
      }}
      onMouseEnter={e=>{ e.currentTarget.style.background = V2.coral; e.currentTarget.style.color = '#0a0a0a'; }}
      onMouseLeave={e=>{ e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = V2.coral; }}>
        {cta}
      </button>
    </div>
  );
}

Object.assign(window, { SettingsPage });
