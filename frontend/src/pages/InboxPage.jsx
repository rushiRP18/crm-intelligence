import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, RefreshCw, Mail, AlertTriangle, ShieldAlert,
  Scale, ClipboardCheck, Inbox, Zap, User, Clock,
} from 'lucide-react'
import { emailsApi } from '../lib/api'
import { formatDistanceToNow } from 'date-fns'
import './InboxPage.css'

/* ── Constants ────────────────────────────────────────── */
const TABS = [
  { key: 'all',          label: 'All Emails' },
  { key: 'needs_human',  label: 'Needs Human' },
  { key: 'escalated',   label: 'Escalated' },
  { key: 'pending_review', label: 'Pending Draft' },
  { key: 'spam',        label: 'Spam' },
  { key: 'internal',    label: 'Internal' },
]

const SENTIMENT = {
  Positive: { badge: 'badge-green',  label: '+ Positive' },
  Negative: { badge: 'badge-red',    label: '− Negative' },
  Mixed:    { badge: 'badge-orange', label: '~ Mixed' },
  Neutral:  { badge: 'badge-gray',   label: '• Neutral' },
}

const URGENCY = {
  Critical: { badge: 'badge-crimson', icon: '🔴' },
  High:     { badge: 'badge-amber',   icon: '🟠' },
  Medium:   { badge: 'badge-blue',    icon: '🔵' },
  Low:      { badge: 'badge-gray',    icon: '⚪' },
}

const CATEGORY_ICON = {
  Complaint:         '😤',
  'Bug Report':      '🐛',
  Legal:             '⚖️',
  Security:          '🔒',
  Compliance:        '📋',
  Billing:           '💳',
  Spam:              '🚫',
  Internal:          '🏢',
  Inquiry:           '❓',
  'Feature Request': '✨',
  Other:             '📧',
}

/* ── Sentiment Score Bar ──────────────────────────────── */
function ScoreBar({ score }) {
  if (score == null) return null
  const pct  = ((score + 1) / 2 * 100).toFixed(0)
  const color = score > 0.3 ? 'var(--green)' : score < -0.3 ? 'var(--red)' : 'var(--amber)'
  return (
    <div className="score-bar">
      <div className="score-fill" style={{ width: `${pct}%`, background: color }} />
    </div>
  )
}

/* ── Single email row ─────────────────────────────────── */
function EmailRow({ email, onClick }) {
  const sent = SENTIMENT[email.sentiment] || SENTIMENT.Neutral
  const urg  = URGENCY[email.urgency]
  const timeAgo = email.timestamp
    ? formatDistanceToNow(new Date(email.timestamp), { addSuffix: true })
    : '—'
  const isNew = ['pending', 'escalated'].includes(email.status)

  return (
    <tr
      className={`email-row ${isNew ? 'unread' : ''} fade-in`}
      onClick={() => onClick(email)}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && onClick(email)}
    >
      {/* Sender */}
      <td className="col-sender">
        <div className="avatar">{(email.sender?.[0] ?? '?').toUpperCase()}</div>
        <div className="sender-info">
          <span className="sender-name">{email.sender?.split('@')[0] ?? 'Unknown'}</span>
          <span className="sender-domain text-xs text-muted">
            @{email.sender?.split('@')[1] ?? ''}
          </span>
        </div>
      </td>

      {/* Subject */}
      <td className="col-subject">
        <span className="subject-text">{email.subject ?? '(no subject)'}</span>
        {email.requires_human && (
          <User size={11} className="human-icon" title="Needs human review" />
        )}
      </td>

      {/* Category */}
      <td className="col-category">
        <span className="cat-icon">{CATEGORY_ICON[email.category] ?? '📧'}</span>
        <span className="text-sm text-muted">{email.category ?? 'Pending'}</span>
      </td>

      {/* Sentiment */}
      <td className="col-sentiment">
        {email.sentiment && (
          <div className="sentiment-col">
            <span className={`badge ${sent.badge}`}>{email.sentiment}</span>
            <ScoreBar score={email.sentiment_score} />
          </div>
        )}
      </td>

      {/* Urgency */}
      <td className="col-urgency">
        {urg && (
          <span className={`badge ${urg.badge}`}>
            {urg.icon} {email.urgency}
          </span>
        )}
      </td>

      {/* Status */}
      <td className="col-status">
        <span className={`status-pill status-${email.status}`}>
          {(email.status ?? 'unknown').replace('_', ' ')}
        </span>
      </td>

      {/* Confidence */}
      <td className="col-conf">
        {email.confidence != null && (
          <span className={`conf-val ${email.confidence < 0.7 ? 'low' : ''}`}>
            {(email.confidence * 100).toFixed(0)}%
          </span>
        )}
      </td>

      {/* Time */}
      <td className="col-time">
        <span className="time-val">{timeAgo}</span>
      </td>
    </tr>
  )
}

