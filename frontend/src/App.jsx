import { useEffect, useMemo, useRef, useState } from 'react'

const API = '/api/v1'

const NAVIGATION = [
  ['home', 'Overview', '⌂'],
  ['research', 'New research', '✦'],
  ['library', 'Research library', '▤'],
  ['knowledge', 'Knowledge base', '◇'],
  ['analytics', 'Analytics', '⌁'],
  ['playground', 'Agent playground', '⌘'],
]

const AGENT_DEFS = [
  ['researcher', 'Research Agent', 'Finds and evaluates credible sources', 'R'],
  ['teacher', 'Teacher Agent', 'Builds a structured explanation', 'T'],
  ['simplifier', 'Simplifier Agent', 'Translates ideas into plain language', 'S'],
  ['student', 'Student Agent', 'Creates concise revision notes', 'N'],
  ['examiner', 'Examiner Agent', 'Tests understanding and application', 'E'],
  ['reporter', 'Report Compiler', 'Assembles the final research artifact', 'C'],
]

const TOPICS = [
  ['Frontier AI', 'How are small language models changing edge computing?'],
  ['Climate', 'What are the most promising long-duration energy storage technologies?'],
  ['Biotech', 'How is CRISPR being used in approved medical treatments?'],
  ['Economics', 'What evidence exists for a four-day work week?'],
]

const MODELS = [
  'openrouter/meta-llama/llama-3.3-70b-instruct',
  'openrouter/openai/gpt-4.1',
  'openrouter/anthropic/claude-sonnet-4',
  'openrouter/google/gemini-2.5-pro',
]

