import { useState, useRef } from 'react'
import { submitComplaint } from '../services/api'
import ResultCard from './ResultCard'

const MAX_CHARS = 1000

const EXAMPLES = [
  'Sewage is overflowing near our street in Adyar causing flooding and health hazards',
  'Street light not working on Anna Salai for the past 3 days causing safety issues',
  'Please fix the large pothole on OMR near Sholinganallur which is causing accidents',
  'Garbage collection has been irregular in T.Nagar for a week and the area smells terrible',
  'Water supply pipe burst in Velachery near the market causing water wastage',
  'Suggest installing more bus shelters on the outer ring road to help daily commuters',
]

const SendIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
       strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
)
const UploadIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
       strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16 16 12 12 8 16" />
    <line x1="12" y1="12" x2="12" y2="21" />
    <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
  </svg>
)
const AlertIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
       strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9"  x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
)

export default function ComplaintForm() {
  const [text,     setText]     = useState('')
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)
  const [error,    setError]    = useState(null)
  const [fileName, setFileName] = useState(null)
  const fileRef = useRef(null)

  const handleSubmit = async () => {
    if (text.trim().length < 10) return
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await submitComplaint(text.trim())
      setResult(data)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Could not connect to the backend. Make sure the FastAPI server is running on port 8000.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) setFileName(file.name)
  }

  const handleReset = () => {
    setText('')
    setResult(null)
    setError(null)
    setFileName(null)
  }

  return (
    <>
      <div className="page-header">
        <h2>Submit a Complaint</h2>
        <p>AI will instantly classify your grievance and route it to the right department</p>
      </div>

      <div className="page-content">
        {error && (
          <div className="alert alert-error">
            <AlertIcon />
            {error}
          </div>
        )}

        <div className="two-col">
          {/* ── Left: Form ── */}
          <div>
            <div className="card">
              <div className="form-group">
                <label className="form-label">Describe your grievance</label>
                <textarea
                  className="form-textarea"
                  value={text}
                  onChange={(e) => setText(e.target.value.slice(0, MAX_CHARS))}
                  placeholder="e.g. The drainage near our street has been overflowing for 3 days, causing water-logging and health hazards for residents…"
                  rows={6}
                />
                <div className="char-count">
                  {text.length} / {MAX_CHARS}
                </div>
              </div>

              {/* Image Upload (UI only) */}
              <div className="form-group">
                <label className="form-label">Attach Image (optional)</label>
                <div
                  className={`upload-area${fileName ? ' has-file' : ''}`}
                  onClick={() => fileRef.current?.click()}
                >
                  <UploadIcon />
                  {fileName
                    ? fileName
                    : 'Click to attach a photo of the issue'}
                </div>
                <input
                  ref={fileRef}
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={handleFileChange}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  className="btn btn-primary"
                  onClick={handleSubmit}
                  disabled={loading || text.trim().length < 10}
                  style={{ flex: 1, justifyContent: 'center' }}
                >
                  {loading
                    ? <><div className="spinner" /> Analysing…</>
                    : <><SendIcon /> Submit Grievance</>}
                </button>

                {result && (
                  <button className="btn btn-outline" onClick={handleReset}>
                    New
                  </button>
                )}
              </div>

              {loading && (
                <div className="loading-bar">
                  <div className="loading-bar-fill" />
                </div>
              )}
            </div>
          </div>

          {/* ── Right: Guide + Examples ── */}
          <div>
            <div className="card">
              <div className="section-title">How it works</div>
              <div style={{ fontSize: '14px', color: 'var(--text2)', lineHeight: 1.8 }}>
                <p style={{ marginBottom: '10px' }}>
                  <span style={{ color: 'var(--accent)', fontFamily: 'var(--mono)' }}>1.</span>
                  &nbsp;Type your complaint in detail
                </p>
                <p style={{ marginBottom: '10px' }}>
                  <span style={{ color: 'var(--accent)', fontFamily: 'var(--mono)' }}>2.</span>
                  &nbsp;Our BERT model detects <strong>type</strong>, <strong>category</strong>, and <strong>severity</strong>
                </p>
                <p style={{ marginBottom: '10px' }}>
                  <span style={{ color: 'var(--accent)', fontFamily: 'var(--mono)' }}>3.</span>
                  &nbsp;Complaint is stored and tracked in the dashboard
                </p>
                <p>
                  <span style={{ color: 'var(--accent)', fontFamily: 'var(--mono)' }}>4.</span>
                  &nbsp;Resolved based on priority and department
                </p>
              </div>

              <hr className="divider" />

              <div className="section-title">Try an example</div>
              <div className="examples">
                {EXAMPLES.map((ex, i) => (
                  <span
                    key={i}
                    className="example-chip"
                    onClick={() => { setText(ex); setResult(null); setError(null) }}
                  >
                    {ex.length > 50 ? ex.slice(0, 50) + '…' : ex}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── Result Card ── */}
        {result && <ResultCard result={result} />}
      </div>
    </>
  )
}
