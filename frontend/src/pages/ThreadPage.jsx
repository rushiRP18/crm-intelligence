import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Send, AlertTriangle, Ban, Brain,
  Database, User, ChevronDown, ChevronUp,
  Clock, ExternalLink, Loader, Zap,
} from 'lucide-react'
import { emailsApi, draftsApi, agentApi, contactsApi } from '../lib/api'
import { format, formatDistanceToNow } from 'date-fns'
import './ThreadPage.css'

/* ── Urgency badge helper ───────────────────────────── */
const URGENCY_CLS = {
  Critical: 'badge-crimson',
  High:     'badge-amber',
  Medium:   'badge-blue',
  Low:      'badge-gray',
}
const SENTIMENT_DOT = {
  Positive: '#10b981',
  Negative: '#ef4444',
  Mixed:    '#f97316',
  Neutral:  '#6b7280',
}

/* ── Collapsible panel ──────────────────────────────── */
function Panel({ icon: Icon, title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="panel">
      <div className="panel-head" onClick={() => setOpen(!open)}>
        <div className="flex items-center gap-2">
          <Icon size={13} />
          <span>{title}</span>
        </div>
        {open ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
      </div>
      {open && <div className="panel-body">{children}</div>}
    </div>
  )
}

/* ── Agent Reasoning viewer ─────────────────────────── */
function ReasoningPanel({ trace }) {
  if (!trace) return null
  const blocks = trace.split(/\n\n+/).filter(Boolean)
  const type = (s) =>
    s.startsWith('Thought')    ? 'thought'
    : s.startsWith('Action')   ? 'action'
    : s.startsWith('Observation') ? 'obs'
    : s.startsWith('Decision') ? 'decision'
    : 'default'
  return (
    <Panel icon={Brain} title="Agent Reasoning Trace">
      <div className="trace-list">
        {blocks.map((b, i) => (
          <div key={i} className={`trace-block trace-${type(b)}`}>
            <pre>{b.trim()}</pre>
          </div>
        ))}
      </div>
    </Panel>
  )
}

/* ── RAG Chunks viewer ──────────────────────────────── */
function RAGPanel({ chunks }) {
  if (!chunks?.length) return null
  return (
    <Panel icon={Database} title={`Knowledge Sources (${chunks.length})`}>
      <div className="rag-list">
        {chunks.map((c, i) => (
          <div key={i} className="rag-chunk">
            <div className="rag-meta">
              <span className="rag-source">{c.source ?? 'unknown'}</span>
              <span className="rag-score">{((c.score ?? 0) * 100).toFixed(0)}% match</span>
            </div>
            <p className="rag-text">{(c.content ?? '').slice(0, 220)}…</p>
          </div>
        ))}
      </div>
    </Panel>
  )
}

/* ── Contact profile card ───────────────────────────── */
function ContactCard({ sender, contact }) {
  const initial = (sender?.[0] ?? '?').toUpperCase()
  return (
    <Panel icon={User} title="Contact Profile">
      <div className="contact-inner">
        <div className="contact-avatar">{initial}</div>
        <div className="contact-email">{sender ?? '—'}</div>
        {contact ? (
          <div className="contact-facts">
            {contact.status && (
              <div className="fact">
                <span className="fact-k">Status</span>
                <span className={`badge ${contact.status === 'VIP' ? 'badge-amber' : contact.status === 'Blocked' ? 'badge-red' : 'badge-gray'}`}>
                  {contact.status}
                </span>
              </div>
            )}
            {contact.company && (
              <div className="fact">
                <span className="fact-k">Company</span>
                <span className="fact-v">{contact.company}</span>
              </div>
            )}
            {contact.account_value != null && (
              <div className="fact">
                <span className="fact-k">Account Value</span>
                <span className="fact-v">${contact.account_value.toLocaleString()}</span>
              </div>
            )}
            {contact.churn_risk_score != null && (
              <div className="fact">
                <span className="fact-k">Churn Risk</span>
                <span
                  className="fact-v"
                  style={{ color: contact.churn_risk_score > 0.6 ? 'var(--red)' : 'var(--green)', fontWeight: 700 }}
                >
                  {(contact.churn_risk_score * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
        ) : (
          <p className="text-muted text-xs" style={{ marginTop: 8 }}>Contact not in CRM</p>
        )}
      </div>
    </Panel>
  )
}

/* ── Entities display ───────────────────────────────── */
function Entities({ ents }) {
  if (!ents) return null
  const items = [
    ...(ents.monetary_amounts ?? []).map(v => ({ label: `💰 ${v}`, cls: 'badge-green' })),
    ...(ents.ticket_ids       ?? []).map(v => ({ label: `🎟 ${v}`,  cls: 'badge-blue' })),
    ...(ents.order_ids        ?? []).map(v => ({ label: `📦 ${v}`,  cls: 'badge-violet' })),
    ...(ents.deadlines        ?? []).map(v => ({ label: `⏰ ${v}`,  cls: 'badge-amber' })),
    ...(ents.products_mentioned ?? []).map(v => ({ label: `📌 ${v}`, cls: 'badge-gray' })),
  ]
  if (!items.length) return null
  return (
    <div className="entities-row">
      {items.map((it, i) => (
        <span key={i} className={`badge ${it.cls}`}>{it.label}</span>
      ))}
    </div>
  )
}

/* ── Main Thread Page ───────────────────────────────── */
export default function ThreadPage() {
  const { threadId } = useParams()   // threadId is the email.id from inbox nav
  const navigate = useNavigate()

  const [emailDetail, setEmailDetail] = useState(null)
  const [thread, setThread]           = useState(null)
  const [contact, setContact]         = useState(null)
  const [loading, setLoading]         = useState(true)
  const [draftText, setDraftText]     = useState('')
  const [draftId, setDraftId]         = useState(null)
  const [sending, setSending]         = useState(false)
  const [processing, setProcessing]   = useState(false)
  const [processResult, setProcessResult] = useState(null)

  useEffect(() => {
    const emailId = decodeURIComponent(threadId)
    setLoading(true)

    // Load email detail
    emailsApi.get(emailId)
      .then(async ({ data }) => {
        setEmailDetail(data)
        if (data.draft?.body) {
          setDraftText(data.draft.body)
          setDraftId(data.draft.id)
        }

        // Load thread if we have thread_id
        if (data.thread_id) {
          try {
            // Get thread context from emails API (thread_id is int here, need string thread_id)
            // We load sibling emails via threads endpoint using thread's thread_id
            const threadStrId = data.thread_id  // int DB id; use email list instead
            // Fallback: load all emails from same thread_id
          } catch (_) {}
        }

        // Load contact
        if (data.sender) {
          contactsApi.get(data.sender)
            .then(r => setContact(r.data))
            .catch(() => setContact(null))
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [threadId])

  const handleApprove = async () => {
    if (!draftId) return
    setSending(true)
    try {
      await draftsApi.approve(draftId)
      // Refresh email detail
      const { data } = await emailsApi.get(decodeURIComponent(threadId))
      setEmailDetail(data)
      alert('✅ Draft approved and sent!')
    } catch (e) {
      alert('Error: ' + (e.response?.data?.message ?? e.message))
    } finally {
      setSending(false)
    }
  }

  const handleSaveDraft = async () => {
    if (!draftId || !draftText) return
    try {
      await draftsApi.edit(draftId, draftText)
      alert('Draft saved!')
    } catch (e) {
      alert('Save failed: ' + e.message)
    }
  }

  const handleProcess = async (dryRun = false) => {
    setProcessing(true)
    try {
      const emailId = decodeURIComponent(threadId)
      const { data } = dryRun
        ? await agentApi.dryRun(emailId)
        : await emailsApi.process(emailId)
      setProcessResult(data)

      if (!dryRun) {
        // Reload full email after processing
        const { data: fresh } = await emailsApi.get(emailId)
        setEmailDetail(fresh)
        if (fresh.draft?.body) {
          setDraftText(fresh.draft.body)
          setDraftId(fresh.draft.id)
        }
      }
    } catch (e) {
      alert('Processing error: ' + (e.response?.data?.message ?? e.message))
    } finally {
      setProcessing(false)
    }
  }

  if (loading) return (
    <div className="thread-loading">
      <div className="spinner" style={{ width: 32, height: 32 }} />
      <p className="text-muted">Loading email…</p>
    </div>
  )

  if (!emailDetail) return (
    <div className="thread-loading">
      <p className="font-medium">Email not found</p>
      <button className="btn btn-ghost" onClick={() => navigate('/inbox')} style={{ marginTop: 12 }}>
        <ArrowLeft size={14} /> Back to Inbox
      </button>
    </div>
  )

  const e = emailDetail
  const classification = {
    category:       e.category,
    sentiment:      e.sentiment,
    sentiment_score: e.sentiment_score,
    urgency:        e.urgency,
    confidence:     e.confidence,
    requires_human: e.requires_human,
    escalation_reason: e.escalation_reason,
  }

  const agentRun = e.agent_run
  const ragChunks = e.rag_context
  const escalations = e.escalations ?? []
  const isProcessed = !!e.category
  const isCritical = e.urgency === 'Critical'

  return (
    <div className="thread-page fade-in">
      {/* ── Header ─────────────────────────────────────── */}
      <div className="thread-header">
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/inbox')}>
          <ArrowLeft size={14} /> Inbox
        </button>
        <div className="thread-title">
          <h2>{e.subject ?? '(no subject)'}</h2>
          <div className="thread-meta">
            <span className="text-muted text-xs">From: {e.sender}</span>
            <span className="text-muted text-xs">·</span>
            <span className="text-muted text-xs">
              {e.timestamp ? format(new Date(e.timestamp), 'PPP HH:mm') : ''}
            </span>
          </div>
        </div>
        <div className="header-badges">
          <span className={`status-pill status-${e.status}`}>{(e.status ?? '').replace('_', ' ')}</span>
          {isCritical && <span className="badge badge-crimson">🔴 Critical</span>}
        </div>
      </div>

      {/* ── Escalation banner ──────────────────────────── */}
      {escalations.length > 0 && (
        <div className={`escalation-bar ${escalations[0].escalation_type === 'security' ? 'security' : escalations[0].escalation_type === 'legal' ? 'legal' : ''}`}>
          <AlertTriangle size={14} />
          <strong>{escalations[0].escalation_type?.toUpperCase()} ESCALATION</strong>
          <span>—</span>
          <span>{escalations[0].reason}</span>
          <span className={`badge ${escalations[0].priority === 'Critical' ? 'badge-crimson' : 'badge-amber'}`}>
            {escalations[0].priority}
          </span>
        </div>
      )}

      {/* ── 3-column workspace ─────────────────────────── */}
      <div className="workspace">
        {/* ── LEFT: Classification details ──────────────── */}
        <div className="col-left">
          <div className="col-label">Classification</div>

          {isProcessed ? (
            <div className="classif-card card">
              <div className="classif-row">
                <span className="classif-k">Category</span>
                <span className="badge badge-blue">{e.category}</span>
              </div>
              <div className="classif-row">
                <span className="classif-k">Sentiment</span>
                <span
                  className={`badge ${e.sentiment === 'Positive' ? 'badge-green' : e.sentiment === 'Negative' ? 'badge-red' : e.sentiment === 'Mixed' ? 'badge-orange' : 'badge-gray'}`}
                >
                  {e.sentiment}
                  {e.sentiment_score != null && ` (${e.sentiment_score?.toFixed(2)})`}
                </span>
              </div>
              <div className="classif-row">
                <span className="classif-k">Urgency</span>
                <span className={`badge ${URGENCY_CLS[e.urgency] ?? 'badge-gray'}`}>{e.urgency}</span>
              </div>
              <div className="classif-row">
                <span className="classif-k">Confidence</span>
                <span
                  className="classif-val"
                  style={{ color: (e.confidence ?? 0) < 0.7 ? 'var(--amber)' : 'var(--green)', fontWeight: 700 }}
                >
                  {e.confidence != null ? `${(e.confidence * 100).toFixed(0)}%` : '—'}
                </span>
              </div>
              <div className="classif-row">
                <span className="classif-k">Needs Human</span>
                <span className={`badge ${e.requires_human ? 'badge-amber' : 'badge-green'}`}>
                  {e.requires_human ? 'Yes' : 'No'}
                </span>
              </div>
              {e.escalation_reason && (
                <div className="escalation-note">
                  ⚠️ {e.escalation_reason}
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{ padding: 16 }}>
              <p className="text-muted text-sm">Not yet classified</p>
              <button
                className="btn btn-primary btn-sm"
                style={{ marginTop: 10 }}
                onClick={() => handleProcess(false)}
                disabled={processing}
              >
                {processing ? <Loader size={12} className="spin" /> : <Zap size={12} />}
                Run AI Agent
              </button>
            </div>
          )}

          {/* Dry run / re-process */}
          {isProcessed && (
            <div className="action-col">
              <button
                className="btn btn-ghost btn-sm w-full"
                onClick={() => handleProcess(true)}
                disabled={processing}
              >
                {processing ? <Loader size={12} className="spin" /> : <Brain size={12} />}
                Dry Run (Preview)
              </button>
              <button
                className="btn btn-ghost btn-sm w-full"
                onClick={() => handleProcess(false)}
                disabled={processing}
              >
                {processing ? <Loader size={12} className="spin" /> : <ExternalLink size={12} />}
                Re-Process
              </button>
            </div>
          )}

          {/* Process result */}
          {processResult && (
            <div className="process-result card">
              <div className="text-xs font-semibold text-accent" style={{ marginBottom: 8 }}>
                {processResult.dry_run ? '🔍 Dry Run Result' : '✅ Agent Result'}
              </div>
              <div className="classif-row">
                <span className="classif-k">Decision</span>
                <span className="badge badge-violet">{processResult.decision}</span>
              </div>
              <div className="classif-row">
                <span className="classif-k">Action</span>
                <span className="badge badge-indigo">{processResult.final_action}</span>
              </div>
              {processResult.reasoning_trace && (
                <details style={{ marginTop: 10 }}>
                  <summary className="text-xs text-muted" style={{ cursor: 'pointer' }}>
                    View trace
                  </summary>
                  <pre className="trace-pre">{processResult.reasoning_trace}</pre>
                </details>
              )}
            </div>
          )}
        </div>

        {/* ── CENTER: Email body + Draft ─────────────────── */}
        <div className="col-center">
          {/* Email viewer */}
          <div className="card email-viewer">
            <div className="email-header">
              <div className="email-from">
                <div className="avatar" style={{ float: 'none', flexShrink: 0 }}>
                  {(e.sender?.[0] ?? '?').toUpperCase()}
                </div>
                <div>
                  <div className="font-semibold">{e.sender}</div>
                  <div className="text-xs text-muted">
                    {e.timestamp ? format(new Date(e.timestamp), 'PPP · HH:mm') : ''}
                  </div>
                </div>
              </div>
              {/* Detected entities */}
              <Entities ents={e.detected_entities} />
            </div>

            <h3 className="email-subject">{e.subject ?? '(no subject)'}</h3>
            <div className="email-body">{e.body ?? '(empty body)'}</div>
          </div>

          {/* Draft editor */}
          <div className="card draft-card" style={{ marginTop: 14 }}>
            <div className="draft-header">
              <span className="font-semibold">AI Draft Reply</span>
              <div className="flex items-center gap-2">
                {draftText && <span className="badge badge-violet">✨ AI Generated</span>}
                {e.draft?.tone && <span className="badge badge-gray">{e.draft.tone}</span>}
              </div>
            </div>

            {draftText ? (
              <>
                <textarea
                  className="input draft-textarea"
                  value={draftText}
                  onChange={ev => setDraftText(ev.target.value)}
                  rows={9}
                  placeholder="Edit the draft before sending…"
                />
                {e.draft?.policy_refs?.length > 0 && (
                  <div className="policy-refs">
                    <span className="text-xs text-muted">Policies cited:</span>
                    {e.draft.policy_refs.map(r => (
                      <span key={r} className="badge badge-indigo">{r}</span>
                    ))}
                  </div>
                )}
                <div className="draft-actions">
                  <button
                    className="btn btn-success"
                    onClick={handleApprove}
                    disabled={sending || e.draft?.status === 'sent'}
                  >
                    {sending ? <Loader size={13} className="spin" /> : <Send size={13} />}
                    {e.draft?.status === 'sent' ? 'Already Sent' : 'Approve & Send'}
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={handleSaveDraft}>
                    💾 Save Edits
                  </button>
                  <button className="btn btn-danger btn-sm">
                    <Ban size={12} /> Reject
                  </button>
                </div>
              </>
            ) : (
              <div className="no-draft">
                {escalations.length > 0 ? (
                  <div className="escalation-note-center">
                    <AlertTriangle size={16} style={{ color: 'var(--amber)' }} />
                    <span>Escalated — no auto-reply sent.</span>
                    <span className="badge badge-amber">{escalations[0].escalation_type}</span>
                  </div>
                ) : (
                  <p className="text-muted text-sm">
                    No draft generated yet. Run the AI agent to generate a reply.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ── RIGHT: Contact + Reasoning + RAG ──────────── */}
        <div className="col-right">
          <ContactCard sender={e.sender} contact={contact} />
          {agentRun?.reasoning_trace && (
            <ReasoningPanel trace={agentRun.reasoning_trace} />
          )}
          {ragChunks?.length > 0 && (
            <RAGPanel chunks={ragChunks} />
          )}
          {/* Agent run meta */}
          {agentRun && (
            <Panel icon={Clock} title="Agent Run Info">
              <div className="run-facts">
                <div className="fact"><span className="fact-k">Decision</span><span className="badge badge-violet">{agentRun.decision}</span></div>
                <div className="fact"><span className="fact-k">Action</span><span className="badge badge-indigo">{agentRun.final_action}</span></div>
                <div className="fact"><span className="fact-k">Duration</span><span className="fact-v">{agentRun.run_duration_ms?.toFixed(0)}ms</span></div>
                {agentRun.tool_calls?.length > 0 && (
                  <div className="fact"><span className="fact-k">Tool Calls</span><span className="fact-v">{agentRun.tool_calls.length}</span></div>
                )}
              </div>
            </Panel>
          )}
        </div>
      </div>
    </div>
  )
}