function App() {
  const [page, setPage] = useState('home')
  const [theme, setTheme] = useState(() => localStorage.getItem('research-theme') || 'light')
  const [mobileNav, setMobileNav] = useState(false)
  const [reports, setReports] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [activeReport, setActiveReport] = useState(null)

  const refresh = async () => {
    const [reportsResponse, analyticsResponse] = await Promise.allSettled([
      api('/reports'),
      api('/analytics'),
    ])
    if (reportsResponse.status === 'fulfilled') setReports(reportsResponse.value.items)
    if (analyticsResponse.status === 'fulfilled') setAnalytics(analyticsResponse.value)
  }

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('research-theme', theme)
  }, [theme])

  useEffect(() => { refresh() }, [])

  const openReport = async (id) => {
    try {
      setActiveReport(await api(`/reports/${id}`))
      setPage('research')
    } catch (error) {
      console.error(error)
    }
  }

  return (
    <div className="app">
      <aside className={`sidebar ${mobileNav ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark"><span>R</span></div>
          <div><strong>ResearchOS</strong><small>Intelligence workspace</small></div>
          <button className="mobile-close" onClick={() => setMobileNav(false)}>×</button>
        </div>

        <nav>
          <p className="nav-label">Workspace</p>
          {NAVIGATION.map(([id, label, icon]) => (
            <button
              key={id}
              className={page === id ? 'active' : ''}
              onClick={() => { setPage(id); setMobileNav(false) }}
            >
              <span className="nav-icon">{icon}</span>{label}
              {id === 'library' && reports.length > 0 && <em>{reports.length}</em>}
            </button>
          ))}
          <p className="nav-label second">Manage</p>
          <button className={page === 'settings' ? 'active' : ''} onClick={() => setPage('settings')}>
            <span className="nav-icon">⚙</span>Settings
          </button>
          <a href="/docs" target="_blank" rel="noreferrer"><span className="nav-icon">↗</span>API documentation</a>
        </nav>

        <div className="sidebar-foot">
          <div className="workspace-usage">
            <div><span>Monthly research</span><strong>{analytics?.total_reports || 0} / 100</strong></div>
            <div className="meter"><i style={{ width: `${Math.min(analytics?.total_reports || 0, 100)}%` }} /></div>
            <small>Resets in 12 days</small>
          </div>
          <div className="profile">
            <div className="avatar">AR</div>
            <div><strong>Alex Researcher</strong><small>Personal workspace</small></div>
            <span>•••</span>
          </div>
        </div>
      </aside>
      {mobileNav && <button className="nav-scrim" onClick={() => setMobileNav(false)} />}

      <div className="main-shell">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileNav(true)}>☰</button>
          <div className="crumb"><span>ResearchOS</span><b>/</b>{pageTitle(page)}</div>
          <div className="top-actions">
            <button className="search-button"><span>⌕</span><label>Search workspace</label><kbd>⌘ K</kbd></button>
            <button className="icon-button" aria-label="Toggle theme" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
              {theme === 'light' ? '☾' : '☀'}
            </button>
            <button className="icon-button notification" aria-label="Notifications">♢<i /></button>
          </div>
        </header>

        <main>
          {(page === 'home' || page === 'research') && (
            <ResearchWorkspace
              initialReport={activeReport}
              reports={reports}
              analytics={analytics}
              onComplete={refresh}
              onOpenReport={openReport}
              onNavigate={setPage}
            />
          )}
          {page === 'library' && <Library reports={reports} onOpen={openReport} onRefresh={refresh} />}
          {page === 'knowledge' && <Knowledge />}
          {page === 'analytics' && <Analytics data={analytics} reports={reports} />}
          {page === 'playground' && <Playground />}
          {page === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  )
}

function ResearchWorkspace({ initialReport, reports, analytics, onComplete, onOpenReport, onNavigate }) {
  const [topic, setTopic] = useState('')
  const [model, setModel] = useState(MODELS[0])
  const [advanced, setAdvanced] = useState(false)
  const [loading, setLoading] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [events, setEvents] = useState([])
  const [report, setReport] = useState(initialReport)
  const [error, setError] = useState('')
  const streamRef = useRef(null)

  useEffect(() => { if (initialReport) setReport(initialReport) }, [initialReport])
  useEffect(() => () => streamRef.current?.close(), [])

  const agentState = useMemo(() => {
    const completed = report?.status === 'completed'
    const state = Object.fromEntries(AGENT_DEFS.map(([key]) => [key, { status: completed ? 'completed' : 'waiting', progress: completed ? 100 : 0 }]))
    events.forEach((event) => {
      if (event.type === 'agent' && event.agent && state[event.agent]) {
        state[event.agent] = {
          ...state[event.agent],
          status: event.status,
          progress: event.status === 'completed' ? 100 : event.status === 'running' ? Math.max(24, event.progress || 24) : 0,
          output: event.data?.output,
        }
      }
    })
    return state
  }, [events])

  const runResearch = async (event) => {
    event?.preventDefault()
    if (!topic.trim() || loading) return
    setLoading(true)
    setError('')
    setEvents([])
    setReport(null)
    streamRef.current?.close()
    try {
      const started = await api('/research', {
        method: 'POST',
        body: JSON.stringify({
          topic: topic.trim(),
          model,
          search_depth: advanced ? 'advanced' : 'basic',
          number_of_sources: advanced ? 15 : 10,
          template: 'professional',
        }),
      })
      setJobId(started.job_id)
      const stream = new EventSource(started.stream_url)
      streamRef.current = stream
      const receive = async (message) => {
        const incoming = JSON.parse(message.data)
        setEvents((current) => current.some((item) => item.sequence === incoming.sequence) ? current : [...current, incoming])
        if (incoming.type === 'job' && incoming.status === 'completed') {
          stream.close()
          const completed = await api(`/reports/${started.job_id}`)
          setReport(completed)
          setLoading(false)
          onComplete()
        }
        if (incoming.type === 'job' && incoming.status === 'failed') {
          stream.close()
          setError(incoming.data?.error || incoming.message)
          setLoading(false)
        }
      }
      ;['job', 'agent', 'recovery', 'log'].forEach((name) => stream.addEventListener(name, receive))
      stream.onerror = () => {
        if (stream.readyState === EventSource.CLOSED) return
      }
    } catch (requestError) {
      setError(requestError.message)
      setLoading(false)
    }
  }

  if (loading || (report && jobId)) {
    return (
      <ExecutionView
        topic={topic || report?.topic}
        events={events}
        agentState={agentState}
        report={report}
        error={error}
        jobId={jobId || report?.id}
        onNew={() => { setReport(null); setJobId(null); setEvents([]); setTopic('') }}
      />
    )
  }

  if (report) {
    return <ExecutionView topic={report.topic} events={report.events || []} agentState={agentState} report={report} jobId={report.id} onNew={() => setReport(null)} />
  }

  return (
    <div className="page overview-page">
      <section className="welcome">
        <div>
          <span className="status-pill"><i /> All research systems operational</span>
          <h1>What do you want to<br /><em>understand deeply?</em></h1>
          <p>Five specialized AI agents research, teach, simplify, synthesize, and challenge a topic—while you watch the evidence take shape.</p>
        </div>
        <div className="hero-orbit" aria-hidden="true">
          <div className="orbit orbit-one"><span>R</span><span>T</span></div>
          <div className="orbit orbit-two"><span>S</span><span>E</span><span>N</span></div>
          <div className="orbit-core">✦</div>
        </div>
      </section>

      <section className="research-composer">
        <form onSubmit={runResearch}>
          <textarea
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Ask a complex research question…"
            rows="3"
            autoFocus
          />
          <div className="composer-footer">
            <div className="composer-options">
              <label className="select-wrap"><span className="provider-dot" /> 
                <select value={model} onChange={(event) => setModel(event.target.value)}>
                  {MODELS.map((item) => <option key={item} value={item}>{shortModel(item)}</option>)}
                </select>
              </label>
              <button type="button" className={advanced ? 'option active' : 'option'} onClick={() => setAdvanced(!advanced)}>
                <span>◉</span> Deep search
              </button>
              <button type="button" className="option"><span>＋</span> Add context</button>
            </div>
            <button className="run-button" disabled={!topic.trim()}>
              Begin research <span>→</span>
            </button>
          </div>
        </form>
      </section>

      <div className="suggestion-head"><span>Explore an idea</span><small>Curated starting points</small></div>
      <section className="suggestion-grid">
        {TOPICS.map(([category, text], index) => (
          <button key={category} onClick={() => setTopic(text)}>
            <span className={`suggestion-icon color-${index}`}>{['⌁', '◌', '⌬', '◫'][index]}</span>
            <div><small>{category}</small><strong>{text}</strong></div><b>↗</b>
          </button>
        ))}
      </section>

      <section className="dashboard-row">
        <div className="recent-panel">
          <div className="section-title"><div><h2>Recent research</h2><p>Continue where your agents left off</p></div><button onClick={() => onNavigate('library')}>View library →</button></div>
          {reports.length ? reports.slice(0, 4).map((item) => (
            <button className="recent-item" key={item.id} onClick={() => onOpenReport(item.id)}>
              <span className={`doc-icon ${item.status}`}>▤</span>
              <div><strong>{item.topic}</strong><small>{relativeTime(item.created_at)} · {item.source_count || 0} sources</small></div>
              <Status value={item.status} />
              <b>›</b>
            </button>
          )) : <Empty compact title="Your library is ready" text="Completed research reports will appear here." />}
        </div>
        <div className="insight-panel">
          <div className="section-title"><div><h2>Workspace pulse</h2><p>Your research performance</p></div><span>Last 30 days</span></div>
          <div className="mini-stats">
            <Metric value={analytics?.total_reports || 0} label="Reports" trend="+12%" />
            <Metric value={analytics?.sources || 0} label="Sources" trend="+8%" />
            <Metric value={`${analytics?.success_rate || 0}%`} label="Success" trend="Stable" />
            <Metric value={formatDuration(analytics?.average_duration || 0)} label="Avg. runtime" trend="-4%" />
          </div>
          <div className="tiny-chart">
            {[28, 42, 36, 61, 48, 73, 58, 80, 64, 87, 76, 93].map((height, index) => <i key={index} style={{ height: `${height}%` }} />)}
          </div>
        </div>
      </section>
    </div>
  )
}

function ExecutionView({ topic, events, agentState, report, error, jobId, onNew }) {
  const [tab, setTab] = useState('report')
  const [logSearch, setLogSearch] = useState('')
  const [logLevel, setLogLevel] = useState('ALL')
  const terminal = report?.status === 'completed'
  const progress = report?.progress || Math.max(2, ...events.map((item) => item.progress || 0))
  const filteredLogs = events.filter((item) => {
    const matchesText = `${item.message} ${item.agent}`.toLowerCase().includes(logSearch.toLowerCase())
    return matchesText && (logLevel === 'ALL' || item.level === logLevel)
  })

  return (
    <div className="page execution-page">
      <div className="execution-header">
        <div>
          <button className="back-link" onClick={onNew}>← New research</button>
          <div className="live-label"><i className={terminal ? 'done' : ''} />{terminal ? 'Research complete' : 'Agents working live'}</div>
          <h1>{topic}</h1>
          <p>Run ID {jobId?.slice(0, 8)} · {report?.model ? shortModel(report.model) : 'Multi-agent pipeline'}</p>
        </div>
        <div className="overall-progress">
          <div><span>Pipeline progress</span><strong>{progress}%</strong></div>
          <div className="meter large"><i style={{ width: `${progress}%` }} /></div>
          <small>{terminal ? `Completed in ${formatDuration(report.duration_seconds)}` : estimateRemaining(progress)}</small>
        </div>
      </div>

      {error && <div className="error-banner"><span>!</span><div><strong>Pipeline interrupted</strong><p>{error}</p></div></div>}

      <div className="execution-grid">
        <section className="agent-panel panel">
          <div className="panel-title"><div><h2>Agent execution</h2><p>Context flows sequentially through the crew</p></div><span className="live-chip">{terminal ? 'Complete' : 'Live'}</span></div>
          <div className="agent-list">
            {AGENT_DEFS.map(([key, name, description, initial], index) => {
              const state = agentState[key] || { status: report ? 'completed' : 'waiting', progress: report ? 100 : 0 }
              return (
                <div className={`agent-row ${state.status}`} key={key}>
                  <div className="agent-rail"><span className="agent-avatar">{state.status === 'completed' ? '✓' : initial}</span>{index < AGENT_DEFS.length - 1 && <i />}</div>
                  <div className="agent-content">
                    <div><strong>{name}</strong><Status value={state.status} /></div>
                    <p>{state.status === 'running' ? activeMessage(key) : description}</p>
                    {state.status === 'running' && <div className="indeterminate"><i /></div>}
                    {state.status === 'completed' && <small>Output checkpoint saved</small>}
                  </div>
                </div>
              )
            })}
          </div>
        </section>

        <section className="logs-panel panel">
          <div className="panel-title"><div><h2>Live activity</h2><p>Execution timeline and recovery logs</p></div><button onClick={() => navigator.clipboard?.writeText(filteredLogs.map((e) => `${e.timestamp} ${e.level} ${e.message}`).join('\n'))}>Copy</button></div>
          <div className="log-tools">
            <label>⌕<input value={logSearch} onChange={(event) => setLogSearch(event.target.value)} placeholder="Filter logs…" /></label>
            <select value={logLevel} onChange={(event) => setLogLevel(event.target.value)}>
              <option>ALL</option><option>INFO</option><option>WARNING</option><option>ERROR</option>
            </select>
            {jobId && <a href={`${API}/reports/${jobId}/logs`}>↓</a>}
          </div>
          <div className="terminal">
            {filteredLogs.length ? filteredLogs.map((event) => (
              <div className={`log-line ${event.level?.toLowerCase()}`} key={event.id || event.sequence}>
                <time>{formatTime(event.timestamp)}</time>
                <span>{event.level || 'INFO'}</span>
                <p>{event.message}</p>
                {event.duration_seconds > 0 && <em>{event.duration_seconds.toFixed(1)}s</em>}
              </div>
            )) : <div className="terminal-empty"><span className="blink">▋</span> Connecting to agent runtime…</div>}
          </div>
        </section>
      </div>

      <section className="report-panel panel">
        <div className="report-toolbar">
          <div className="tabs">
            {['report', 'sources', 'citations', 'timeline', 'graph'].map((item) => (
              <button className={tab === item ? 'active' : ''} onClick={() => setTab(item)} key={item}>{item}</button>
            ))}
          </div>
          {terminal && <div className="exports">
            <span>Export</span>
            {['pdf', 'docx', 'html', 'md', 'json', 'zip'].map((format) => <a key={format} href={`${API}/reports/${report.id}/export/${format}`}>{format.toUpperCase()}</a>)}
          </div>}
        </div>
        {!report ? (
          <div className="report-loading">
            <div className="document-skeleton"><i /><i /><i /><i /><i /><i /></div>
            <div><strong>Your report is taking shape</strong><p>Completed agent outputs appear above instantly. The compiled report will land here when the evidence has passed through the full crew.</p></div>
          </div>
        ) : (
          <>
            {tab === 'report' && <article className="markdown"><div className="report-cover"><span>ResearchOS Intelligence Brief</span><h1>{report.topic}</h1><p>{report.source_count} ranked sources · {formatDuration(report.duration_seconds)} execution · {report.completion_tokens?.toLocaleString()} output tokens</p></div><MarkdownView text={report.result} /></article>}
            {tab === 'sources' && <SourceTable sources={report.sources || []} />}
            {tab === 'citations' && <Citations report={report} />}
            {tab === 'timeline' && <Timeline events={report.events || events} />}
            {tab === 'graph' && <GraphView graph={report.graph} />}
          </>
        )}
      </section>
    </div>
  )
}

function Library({ reports, onOpen, onRefresh }) {
  const [query, setQuery] = useState('')
  const visible = reports.filter((item) => item.topic.toLowerCase().includes(query.toLowerCase()))
  return (
    <div className="page standard-page">
      <PageHeading eyebrow="Research library" title="Every question becomes an asset." text="Search, revisit, save, and export the work your agent crew has completed." />
      <div className="library-tools"><label>⌕<input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search reports and topics…" /></label><button onClick={onRefresh}>↻ Refresh</button></div>
      <div className="report-grid">
        {visible.map((report) => (
          <article className="report-card" key={report.id} onClick={() => onOpen(report.id)}>
            <div><span className="doc-icon completed">▤</span><Status value={report.status} /></div>
            <h3>{report.topic}</h3>
            <p>Built with {shortModel(report.model)} across {report.source_count || 0} ranked sources.</p>
            <footer><span>{relativeTime(report.created_at)}</span><strong>{formatDuration(report.duration_seconds)} →</strong></footer>
          </article>
        ))}
      </div>
      {!visible.length && <Empty title="No reports found" text="Try a broader search, or begin a new research run." />}
    </div>
  )
}

function Knowledge() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const search = async (event) => {
    event.preventDefault(); setLoading(true)
    try { setResults((await api('/knowledge/search', { method: 'POST', body: JSON.stringify({ query, limit: 8 }) })).items) } finally { setLoading(false) }
  }
  return (
    <div className="page standard-page">
      <PageHeading eyebrow="Persistent memory" title="Ask what your workspace already knows." text="Semantic retrieval searches every completed report, then reranks the most relevant evidence." />
      <form className="knowledge-search" onSubmit={search}><span>◇</span><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search concepts across your research memory…" required /><button>{loading ? 'Searching…' : 'Search memory'}</button></form>
      <div className="knowledge-results">
        {results.map((item, index) => <article key={`${item.report_id}-${index}`}><div><span>{Math.round(item.score * 100)}% match</span><small>{item.topic}</small></div><p>{item.content}</p></article>)}
      </div>
      {!results.length && <div className="memory-visual"><div className="memory-core">◇</div>{['Reports', 'Evidence', 'Concepts', 'Notes'].map((x, i) => <span className={`memory-node n${i}`} key={x}>{x}</span>)}<h3>Your private research graph</h3><p>Each completed report is chunked, embedded, and made retrievable automatically.</p></div>}
    </div>
  )
}

function Analytics({ data, reports }) {
  const points = data?.recent_runs || []
  const maxDuration = Math.max(1, ...points.map((item) => item.duration || 0))
  return (
    <div className="page standard-page">
      <PageHeading eyebrow="Analytics" title="See how your intelligence system performs." text="Runtime, reliability, token consumption, and evidence volume—without the black box." />
      <div className="kpi-grid">
        <Kpi icon="▤" label="Total reports" value={data?.total_reports || 0} note={`${data?.completed || 0} completed`} />
        <Kpi icon="◷" label="Avg. execution" value={formatDuration(data?.average_duration || 0)} note="Across all agents" />
        <Kpi icon="◎" label="Success rate" value={`${data?.success_rate || 0}%`} note={`${data?.failed || 0} failed runs`} />
        <Kpi icon="⌁" label="Sources ranked" value={data?.sources || 0} note="Credibility scored" />
      </div>
      <div className="analytics-grid">
        <section className="panel chart-card"><div className="panel-title"><div><h2>Agent pipeline runtime</h2><p>Recent research executions</p></div><span>Seconds</span></div>
          <div className="bar-chart">{points.length ? points.map((item) => <div key={item.id}><i style={{ height: `${Math.max(6, item.duration / maxDuration * 100)}%` }} title={`${item.duration}s`} /><span>{new Date(item.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span></div>) : <Empty compact title="No runtime data" text="Complete a report to populate this chart." />}</div>
        </section>
        <section className="panel cost-card"><div className="panel-title"><div><h2>Usage overview</h2><p>Model tokens and estimated spend</p></div></div>
          <div className="token-ring" style={{ '--value': `${Math.min(100, ((data?.completion_tokens || 0) / 100000) * 100)}deg` }}><div><strong>{compactNumber((data?.prompt_tokens || 0) + (data?.completion_tokens || 0))}</strong><span>Total tokens</span></div></div>
          <div className="usage-legend"><span><i className="green" />Prompt <b>{compactNumber(data?.prompt_tokens || 0)}</b></span><span><i className="lime" />Completion <b>{compactNumber(data?.completion_tokens || 0)}</b></span><span><i className="gray" />Est. cost <b>${(data?.estimated_cost || 0).toFixed(2)}</b></span></div>
        </section>
      </div>
      <section className="panel run-table"><div className="panel-title"><div><h2>Execution history</h2><p>Operational detail for every run</p></div></div><table><thead><tr><th>Topic</th><th>Status</th><th>Sources</th><th>Runtime</th><th>Started</th></tr></thead><tbody>{reports.slice(0, 10).map((item) => <tr key={item.id}><td>{item.topic}</td><td><Status value={item.status} /></td><td>{item.source_count}</td><td>{formatDuration(item.duration_seconds)}</td><td>{relativeTime(item.created_at)}</td></tr>)}</tbody></table></section>
    </div>
  )
}

function Playground() {
  const [agent, setAgent] = useState('teacher')
  const [topic, setTopic] = useState('')
  const [context, setContext] = useState('')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const run = async (event) => {
    event.preventDefault(); setLoading(true); setResult('')
    try { setResult((await api('/playground', { method: 'POST', body: JSON.stringify({ agent, topic, context }) })).result) } catch (e) { setResult(`Error: ${e.message}`) } finally { setLoading(false) }
  }
  return (
    <div className="page standard-page">
      <PageHeading eyebrow="Agent playground" title="Put one specialist under the microscope." text="Run agents independently, supply custom context, and inspect their raw output before changing the production prompt." />
      <div className="playground-grid">
        <form className="panel playground-form" onSubmit={run}>
          <label>Agent<select value={agent} onChange={(e) => setAgent(e.target.value)}>{AGENT_DEFS.slice(0, 5).map(([id, name]) => <option value={id} key={id}>{name}</option>)}</select></label>
          <label>Research topic<input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="What should this agent work on?" required /></label>
          <label>Custom context<textarea value={context} onChange={(e) => setContext(e.target.value)} rows="10" placeholder="Paste source material, a previous agent output, or debug instructions…" /></label>
          <button className="run-button">{loading ? 'Agent is thinking…' : 'Run agent →'}</button>
        </form>
        <section className="panel playground-output"><div className="panel-title"><div><h2>Raw output</h2><p>Unmodified model response</p></div><span className="live-chip">{loading ? 'Running' : 'Ready'}</span></div>{result ? <MarkdownView text={result} /> : <Empty title="Waiting for an agent" text="Configure a run on the left. The isolated response will appear here." />}</section>
      </div>
    </div>
  )
}

function Settings() {
  const [config, setConfig] = useState(null)
  const [saved, setSaved] = useState(false)
  useEffect(() => { api('/config').then(setConfig).catch(console.error) }, [])
  const update = (key, value) => setConfig((current) => ({ ...current, [key]: value }))
  const submit = async (event) => { event.preventDefault(); setConfig(await api('/config', { method: 'PUT', body: JSON.stringify(config) })); setSaved(true); setTimeout(() => setSaved(false), 2000) }
  if (!config) return <div className="page standard-page"><div className="loading-line" /></div>
  return (
    <div className="page standard-page">
      <PageHeading eyebrow="Platform settings" title="Tune the research engine." text="Model behavior, search depth, retrieval, reliability, and provider configuration live in one place." />
      <form className="settings-layout" onSubmit={submit}>
        <section className="panel settings-section"><div className="settings-title"><span>01</span><div><h2>Model & generation</h2><p>Choose how agents reason and respond.</p></div></div>
          <div className="field-grid">
            <Field label="Provider"><select value={config.provider} onChange={(e) => update('provider', e.target.value)}><option>openrouter</option><option>openai</option><option>gemini</option><option>anthropic</option><option>groq</option><option>ollama</option></select></Field>
            <Field label="Model"><input value={config.model} onChange={(e) => update('model', e.target.value)} /></Field>
            <Field label={`Temperature · ${config.temperature}`}><input type="range" min="0" max="2" step=".1" value={config.temperature} onChange={(e) => update('temperature', Number(e.target.value))} /></Field>
            <Field label="Max tokens"><input type="number" value={config.max_tokens} onChange={(e) => update('max_tokens', Number(e.target.value))} /></Field>
          </div>
        </section>
        <section className="panel settings-section"><div className="settings-title"><span>02</span><div><h2>Search & memory</h2><p>Control evidence collection and retrieval.</p></div></div>
          <div className="field-grid">
            <Field label="Search depth"><select value={config.search_depth} onChange={(e) => update('search_depth', e.target.value)}><option>basic</option><option>advanced</option></select></Field>
            <Field label="Number of sources"><input type="number" value={config.number_of_sources} onChange={(e) => update('number_of_sources', Number(e.target.value))} /></Field>
            <Field label="Vector database"><select value={config.vector_db} onChange={(e) => update('vector_db', e.target.value)}><option>local</option><option>chromadb</option><option>faiss</option><option>qdrant</option><option>pinecone</option></select></Field>
            <Field label="Chunk size"><input type="number" value={config.chunk_size} onChange={(e) => update('chunk_size', Number(e.target.value))} /></Field>
          </div>
        </section>
        <section className="panel settings-section"><div className="settings-title"><span>03</span><div><h2>Reliability</h2><p>Recovery policy for slow or failing providers.</p></div></div>
          <div className="field-grid"><Field label="Retry count"><input type="number" value={config.retry_count} onChange={(e) => update('retry_count', Number(e.target.value))} /></Field><Field label="Timeout (seconds)"><input type="number" value={config.timeout} onChange={(e) => update('timeout', Number(e.target.value))} /></Field></div>
        </section>
        <section className="panel integration-section"><div className="settings-title"><span>04</span><div><h2>API connections</h2><p>Secrets remain server-side in environment variables.</p></div></div>
          <div className="integration-grid">{[['OpenRouter', 'Connected', 'OR'], ['Serper Search', 'Connected', 'S'], ['Google OAuth', 'Environment', 'G'], ['GitHub OAuth', 'Environment', 'GH']].map(([name, state, icon]) => <div key={name}><span>{icon}</span><div><strong>{name}</strong><small>{state}</small></div><i /></div>)}</div>
        </section>
        <div className="settings-save"><span>{saved && '✓ Configuration saved'}</span><button className="run-button">Save changes</button></div>
      </form>
    </div>
  )
}

function MarkdownView({ text = '' }) {
  let inCode = false
  return <div className="markdown-body">{text.split('\n').map((line, index) => {
    if (line.startsWith('```')) { inCode = !inCode; return <span key={index} /> }
    if (inCode) return <code className="code-line" key={index}>{line}</code>
    if (line.startsWith('### ')) return <h3 key={index}>{line.slice(4)}</h3>
    if (line.startsWith('## ')) return <h2 key={index}>{line.slice(3)}</h2>
    if (line.startsWith('# ')) return <h1 key={index}>{line.slice(2)}</h1>
    if (/^[-*]\s/.test(line)) return <div className="bullet" key={index}><span>•</span><p>{linkify(line.slice(2))}</p></div>
    if (/^\d+\.\s/.test(line)) return <div className="bullet numbered" key={index}><span>{line.match(/^\d+/)[0]}</span><p>{linkify(line.replace(/^\d+\.\s/, ''))}</p></div>
    if (line.startsWith('> ')) return <blockquote key={index}>{line.slice(2)}</blockquote>
    if (!line.trim()) return <br key={index} />
    return <p key={index}>{linkify(line)}</p>
  })}</div>
}

