import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Inbox, BarChart3, Zap, Activity, AlertCircle } from 'lucide-react'
import { analyticsApi } from '../lib/api'
import './Layout.css'

function Sidebar() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    analyticsApi.summary()
      .then(r => setStats(r.data))
      .catch(() => {})

    // Refresh every 10s
    const id = setInterval(() => {
      analyticsApi.summary().then(r => setStats(r.data)).catch(() => {})
    }, 10000)
    return () => clearInterval(id)
  }, [])

  const nav = [
    {
      to: '/inbox',
      icon: Inbox,
      label: 'Mission Control',
      badge: stats?.needs_human,
    },
    {
      to: '/analytics',
      icon: BarChart3,
      label: 'Analytics',
    },
  ]

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-mark">
          <Zap size={16} strokeWidth={2.5} />
        </div>
        <div>
          <div className="logo-name">CRM Intel</div>
          <div className="logo-tagline">AI Operations</div>
        </div>
      </div>

      {/* Live agent status */}
      <div className="agent-status">
        <span className="pulse-dot" />
        <span>LangGraph Agent Active</span>
      </div>

      {/* Nav links */}
      <nav className="sidebar-nav">
        {nav.map(({ to, icon: Icon, label, badge }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <Icon size={16} strokeWidth={2} />
            <span className="nav-label">{label}</span>
            {badge > 0 && <span className="nav-badge">{badge}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Mini stats */}
      {stats && (
        <div className="sidebar-metrics">
          <div className="metric">
            <span className="metric-val">{stats.total_emails ?? 0}</span>
            <span className="metric-key">Total</span>
          </div>
          <div className="metric-divider" />
          <div className="metric">
            <span className="metric-val" style={{ color: 'var(--amber)' }}>{stats.escalated ?? 0}</span>
            <span className="metric-key">Escalated</span>
          </div>
          <div className="metric-divider" />
          <div className="metric">
            <span className="metric-val" style={{ color: 'var(--green)' }}>{stats.auto_replied ?? 0}</span>
            <span className="metric-key">Auto-Sent</span>
          </div>
        </div>
      )}

      {/* At-risk contacts alert */}
      {stats?.at_risk_contacts > 0 && (
        <div className="churn-alert">
          <AlertCircle size={12} />
          <span>{stats.at_risk_contacts} contacts at churn risk</span>
        </div>
      )}

      <div className="sidebar-footer">
        <Activity size={11} />
        <span>mistralai/Mistral-7B · MiniLM-L6-v2</span>
      </div>
    </aside>
  )
}

export default function Layout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="page-content">
        <Outlet />
      </main>
    </div>
  )
}
