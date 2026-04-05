import { useState, useEffect, useCallback } from 'react'
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid,
} from 'recharts'
import { fetchStats, fetchComplaints } from '../services/api'
import ComplaintTable from './ComplaintTable'

// ── Palette ───────────────────────────────────
const SEV_COLORS  = { High: '#ef4444', Medium: '#f59e0b', Low: '#00d4a8' }
const CAT_COLORS  = ['#00d4a8','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#ec4899','#14b8a6']

const RefreshIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
       strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
    <polyline points="23 4 23 10 17 10" />
    <polyline points="1 20 1 14 7 14" />
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
  </svg>
)

// ── Custom tooltip ────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--surface)', border: '1px solid var(--border)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
    }}>
      <p style={{ color: 'var(--text2)', marginBottom: 4 }}>{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color || 'var(--accent)', fontWeight: 600 }}>
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [stats,      setStats]      = useState(null)
  const [complaints, setComplaints] = useState([])
  const [total,      setTotal]      = useState(0)
  const [loading,    setLoading]    = useState(true)
  const [error,      setError]      = useState(null)

  // Filters
  const [filterCat,  setFilterCat]  = useState('')
  const [filterSev,  setFilterSev]  = useState('')
  const [filterType, setFilterType] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [s, c] = await Promise.all([
        fetchStats(),
        fetchComplaints({
          limit:    200,
          category: filterCat  || undefined,
          severity: filterSev  || undefined,
          type:     filterType || undefined,
        }),
      ])
      setStats(s)
      setComplaints(c.complaints)
      setTotal(c.total)
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || String(e)
      setError(`API error: ${msg}`)
    } finally {
      setLoading(false)
    }
  }, [filterCat, filterSev, filterType])

  useEffect(() => { load() }, [load])

  // ── Derived chart data ────────────────────────
  const severityData = stats
    ? Object.entries(stats.by_severity).map(([name, value]) => ({ name, value }))
    : []

  const categoryData = stats
    ? Object.entries(stats.by_category)
        .sort((a, b) => b[1] - a[1])
        .map(([name, value]) => ({ name, value }))
    : []

  return (
    <>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2>Dashboard</h2>
            <p>Real-time grievance analytics and complaint tracking</p>
          </div>
          <button className="btn btn-outline" onClick={load} disabled={loading}>
            <RefreshIcon /> {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="page-content">
        {error && (
          <div className="alert alert-error" style={{ marginBottom: 24 }}>
            {error}
          </div>
        )}

        {/* ── Stat Cards ── */}
        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-label">Total Complaints</div>
            <div className="stat-value">{stats?.total ?? '—'}</div>
            <div className="stat-sub">All time</div>
          </div>
          <div className="stat-card danger">
            <div className="stat-label">High Severity</div>
            <div className="stat-value" style={{ color: '#f87171' }}>
              {stats?.by_severity?.High ?? '—'}
            </div>
            <div className="stat-sub">Needs urgent attention</div>
          </div>
          <div className="stat-card warn">
            <div className="stat-label">Medium Severity</div>
            <div className="stat-value" style={{ color: '#fbbf24' }}>
              {stats?.by_severity?.Medium ?? '—'}
            </div>
            <div className="stat-sub">Moderate priority</div>
          </div>
          <div className="stat-card info">
            <div className="stat-label">Last 7 Days</div>
            <div className="stat-value" style={{ color: '#93c5fd' }}>
              {stats?.recent_7days_count ?? '—'}
            </div>
            <div className="stat-sub">New submissions</div>
          </div>
        </div>

        {/* ── Charts ── */}
        {stats && (
          <div className="charts-grid">
            {/* Pie – Severity */}
            <div className="chart-card">
              <div className="chart-title">Severity Distribution</div>
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {severityData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={SEV_COLORS[entry.name] || '#4a6a8a'}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    formatter={(v) => (
                      <span style={{ color: 'var(--text2)', fontSize: 12 }}>{v}</span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Bar – Category */}
            <div className="chart-card">
              <div className="chart-title">Complaints by Category</div>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={categoryData} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: 'var(--text3)', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: 'var(--text3)', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,212,168,0.06)' }} />
                  <Bar dataKey="value" name="Count" radius={[4, 4, 0, 0]}>
                    {categoryData.map((_, i) => (
                      <Cell key={i} fill={CAT_COLORS[i % CAT_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* ── Complaints Table ── */}
        <div className="card" style={{ marginTop: 4 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div className="section-title" style={{ marginBottom: 0 }}>
              All Complaints
              <span style={{ color: 'var(--accent)', marginLeft: 8, fontFamily: 'var(--mono)' }}>
                ({total})
              </span>
            </div>

            {/* Filters */}
            <div className="filter-bar" style={{ marginBottom: 0 }}>
              <select
                className="filter-select"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="">All Types</option>
                {['Complaint', 'Request', 'Suggestion'].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>

              <select
                className="filter-select"
                value={filterCat}
                onChange={(e) => setFilterCat(e.target.value)}
              >
                <option value="">All Categories</option>
                {['Water', 'Road', 'Electricity', 'Garbage', 'Drainage', 'Health', 'Transport'].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>

              <select
                className="filter-select"
                value={filterSev}
                onChange={(e) => setFilterSev(e.target.value)}
              >
                <option value="">All Severities</option>
                {['High', 'Medium', 'Low'].map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text3)' }}>
              <div className="spinner" style={{ margin: '0 auto 12px' }} />
              Loading complaints…
            </div>
          ) : (
            <ComplaintTable
              complaints={complaints}
              total={total}
              onRefresh={load}
            />
          )}
        </div>
      </div>
    </>
  )
}
