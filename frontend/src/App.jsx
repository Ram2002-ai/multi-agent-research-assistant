import { useState } from 'react'

function App() {
  const [topic, setTopic] = useState('What is Artificial Intelligence?')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setResult('')
    setLoading(true)

    try {
      const response = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic }),
      })

      const text = await response.text()
      const data = text ? JSON.parse(text) : null

      if (!response.ok) {
        throw new Error(data?.detail || data?.message || `Request failed (${response.status})`)
      }

      if (!data || typeof data.result !== 'string') {
        throw new Error('Unexpected API response format')
      }

      setResult(data.result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Multi-Agent Research Assistant</p>
          <h1>AI Research, Teaching, and Notes — in one flow</h1>
          <p>Enter a topic and let the crew generate a detailed report, simplified summary, notes, and test questions.</p>
        </div>
      </header>

      <main className="content">
        <section className="form-card">
          <form onSubmit={handleSubmit}>
            <label htmlFor="topic">Research topic</label>
            <input
              id="topic"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="Enter a topic to research"
              required
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Generating report…' : 'Generate report'}
            </button>
          </form>

          {error && <p className="error">{error}</p>}
          {result && (
            <div className="result">
              <h2>Research Report</h2>
              <pre>{result}</pre>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
