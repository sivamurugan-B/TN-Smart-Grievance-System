export default function ResultCard({ result }) {
  const severityClass = {
    High:   'badge badge-high',
    Medium: 'badge badge-medium',
    Low:    'badge badge-low',
  }
  const typeClass = {
    Complaint:  'badge badge-complaint',
    Request:    'badge badge-request',
    Suggestion: 'badge badge-suggestion',
  }

  return (
    <div className="result-card">
      <div className="result-header">
        <div className="result-check">
          <svg viewBox="0 0 24 24" fill="var(--bg)" stroke="none">
            <path d="M20 6L9 17l-5-5" stroke="var(--bg)" strokeWidth="3"
                  fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <h3>Grievance Analysed</h3>
      </div>

      <div className="result-grid">
        <div className="result-item">
          <div className="result-item-label">Type</div>
          <div className="result-item-value">
            <span className={typeClass[result.type] || 'badge'}>
              {result.type}
            </span>
          </div>
        </div>
        <div className="result-item">
          <div className="result-item-label">Category</div>
          <div className="result-item-value" style={{ color: 'var(--accent)' }}>
            {result.category}
          </div>
        </div>
        <div className="result-item">
          <div className="result-item-label">Severity</div>
          <div className="result-item-value">
            <span className={severityClass[result.severity] || 'badge'}>
              {result.severity}
            </span>
          </div>
        </div>
      </div>

      <div className="result-msg">
        Your complaint has been registered and will be resolved soon. Our team
        will address it based on the detected severity and category.
      </div>

      {result.method && (
        <div className="method-tag">
          Classified via <span>{result.method}</span>
        </div>
      )}
    </div>
  )
}