/* ── Main Inbox Page ──────────────────────────────────── */
export default function InboxPage() {
  const navigate = useNavigate()
  const [emails, setEmails]     = useState([])
  const [total, setTotal]       = useState(0)
  const [loading, setLoading]   = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [activeTab, setActiveTab]   = useState('all')
  const [search, setSearch]         = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')

  // Debounce search input
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400)
    return () => clearTimeout(t)
  }, [search])

  const fetchEmails = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true)
    try {
      const params = { limit: 150 }
      if (activeTab === 'needs_human') params.requires_human = true
      else if (activeTab !== 'all') params.status = activeTab
      if (debouncedSearch) params.search = debouncedSearch

      const { data } = await emailsApi.list(params)
      setEmails(data.emails ?? [])
      setTotal(data.total ?? 0)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [activeTab, debouncedSearch])

  useEffect(() => { fetchEmails() }, [fetchEmails])

  // Auto-refresh every 6 s
  useEffect(() => {
    const id = setInterval(() => fetchEmails(true), 6000)
    return () => clearInterval(id)
  }, [fetchEmails])

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchEmails()
    setRefreshing(false)
  }

  const handleRowClick = (email) => {
    // We navigate by email ID (thread page will work off that too)
    navigate(`/thread/${encodeURIComponent(email.id)}`)
  }

  // Count tabs from local data where possible
  const counts = {
    all:          total,
    needs_human:  emails.filter(e => e.requires_human).length,
    escalated:    emails.filter(e => e.status === 'escalated').length,
    pending_review: emails.filter(e => e.status === 'pending_review').length,
    spam:         emails.filter(e => e.status === 'spam').length,
    internal:     emails.filter(e => e.status === 'internal').length,
  }

  return (
    <div className="inbox-page">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Inbox size={22} />
            Mission Control
          </h1>
          <p className="text-muted text-sm" style={{ marginTop: 2 }}>
            {total.toLocaleString()} emails · autonomous AI triage active
          </p>
        </div>
        <button
          className={`btn btn-ghost btn-sm ${refreshing ? 'loading' : ''}`}
          onClick={handleRefresh}
        >
          <RefreshCw size={13} className={refreshing ? 'spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="inbox-tabs">
        {TABS.map(tab => (
          <button
            key={tab.key}
            className={`inbox-tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
            {(counts[tab.key] ?? 0) > 0 && (
              <span className="tab-count">{counts[tab.key]}</span>
            )}
          </button>
        ))}
      </div>

      {/* Search bar */}
      <div className="search-bar">
        <Search size={14} className="search-icon" />
        <input
          className="input search-input"
          placeholder="Search by subject, sender, body…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Table container */}
      <div className="table-wrap">
        {loading ? (
          <div className="center-state">
            <div className="spinner" style={{ width: 28, height: 28 }} />
            <p className="text-muted text-sm">Loading emails…</p>
          </div>
        ) : emails.length === 0 ? (
          <div className="center-state">
            <Mail size={44} style={{ color: 'var(--text-3)', opacity: 0.45 }} />
            <p className="font-medium">No emails found</p>
            <p className="text-muted text-sm">
              Try a different filter or ingest emails first.
            </p>
          </div>
        ) : (
          <table className="email-table">
            <thead>
              <tr>
                <th>Sender</th>
                <th>Subject</th>
                <th>Category</th>
                <th>Sentiment</th>
                <th>Urgency</th>
                <th>Status</th>
                <th>Conf.</th>
                <th><Clock size={12} /></th>
              </tr>
            </thead>
            <tbody>
              {emails.map(email => (
                <EmailRow key={email.id} email={email} onClick={handleRowClick} />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer count */}
      {!loading && emails.length > 0 && (
        <div className="table-footer">
          Showing {emails.length} of {total} emails
        </div>
      )}
    </div>
  )
}
