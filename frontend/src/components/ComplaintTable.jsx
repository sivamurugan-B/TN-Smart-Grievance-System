import { useState } from 'react'
import { deleteComplaint } from '../services/api'

const PAGE_SIZE = 10

const TrashIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
       strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
  </svg>
)

function Badge({ type, value }) {
  const cls = type === 'severity'
    ? value === 'High'   ? 'badge badge-high'
    : value === 'Medium' ? 'badge badge-medium'
    :                      'badge badge-low'
    : value === 'Complaint'  ? 'badge badge-complaint'
    : value === 'Request'    ? 'badge badge-request'
    :                          'badge badge-suggestion'
  return <span className={cls}>{value}</span>
}

function fmt(ts) {
  if (!ts) return '—'
  try {
    return new Date(ts).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return ts }
}

export default function ComplaintTable({ complaints, total, onRefresh }) {
  const [page,    setPage]    = useState(1)
  const [deleting, setDeleting] = useState(null)

  const totalPages = Math.ceil(total / PAGE_SIZE) || 1
  const start      = (page - 1) * PAGE_SIZE
  const slice      = complaints.slice(start, start + PAGE_SIZE)

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this complaint?')) return
    setDeleting(id)
    try {
      await deleteComplaint(id)
      onRefresh()
    } catch (e) {
      alert('Delete failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setDeleting(null)
    }
  }

  if (!complaints.length) {
    return (
      <div className="empty">
        <div className="empty-icon">📋</div>
        <h3>No complaints yet</h3>
        <p>Submit a complaint from the form page to see it here.</p>
      </div>
    )
  }

  return (
    <>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Complaint Text</th>
              <th>Type</th>
              <th>Category</th>
              <th>Severity</th>
              <th>Timestamp</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {slice.map((c, idx) => (
              <tr key={c.id}>
                <td style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--text3)' }}>
                  {start + idx + 1}
                </td>
                <td>
                  <span className="text-cell" title={c.text}>{c.text}</span>
                </td>
                <td><Badge type="type"     value={c.type} /></td>
                <td style={{ color: 'var(--accent)', fontSize: '12px' }}>{c.category}</td>
                <td><Badge type="severity" value={c.severity} /></td>
                <td className="ts-cell">{fmt(c.created_at)}</td>
                <td>
                  <button
                    className="btn btn-danger"
                    style={{ padding: '5px 10px', fontSize: '12px' }}
                    onClick={() => handleDelete(c.id)}
                    disabled={deleting === c.id}
                    title="Delete"
                  >
                    {deleting === c.id ? '…' : <TrashIcon />}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="page-btn"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            ← Prev
          </button>
          <span className="page-info">Page {page} of {totalPages}</span>
          <button
            className="page-btn"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            Next →
          </button>
        </div>
      )}
    </>
  )
}
