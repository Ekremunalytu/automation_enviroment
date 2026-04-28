/**
 * ExTrace — Marketplace Page (v3)
 * Intake worksheet: search at top, result list as index card stack.
 */
const MKT_RESULTS = [
  { publisher:'ms-python',  name:'python',          displayName:'Python',         version:'2024.4.1', description:'Python language support — interpreter, linter, formatter, and debugger.', installs:118_200_000, rating:4.7 },
  { publisher:'esbenp',     name:'prettier-vscode', displayName:'Prettier',       version:'11.0.0',   description:'Opinionated code formatter for JS, TS, CSS, HTML and more.', installs:48_500_000, rating:4.3 },
  { publisher:'dbaeumer',   name:'vscode-eslint',   displayName:'ESLint',         version:'3.0.10',   description:'Integrates ESLint into VS Code with inline diagnostics and auto-fix.', installs:32_100_000, rating:4.1 },
  { publisher:'github',     name:'copilot',         displayName:'GitHub Copilot', version:'1.214.0',  description:'AI-powered code completions. Requires GitHub authentication.', installs:22_400_000, rating:3.9 },
];

function fmtInstalls(n) {
  if (n >= 1_000_000) return (n/1_000_000).toFixed(1).replace(/\.0$/,'') + 'M';
  if (n >= 1_000) return (n/1_000).toFixed(0) + 'K';
  return String(n);
}

