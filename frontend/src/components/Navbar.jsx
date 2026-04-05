import { NavLink, useLocation } from 'react-router-dom'

const ShieldIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
       strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
)

const FormIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
       strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <line x1="10" y1="9"  x2="8" y2="9" />
  </svg>
)

const ChartIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
       strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10" />
    <line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6"  y1="20" x2="6"  y2="14" />
  </svg>
)

const GovIcon = () => (
  <svg viewBox="0 0 24 24" fill="var(--bg)">
    <path d="M12 2L2 7l1 2h18l1-2L12 2zm0 2.18L19.28 8H4.72L12 4.18zM4
      10v8H2v2h20v-2h-2v-8h-2v8h-4v-8h-2v8H8v-8H4z"/>
  </svg>
)

export default function Navbar() {
  const location = useLocation()

  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-mark">
          <div className="logo-icon">
            <GovIcon />
          </div>
          <h1>TN Grievance<br />System</h1>
        </div>
        <p>AI-Powered · v1.0</p>
      </div>

      <nav className="nav">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
        >
          <FormIcon />
          Submit Complaint
        </NavLink>

        <NavLink
          to="/dashboard"
          className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
        >
          <ChartIcon />
          Dashboard
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        Tamil Nadu · Civic Portal<br />
        <span style={{ color: 'var(--accent)' }}>BERT</span> + FastAPI + MongoDB
      </div>
    </aside>
  )
}