function linkify(text) {
  const parts = text.split(/(https?:\/\/[^\s)]+)/g)
  return parts.map((part, index) => part.startsWith('http') ? <a href={part} target="_blank" rel="noreferrer" key={index}>{part}</a> : <span key={index}>{part.replace(/\*\*/g, '')}</span>)
}

function SourceTable({ sources }) {
  return <div className="source-table"><div className="source-summary"><div><strong>{sources.length}</strong><span>Unique sources</span></div><div><strong>{sources.length ? Math.round(sources.reduce((a, b) => a + b.credibility_score, 0) / sources.length) : 0}</strong><span>Avg. credibility</span></div><div><strong>{sources.filter((s) => s.label.includes('Trusted')).length}</strong><span>Trusted sources</span></div></div><table><thead><tr><th>Source</th><th>Credibility</th><th>Authority</th><th>Recency</th><th>Confidence</th></tr></thead><tbody>{sources.map((source) => <tr key={source.url}><td><a href={source.url} target="_blank" rel="noreferrer"><strong>{source.title || source.domain}</strong><small>{source.domain} ↗</small></a></td><td><Score value={source.credibility_score} /></td><td>{source.authority_score}</td><td>{source.recency_score}</td><td><span className={`trust ${source.label.toLowerCase().replace(' ', '-')}`}>{source.label}</span></td></tr>)}</tbody></table>{!sources.length && <Empty title="No URLs detected" text="The model output did not contain source URLs to score." />}</div>
}

