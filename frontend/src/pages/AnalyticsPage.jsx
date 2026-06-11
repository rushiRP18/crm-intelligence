import { useState, useEffect } from 'react'
import { analyticsApi, intelligenceApi } from '../lib/api'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { BarChart3, TrendingUp, TrendingDown, Globe } from 'lucide-react'
import './AnalyticsPage.css'

/* ── Color maps ──────────────────────────────────────── */
const CATEGORY_COLORS = {
  Complaint:         '#ef4444',
  'Bug Report':      '#f97316',
  Legal:             '#dc2626',
  Security:          '#7c3aed',
  Compliance:        '#2563eb',
  Billing:           '#d97706',
  Spam:              '#6b7280',
  Internal:          '#8b5cf6',
  Inquiry:           '#3b82f6',
  'Feature Request': '#10b981',
  Other:             '#94a3b8',
}

/* ── Stat Card ───────────────────────────────────────── */
function StatCard({ label, value, sub, color, trend }) {
  return (
    <div className="stat-card">
      <div className="stat-lbl">{label}</div>
      <div className="stat-val" style={{ color: color || 'var(--text-1)' }}>
        {value ?? '—'}
      </div>
      {sub   && <div className="stat-sub">{sub}</div>}
      {trend && (
        <div className={`stat-trend ${trend === 'up' ? 'up' : 'down'}`}>
          {trend === 'up' ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
        </div>
      )}
    </div>
  )
}

/* ── Custom Recharts tooltip ─────────────────────────── */
const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      {label && <div className="tooltip-label">{label}</div>}
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color || 'var(--text-1)', fontSize: '0.78rem' }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(3) : p.value}</strong>
        </div>
      ))}
    </div>
  )
}