function MarketplacePage({ onAnalyze }) {
  const [query, setQuery] = React.useState('');
  const [submitted, setSubmitted] = React.useState('');
  const [results, setResults] = React.useState([]);
  const [ready, setReady] = React.useState({});
  const [busy, setBusy] = React.useState({});

  const onSearch = e => {
    e.preventDefault();
    if (!query.trim()) return;
    const q = query.trim().toLowerCase();
    setSubmitted(query.trim());
    const filtered = MKT_RESULTS.filter(r =>
      r.displayName.toLowerCase().includes(q) || r.name.includes(q)
    );
    setResults(filtered.length ? filtered : MKT_RESULTS);
  };

  const onDownload = key => {
    setBusy(b => ({...b, [key]:true}));
    setTimeout(() => {
      setBusy(b => { const n={...b}; delete n[key]; return n; });
      setReady(r => ({...r, [key]:true}));
    }, 1200);
  };

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:40 }}>
      {/* ── HEADER ──────────────────────────────────────────────── */}
      <header style={{
        paddingBottom:24, borderBottom:`1px solid ${V2.rule2}`,
      }}>
        <Eyebrow num={1}>Extension intake</Eyebrow>
        <PageTitle style={{ marginTop:14 }}>Find, download, analyze.</PageTitle>
        <p style={{
          fontSize:15, color:V2.ink3, marginTop:14, maxWidth:580, lineHeight:1.6
        }}>
          Search the VS Code marketplace, shortlist a candidate, then hand it to the sandbox.
          Each download adds one entry to the local catalog.
        </p>
      </header>

      {/* ── SEARCH ──────────────────────────────────────────────── */}
      <section>
        <Eyebrow num={2} style={{ marginBottom:12 }}>Search marketplace</Eyebrow>
        <form onSubmit={onSearch} style={{
          display:'grid', gridTemplateColumns:'auto 1fr auto', gap:0,
          alignItems:'stretch', maxWidth:720,
          border:`1px solid ${V2.ink}`, borderRadius:2, background:V2.card,
        }}>
          <div style={{
            padding:'0 14px', display:'flex', alignItems:'center',
            borderRight:`1px solid ${V2.rule}`, background:V2.paper2,
          }}>
            <span className="mono" style={{ fontSize:12, color:V2.ink3 }}>find ›</span>
          </div>
          <input placeholder="python, eslint, prettier, github copilot…"
            value={query} onChange={e=>setQuery(e.target.value)}
            style={{
              background:'transparent', border:'none', outline:'none',
              padding:'14px 16px', fontSize:15, color:V2.ink,
              fontFamily:"'JetBrains Mono', monospace",
              fontVariantLigatures:'none',
            }}/>
          <button type="submit" style={{
            background:V2.ink, color:V2.paper, border:'none',
            padding:'0 22px', fontSize:13, fontWeight:500, cursor:'pointer',
            fontFamily:'inherit',
          }}>Search ↵</button>
        </form>

        <div style={{ marginTop:14, display:'flex', gap:8, flexWrap:'wrap' }}>
          <span className="mono" style={{ fontSize:11, color:V2.ink3, marginRight:4, alignSelf:'center' }}>try:</span>
          {['python', 'copilot', 'eslint', 'prettier'].map(q=>(
            <button key={q} onClick={()=>{ setQuery(q); setTimeout(()=>{ setSubmitted(q); setResults(MKT_RESULTS.filter(r=>r.displayName.toLowerCase().includes(q)||r.name.includes(q))); },0); }}
              style={{
                background:V2.paper2, border:`1px solid ${V2.rule}`, borderRadius:2,
                padding:'4px 10px', fontSize:11.5, color:V2.ink2,
                cursor:'pointer', fontFamily:"'JetBrains Mono', monospace",
                transition:'all 140ms'
              }}
              onMouseEnter={e=>{ e.currentTarget.style.borderColor=V2.ink; e.currentTarget.style.background=V2.card; }}
              onMouseLeave={e=>{ e.currentTarget.style.borderColor=V2.rule; e.currentTarget.style.background=V2.paper2; }}>
              {q}
            </button>
          ))}
        </div>
      </section>

      {/* ── RESULTS ─────────────────────────────────────────────── */}
      <section>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-end', marginBottom:16, gap:16, flexWrap:'wrap' }}>
          <div>
            <Eyebrow num={3}>Results</Eyebrow>
            <SectionTitle style={{ marginTop:10 }}>
              {!submitted ? 'Awaiting query' : results.length===0 ? 'No matches' : `“${submitted}” · ${results.length} matches`}
            </SectionTitle>
          </div>
          {submitted && results.length > 0 && (
            <span className="mono" style={{ fontSize:12, color:V2.ink3 }}>
              sorted by installs
            </span>
          )}
        </div>

        {!submitted ? (
          <EmptyState eyebrow="Ready" title="No query yet"
            body="Enter an extension name or keyword above to populate results from the marketplace catalog."/>
        ) : results.length === 0 ? (
          <EmptyState eyebrow="Empty" title="Nothing matched" body="Try a different keyword."/>
        ) : (
          <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
            {results.map((ext, i) => {
              const key = `${ext.publisher}.${ext.name}`;
              const isReady = ready[key];
              const isBusy = busy[key];
              return (
                <article key={key} style={{
                  display:'grid', gridTemplateColumns:'48px 1fr auto',
                  gap:20, alignItems:'flex-start',
                  padding:'18px 20px',
                  background:V2.card, border:`1px solid ${V2.rule}`, borderRadius:2,
                  transition:'border-color 140ms',
                }}
                  onMouseEnter={e=>{ e.currentTarget.style.borderColor = V2.rule2; }}
                  onMouseLeave={e=>{ e.currentTarget.style.borderColor = V2.rule; }}>
                  {/* index number */}
                  <div className="mono" style={{
                    fontSize:11, color:V2.ink4, paddingTop:2,
                    textAlign:'left', letterSpacing:'0.05em',
                    borderRight:`1px dashed ${V2.rule}`,
                    paddingRight:12, minHeight:60
                  }}>
                    {String(i+1).padStart(2,'0')}
                  </div>

                  <div style={{ minWidth:0 }}>
                    <div style={{ display:'flex', alignItems:'baseline', gap:10, flexWrap:'wrap' }}>
                      <div className="serif" style={{
                        fontSize:22, fontWeight:500, color:V2.ink, letterSpacing:'-0.01em'
                      }}>{ext.displayName}</div>
                      {isReady && <Badge tone="ok">Ready</Badge>}
                      {!isReady && <Badge tone="neutral">Marketplace</Badge>}
                    </div>
                    <div className="mono" style={{
                      fontSize:11.5, color:V2.ink3, marginTop:6
                    }}>{ext.publisher}.{ext.name}</div>
                    <p style={{
                      fontSize:13.5, color:V2.ink2, lineHeight:1.55,
                      marginTop:10, maxWidth:600
                    }}>{ext.description}</p>

                    <div style={{
                      marginTop:12, display:'flex', gap:0, alignItems:'center',
                      flexWrap:'wrap',
                    }}>
                      <Meta k="version" v={`v${ext.version}`}/>
                      <Divider/>
                      <Meta k="installs" v={fmtInstalls(ext.installs)}/>
                      <Divider/>
                      <Meta k="rating" v={`${ext.rating.toFixed(1)} / 5`}/>
                    </div>
                  </div>

                  <div style={{ display:'flex', flexDirection:'column', gap:8, alignItems:'flex-end' }}>
                    {!isReady ? (
                      <SolidButton disabled={isBusy} onClick={()=>onDownload(key)}>
                        {isBusy ? (
                          <>
                            <span className="mono" style={{ fontSize:11 }}>⟳</span>
                            <span>Downloading…</span>
                          </>
                        ) : (
                          <>
                            <span>Download</span>
                            <span className="mono" style={{ fontSize:11, opacity:0.6 }}>↓</span>
                          </>
                        )}
                      </SolidButton>
                    ) : (
                      <SolidButton onClick={()=>onAnalyze && onAnalyze(ext)}>
                        <span>Analyze</span>
                        <span className="mono" style={{ fontSize:11, opacity:0.6 }}>→</span>
                      </SolidButton>
                    )}
                    {isReady && (
                      <span className="mono" style={{ fontSize:10, color:V2.ok, letterSpacing:'0.08em', textTransform:'uppercase' }}>
                        ● in catalog
                      </span>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

function Meta({ k, v }) {
  return (
    <span style={{ display:'inline-flex', flexDirection:'column', gap:2, padding:'0 14px 0 0' }}>
      <span className="eyebrow">{k}</span>
      <span className="mono" style={{ fontSize:12.5, color:V2.ink, fontWeight:500 }}>{v}</span>
    </span>
  );
}
function Divider() {
  return <span style={{ width:1, height:24, background:V2.rule, margin:'0 14px 0 0' }}/>;
}

Object.assign(window, { MarketplacePage });