function Citations({ report }) {
  const [style, setStyle] = useState('ieee')
  const entries = report.citations?.[style] || []
  return <div className="citations-view"><div className="citation-head"><div><h2>Citation manager</h2><p>Deduplicated references, ready for publication.</p></div><div>{['ieee', 'apa', 'mla', 'bibtex'].map((item) => <button className={style === item ? 'active' : ''} onClick={() => setStyle(item)} key={item}>{item.toUpperCase()}</button>)}</div></div>{entries.map((entry, index) => <div className="citation-item" key={index}><span>{index + 1}</span><code>{entry}</code><button onClick={() => navigator.clipboard?.writeText(entry)}>Copy</button></div>)}</div>
}

function Timeline({ events }) {
  return <div className="timeline">{events.map((event, index) => <div className={event.status} key={event.id || index}><span>{event.status === 'completed' ? '✓' : event.level === 'ERROR' ? '!' : '·'}</span><i /><time>{formatTime(event.timestamp)}</time><section><strong>{event.message}</strong><p>{event.agent ? `${event.agent} · ` : ''}{event.duration_seconds ? `${event.duration_seconds.toFixed(1)} seconds` : event.status}</p></section>{event.retry_count > 0 && <em>Retry {event.retry_count}</em>}</div>)}</div>
}