/* ── Analytics page ──────────────────────────────────── */
export default function AnalyticsPage() {
  const [summary,     setSummary]     = useState(null)
  const [sentiment,   setSentiment]   = useState([])
  const [categories,  setCategories]  = useState([])
  const [reputation,  setReputation]  = useState(null)
  const [days,        setDays]        = useState(30)
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [s, st, cat, rep] = await Promise.allSettled([
          analyticsApi.summary(),
          analyticsApi.sentimentTrend({ days }),
          analyticsApi.categoryBreakdown({ days }),
          intelligenceApi.reputation(),
        ])
        if (s.status   === 'fulfilled') setSummary(s.value.data)
        if (st.status  === 'fulfilled') setSentiment(st.value.data.data_points ?? [])
        if (cat.status === 'fulfilled') setCategories(cat.value.data.categories ?? [])
        if (rep.status === 'fulfilled') setReputation(rep.value.data)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [days])

  if (loading) return (
    <div className="analytics-loading">
      <div className="spinner" style={{ width: 32, height: 32 }} />
      <p className="text-muted">Loading analytics…</p>
    </div>
  )

  if (error) return (
    <div className="analytics-loading">
      <p className="text-muted">Failed to load analytics: {error}</p>
      <p className="text-xs text-muted">Make sure the backend is running on port 8000.</p>
    </div>
  )

  const avgSentUp = summary?.avg_sentiment_score != null && summary.avg_sentiment_score > 0

  return (
    <div className="analytics-page fade-in">
      {/* ── Header ─────────────────────────────────────── */}
      <div className="analytics-header">
        <div>
          <h1 className="page-title">
            <BarChart3 size={22} />
            Analytics Dashboard
          </h1>
          <p className="text-muted text-sm" style={{ marginTop: 2 }}>
            AI performance metrics · business intelligence · public reputation
          </p>
        </div>
        <select
          className="input days-select"
          value={days}
          onChange={e => setDays(+e.target.value)}
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={180}>Last 180 days</option>
          <option value={365}>Last 365 days</option>
        </select>
      </div>

      {/* ── KPI Grid ───────────────────────────────────── */}
      {summary && (
        <div className="kpi-grid">
          <StatCard label="Total Emails"   value={summary.total_emails?.toLocaleString()} />
          <StatCard label="Escalated"      value={summary.escalated}      color="var(--amber)"  sub={`${summary.escalation_rate}% rate`} />
          <StatCard label="Needs Human"    value={summary.needs_human}    color="var(--red)" />
          <StatCard label="Auto Replied"   value={summary.auto_replied}   color="var(--green)"  sub={`${summary.auto_reply_rate}% rate`} />
          <StatCard label="Spam Filtered"  value={summary.spam}           color="var(--gray)" />
          <StatCard
            label="Avg Confidence"
            value={summary.avg_confidence ? `${(summary.avg_confidence * 100).toFixed(1)}%` : '—'}
            color="var(--accent-light)"
          />
          <StatCard
            label="Avg Sentiment"
            value={summary.avg_sentiment_score?.toFixed(3)}
            color={avgSentUp ? 'var(--green)' : 'var(--red)'}
            trend={avgSentUp ? 'up' : 'down'}
          />
          <StatCard label="At-Risk Contacts" value={summary.at_risk_contacts} color="var(--crimson)" />
        </div>
      )}

      {/* ── Sentiment trend line chart ──────────────────── */}
      <div className="chart-block card">
        <div className="chart-title">Sentiment Trend</div>
        <p className="text-muted text-xs" style={{ marginBottom: 16 }}>
          Daily average sentiment score — −1.0 (very negative) to +1.0 (very positive)
        </p>
        {sentiment.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={sentiment} margin={{ top: 4, right: 20, bottom: 4, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis
                dataKey="date"
                tick={{ fill: 'var(--text-3)', fontSize: 10 }}
                tickLine={false}
              />
              <YAxis
                domain={[-1, 1]}
                tick={{ fill: 'var(--text-3)', fontSize: 10 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fill: 'var(--text-3)', fontSize: 10 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<ChartTooltip />} />
              <ReferenceLine y={0} stroke="rgba(255,255,255,0.1)" strokeDasharray="4 4" />
              <Line
                type="monotone"
                dataKey="avg_score"
                name="Sentiment"
                stroke="var(--accent)"
                strokeWidth={2.5}
                dot={{ fill: 'var(--accent)', r: 3, strokeWidth: 0 }}
                activeDot={{ r: 5, fill: 'var(--accent-light)' }}
              />
              {sentiment[0]?.email_count !== undefined && (
                <Line
                  type="monotone"
                  dataKey="email_count"
                  name="Volume"
                  stroke="rgba(255,255,255,0.25)"
                  strokeWidth={1.5}
                  dot={false}
                  yAxisId="right"
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-chart">
            No sentiment data yet — ingest and process emails to see trends.
          </div>
        )}
      </div>

      {/* ── Two-column charts ───────────────────────────── */}
      <div className="chart-row">
        {/* Pie chart */}
        <div className="chart-block card">
          <div className="chart-title">Category Breakdown</div>
          {categories.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={categories}
                    dataKey="count"
                    nameKey="category"
                    cx="50%" cy="50%"
                    outerRadius={80}
                    innerRadius={42}
                    strokeWidth={0}
                  >
                    {categories.map(c => (
                      <Cell key={c.category} fill={CATEGORY_COLORS[c.category] ?? '#6b7280'} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v, n) => [`${v} emails`, n]} />
                </PieChart>
              </ResponsiveContainer>
              <div className="legend-grid">
                {categories.slice(0, 8).map(c => (
                  <div key={c.category} className="legend-item">
                    <div className="legend-dot" style={{ background: CATEGORY_COLORS[c.category] ?? '#6b7280' }} />
                    <span className="legend-cat">{c.category}</span>
                    <span className="legend-pct">{c.percentage}%</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty-chart">No classification data yet</div>
          )}
        </div>

        {/* Public reputation */}
        <div className="chart-block card">
          <div className="chart-title">
            <Globe size={14} style={{ display: 'inline', marginRight: 5, verticalAlign: 'middle' }} />
            Public Reputation (Mock Intelligence)
          </div>
          {reputation ? (
            <div className="reputation-list">
              {Object.entries(reputation).map(([domain, data]) => (
                <div key={domain} className="rep-item">
                  <div className="rep-header">
                    <span className="rep-domain">{domain}</span>
                    <span
                      className={`rep-trend-badge ${data.trend === 'declining' ? 'declining' : data.trend === 'improving' ? 'improving' : 'stable'}`}
                    >
                      {data.trend === 'declining' ? '↘ Declining' : data.trend === 'improving' ? '↗ Improving' : '→ Stable'}
                    </span>
                  </div>
                  <div className="rep-stars">
                    {'★'.repeat(Math.round(data.rating ?? 0))}
                    {'☆'.repeat(5 - Math.round(data.rating ?? 0))}
                    <span className="rep-score-val">{data.rating}/5</span>
                    <span className="rep-count">{data.review_count?.toLocaleString()} reviews</span>
                  </div>
                  {data.top_complaints?.length > 0 && (
                    <div className="rep-tags">
                      {data.top_complaints.slice(0, 3).map(c => (
                        <span key={c} className="badge badge-red">{c}</span>
                      ))}
                    </div>
                  )}
                  {data.recent_highlights?.length > 0 && (
                    <p className="rep-highlight">"{data.recent_highlights[0]}"</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-chart">No reputation data</div>
          )}
        </div>
      </div>

      {/* ── Volume bar chart ────────────────────────────── */}
      <div className="chart-block card">
        <div className="chart-title">Email Volume by Category</div>
        {categories.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={categories} margin={{ top: 4, right: 16, bottom: 4, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis
                dataKey="category"
                tick={{ fill: 'var(--text-3)', fontSize: 9 }}
                tickLine={false}
              />
              <YAxis tick={{ fill: 'var(--text-3)', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Bar dataKey="count" name="Emails" radius={[4, 4, 0, 0]}>
                {categories.map(c => (
                  <Cell key={c.category} fill={CATEGORY_COLORS[c.category] ?? 'var(--accent)'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-chart">No data yet</div>
        )}
      </div>

      {/* ── Escalation / Auto-reply rates ───────────────── */}
      {summary && (
        <div className="rates-row">
          <div className="rate-card card">
            <div className="rate-label">Escalation Rate</div>
            <div
              className="rate-val"
              style={{ color: summary.escalation_rate > 40 ? 'var(--red)' : summary.escalation_rate > 20 ? 'var(--amber)' : 'var(--green)' }}
            >
              {summary.escalation_rate}%
            </div>
            <div className="rate-bar-wrap">
              <div
                className="rate-bar-fill"
                style={{
                  width: `${Math.min(summary.escalation_rate, 100)}%`,
                  background: summary.escalation_rate > 40 ? 'var(--red)' : summary.escalation_rate > 20 ? 'var(--amber)' : 'var(--green)',
                }}
              />
            </div>
          </div>
          <div className="rate-card card">
            <div className="rate-label">Auto-Reply Rate</div>
            <div className="rate-val" style={{ color: 'var(--green)' }}>
              {summary.auto_reply_rate}%
            </div>
            <div className="rate-bar-wrap">
              <div
                className="rate-bar-fill"
                style={{ width: `${Math.min(summary.auto_reply_rate, 100)}%`, background: 'var(--green)' }}
              />
            </div>
          </div>
          <div className="rate-card card">
            <div className="rate-label">Avg Agent Confidence</div>
            <div className="rate-val" style={{ color: 'var(--accent-light)' }}>
              {summary.avg_confidence ? `${(summary.avg_confidence * 100).toFixed(1)}%` : '—'}
            </div>
            {summary.avg_confidence && (
              <div className="rate-bar-wrap">
                <div
                  className="rate-bar-fill"
                  style={{ width: `${(summary.avg_confidence * 100).toFixed(1)}%`, background: 'var(--accent)' }}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