function GraphView({ graph }) {
  const nodes = graph?.nodes || []
  const sources = nodes.filter((node) => node.type === 'source')
  return <div className="graph-view"><div className="graph-canvas"><div className="graph-topic">{nodes[0]?.label || 'Topic'}</div><div className="graph-agents">{nodes.filter((node) => node.type === 'agent').map((node, i) => <div key={node.id}><span>{node.label[0]}</span><small>{node.label}</small>{i < 4 && <i>→</i>}</div>)}</div><div className="graph-sources">{sources.slice(0, 8).map((node, i) => <a href={node.url} target="_blank" rel="noreferrer" className={`g${i}`} key={node.id}>{node.label}<small>{node.score}</small></a>)}</div></div><p>Interactive research graph · topic → agents → ranked evidence</p></div>
}

function PageHeading({ eyebrow, title, text }) {
  return <div className="page-heading"><span>{eyebrow}</span><h1>{title}</h1><p>{text}</p></div>
}
function Field({ label, children }) { return <label className="field"><span>{label}</span>{children}</label> }
function Status({ value = 'waiting' }) { return <span className={`status ${value}`}><i />{value}</span> }
function Score({ value }) { return <div className="score"><strong>{value}</strong><div><i style={{ width: `${value}%` }} /></div></div> }
function Metric({ value, label, trend }) { return <div><strong>{value}</strong><span>{label}</span><small>{trend}</small></div> }
function Kpi({ icon, label, value, note }) { return <div className="kpi"><span>{icon}</span><div><small>{label}</small><strong>{value}</strong><p>{note}</p></div></div> }
function Empty({ title, text, compact = false }) { return <div className={`empty ${compact ? 'compact' : ''}`}><span>◇</span><div><strong>{title}</strong><p>{text}</p></div></div> }

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json', ...options.headers }, ...options })
  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('json') ? await response.json() : await response.text()
  if (!response.ok) throw new Error(payload?.detail || payload || `Request failed (${response.status})`)
  return payload
}
function shortModel(value = '') { return value.split('/').slice(-1)[0].replaceAll('-', ' ').replace(/\b\w/g, (c) => c.toUpperCase()) }
function relativeTime(value) { const seconds = Math.max(1, (Date.now() - new Date(value).getTime()) / 1000); if (seconds < 60) return 'Just now'; if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`; if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`; return `${Math.floor(seconds / 86400)}d ago` }
function formatDuration(seconds = 0) { if (seconds < 60) return `${Math.round(seconds)}s`; return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s` }
function formatTime(value) { return value ? new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '--:--:--' }
function estimateRemaining(progress) { const remaining = Math.max(10, Math.round((100 - progress) * 2.4)); return `About ${formatDuration(remaining)} remaining` }
function compactNumber(value) { return Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(value) }
function activeMessage(key) { return { researcher: 'Searching, reading, and ranking evidence…', teacher: 'Building a rigorous explanation…', simplifier: 'Removing jargon and sharpening the core idea…', student: 'Synthesizing structured revision notes…', examiner: 'Designing questions that test understanding…', reporter: 'Compiling the final intelligence brief…' }[key] }
function pageTitle(page) { return { home: 'Overview', research: 'Research', library: 'Library', knowledge: 'Knowledge base', analytics: 'Analytics', playground: 'Agent playground', settings: 'Settings' }[page] }

export default App
