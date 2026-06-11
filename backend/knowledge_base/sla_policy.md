# Service Level Agreement (SLA) Policy — CRM Intelligence Platform

**Effective Date:** January 1, 2024  
**Last Updated:** June 1, 2024  
**Document Owner:** Engineering & Customer Success  
**Version:** 2.3

---

## 1. Overview and Scope

This Service Level Agreement ("SLA") defines the performance standards, support response commitments, and remediation procedures that CRM Intelligence Platform ("Company") provides to paying customers. This SLA is incorporated by reference into the Master Subscription Agreement (MSA) and is binding upon Company and Customer.

**This SLA applies to:**
- Standard plan customers
- Pro plan customers
- Enterprise plan customers

**This SLA does NOT apply to:**
- Free plan users (best-effort support only)
- Beta features explicitly labeled as "Preview" or "Beta"
- Downtime caused by Customer actions or third-party services outside Company control

---

## 2. Service Availability (Uptime Guarantee)

### 2.1 Uptime Commitment

| Plan       | Monthly Uptime Guarantee | Maximum Monthly Downtime |
|------------|--------------------------|--------------------------|
| Standard   | 99.9%                    | 43.8 minutes/month       |
| Pro        | 99.9%                    | 43.8 minutes/month       |
| Enterprise | 99.99%                   | 4.38 minutes/month       |

**Uptime Formula:**
```
Uptime % = ((Total Minutes in Month - Downtime Minutes) / Total Minutes in Month) × 100
```

Where **Total Minutes in Month** = number of days in calendar month × 24 × 60.

For a 30-day month: 30 × 24 × 60 = **43,200 minutes**

**99.9% SLA:** Maximum allowable downtime = 43,200 × 0.001 = **43.2 minutes/month**  
**99.99% SLA:** Maximum allowable downtime = 43,200 × 0.0001 = **4.32 minutes/month**

### 2.2 What Counts as Downtime

**Included in downtime calculation:**
- Complete service unavailability (HTTP 5xx errors on all requests)
- API endpoint failures affecting >25% of requests for >5 consecutive minutes
- Authentication service failures preventing any user login
- Data pipeline failures preventing data ingestion for >30 minutes

**Excluded from downtime calculation:**
- Scheduled maintenance windows (announced 72+ hours in advance)
- Downtime caused by customer-side network, hardware, or configuration issues
- Force majeure events (natural disasters, acts of government, large-scale internet outages)
- Issues caused by third-party services (e.g., AWS global outages) that affect all customers equally
- Free plan service interruptions
- Beta/preview feature unavailability

### 2.3 Scheduled Maintenance Windows

- **Preferred window:** Tuesdays and Thursdays, 02:00–04:00 UTC
- **Advance notice:** Minimum 72 hours via email and status page (status.company.com)
- **Emergency maintenance:** Minimum 1-hour notice; communicated via status page and in-app banner
- **Duration limit:** Scheduled maintenance shall not exceed 4 hours per month for Standard/Pro; 2 hours for Enterprise
- Enterprise customers receive dedicated maintenance scheduling in coordination with their CSM

---

## 3. Incident Priority Levels

All incidents are classified into four priority levels (P0–P3) based on business impact. Priority is initially assigned by the reporting customer or by automated monitoring systems, subject to validation by the on-call engineering team.

### 3.1 P0 — Critical (Production Down)

**Definition:** Complete or near-complete service outage affecting all or most customers. The production environment is down, rendering the platform entirely unusable.

**Examples:**
- API returns 5xx errors for >90% of requests
- Login/authentication service completely unavailable
- Database unavailable; no data can be read or written
- Complete data loss event
- Security breach or active ransomware attack

**SLA Commitments:**
| Metric | Target |
|--------|--------|
| **Initial Response Time** | Within **15 minutes** of ticket creation or alert trigger |
| **Resolution Target** | Within **2 hours** |
| **Customer Update Frequency** | Every 30 minutes during active incident |
| **Root Cause Analysis (RCA) Delivery** | Within **24 hours** of resolution |
| **Notification Channels** | Phone (Enterprise), Email, Status Page, In-App Banner |

**Internal Escalation (auto-triggered):**
- T+0: On-call engineer paged
- T+15 min: Engineering Lead notified if not acknowledged
- T+30 min: CTO notified
- T+1 hour: CEO notified if Enterprise customer affected

### 3.2 P1 — High (Major Feature Broken)

**Definition:** A major product feature is broken or severely degraded, significantly impacting customer workflows, but a workaround may exist.

**Examples:**
- AI/ML inference pipeline returning incorrect results for >50% of queries
- Webhook delivery failing for all events
- Reporting/analytics module completely unavailable
- API rate limiting incorrectly blocking valid requests
- Data sync failure lasting >1 hour

**SLA Commitments:**
| Metric | Target |
|--------|--------|
| **Initial Response Time** | Within **1 hour** of ticket creation |
| **Resolution Target** | Within **8 hours** |
| **Customer Update Frequency** | Every 2 hours during active incident |
| **Post-Incident Report** | Within 48 hours of resolution (Enterprise) |
| **Notification Channels** | Email, Status Page |

**Internal Escalation:**
- T+0: On-call engineer assigned
- T+1 hour: Engineering Lead notified if not acknowledged
- T+4 hours: VP Engineering notified if unresolved

### 3.3 P2 — Medium (Degraded Performance)

**Definition:** The service is operational but experiencing degraded performance or intermittent issues that impact the customer experience but do not prevent core workflows.

**Examples:**
- API latency >3x baseline (e.g., normally 100ms, now >300ms consistently)
- Intermittent errors affecting <25% of requests
- Slow dashboard load times (>10 seconds)
- Non-critical integrations failing intermittently
- UI rendering issues in non-critical sections

**SLA Commitments:**
| Metric | Target |
|--------|--------|
| **Initial Response Time** | Within **4 hours** of ticket creation |
| **Resolution Target** | Within **24 hours** |
| **Customer Update Frequency** | Every 8 hours |
| **Notification Channels** | Email (if customer-reported), Status Page |

### 3.4 P3 — Low (Minor Issue)

**Definition:** Minor issues, cosmetic bugs, or feature requests that have minimal impact on the customer's ability to use the platform.

**Examples:**
- UI cosmetic issues (misaligned elements, typos)
- Non-critical feature requests
- Documentation errors or questions
- Minor configuration assistance
- Non-impacting performance observations

**SLA Commitments:**
| Metric | Target |
|--------|--------|
| **Initial Response Time** | Within **24 hours** (business hours) |
| **Resolution Target** | Within **72 hours** (business hours) |
| **Update Frequency** | As needed; at least once per week if open |
| **Channels** | Email support, Help Center |

---

## 4. Root Cause Analysis (RCA) Process

### 4.1 RCA Requirements

An RCA document is mandatory for all P0 incidents and recommended for P1 incidents affecting Enterprise customers.

**RCA Delivery Timeline:** Within **24 hours** of P0 resolution confirmation.

### 4.2 RCA Document Contents

Each RCA document shall include:

1. **Incident Summary** — Plain-language description of what occurred
2. **Timeline** — Chronological log of events from detection to resolution (UTC timestamps)
3. **Impact Assessment** — Customers affected, duration, data affected (if any)
4. **Root Cause** — Technical explanation of the underlying cause
5. **Immediate Remediation** — Actions taken to resolve the incident
6. **Preventive Actions** — Changes to prevent recurrence (with owner and ETA for each item)
7. **Monitoring Improvements** — Gaps in detection that will be addressed

### 4.3 RCA Distribution

- Enterprise customers: RCA delivered via email to primary contact and Customer Success Manager
- Standard/Pro customers: RCA summary published on status.company.com post-incident page
- Internal: Full RCA stored in incident management system with 5-year retention

---

## 5. SLA Credit Calculation

### 5.1 Credit Eligibility

Customers are eligible for SLA credits when:
1. Monthly uptime falls below the guaranteed threshold for their plan
2. The incident was not caused by Customer actions or excluded circumstances (Section 2.2)
3. The credit claim is submitted within **7 days** of the incident end date
4. The customer account is in good standing (no overdue invoices)

### 5.2 Credit Formula

```
SLA Credit = (Actual Downtime Minutes / Total Minutes in Month) × Monthly Fee
```

**Maximum Credit Cap:** Credits are capped at **30% of the customer's monthly fee** for the affected month, regardless of actual downtime.

**Example Calculation:**
- Customer Plan: Pro at $299/month
- Month: June (30 days = 43,200 minutes)
- Actual downtime: 500 minutes (P0 incident)
- Credit = (500 / 43,200) × $299 = 0.01157 × $299 = **$3.46**
- Cap check: 30% of $299 = $89.70 — credit is below cap, so $3.46 applies

**Enterprise Example (exceeding cap):**
- Enterprise customer: $10,000/month
- Downtime: 15,000 minutes (10.4 days — highly unusual scenario)
- Calculated credit: (15,000 / 43,200) × $10,000 = $3,472.22
- Cap: 30% × $10,000 = $3,000.00
- **Credit applied: $3,000.00** (capped)

### 5.3 Credit Form and Application

**Credits are applied as account credits to the next invoice — not as cash refunds.**

- Credits appear as a line item on the next billing cycle's invoice
- Credits cannot be transferred to another account
- Credits do not expire for 12 months from the date of issue
- For annual plan customers, credits are applied to the next monthly equivalent period or the renewal invoice

### 5.4 How to Claim SLA Credits

1. Submit a support ticket at support.company.com with subject: "SLA Credit Request — [Incident Date]"
2. Include: Account name, affected date/time range, and a brief description of the impact experienced
3. Claims must be submitted within **7 calendar days** of the incident end date — late claims are not eligible
4. Company will validate claim against internal monitoring data within 5 business days
5. Approved credits will appear on the next invoice

---

## 6. Support Channels and Hours

| Channel            | Free         | Standard       | Pro                     | Enterprise               |
|--------------------|--------------|----------------|-------------------------|--------------------------|
| **Community Forum** | ✓ (all)     | ✓              | ✓                       | ✓                        |
| **Help Center/Docs** | ✓ (all)    | ✓              | ✓                       | ✓                        |
| **Email Support**  | —            | ✓ (48h SLA)    | ✓ (4h SLA)              | ✓ (1h SLA)               |
| **Live Chat**      | —            | —              | Business hours           | 24/7                     |
| **Phone Support**  | —            | —              | —                       | 24/7 dedicated line      |
| **Slack/Teams Channel** | —       | —              | Optional add-on         | ✓ (dedicated channel)    |
| **Dedicated CSM**  | —            | —              | —                       | ✓                        |

**Business Hours:** Monday–Friday, 09:00–18:00 US Eastern Time (ET), excluding US federal holidays.  
**Emergency/P0 Support:** Available 24/7/365 for Standard, Pro, and Enterprise customers via the emergency support line listed in the customer portal.

---

## 7. Monitoring and Incident Detection

### 7.1 Monitoring Infrastructure

- Real-time synthetic monitoring from 5 global locations (US East, US West, EU West, Asia Pacific, South America)
- API health checks every 60 seconds
- Database performance metrics collected every 30 seconds
- Automated alerting threshold: 3 consecutive failed health checks trigger P0 incident

### 7.2 Status Page

**Public Status Page:** https://status.company.com

- Real-time service status by component (API, Dashboard, Webhooks, AI Engine, Data Pipeline)
- Historical uptime data (90-day rolling)
- Incident history with post-mortems
- Subscribe for email/SMS/webhook notifications

### 7.3 Incident Communication

All incidents are communicated via:
1. Status page update (within 10 minutes of detection for P0, 30 minutes for P1)
2. Email notification to account admin (for P0 and P1)
3. In-app banner (for P0)
4. Proactive outreach from CSM (Enterprise customers, P0 and P1)

---

## 8. SLA Exclusions and Limitations

The following are explicitly excluded from SLA uptime calculations and credit eligibility:

1. **Force Majeure:** Events beyond Company's reasonable control including natural disasters, acts of war, government actions, or widespread internet infrastructure failures
2. **Scheduled Maintenance:** Pre-announced maintenance windows per Section 2.3
3. **Customer-Caused Issues:** Outages resulting from customer's improper configuration, scripts, or exceeding rate limits causing cascading failures
4. **Third-Party Services:** Failures in third-party services (e.g., payment processors, email providers, OAuth providers) that are outside Company's infrastructure
5. **Free Plan:** Free plan is provided on a best-effort basis with no uptime guarantees
6. **Beta Features:** Any feature labeled "Beta," "Preview," or "Experimental"
7. **Abuse or ToS Violations:** Service suspension due to violation of Terms of Service or Acceptable Use Policy

---

## 9. SLA Review and Amendment

- This SLA is reviewed quarterly by the Engineering and Customer Success leadership teams
- Customers will be notified of material changes to this SLA at least 30 days in advance via email
- The most current version of this SLA is always available at: https://company.com/legal/sla
- For Enterprise customers, any SLA modifications negotiated in the MSA supersede this standard SLA

---

## 10. Contact Information for SLA Matters

| Purpose                    | Contact                     | Response Time (P0) |
|----------------------------|-----------------------------|-------------------|
| General Support            | support@company.com          | Per priority tier |
| P0 Emergency (Enterprise)  | Listed in customer portal    | 15 minutes        |
| SLA Credit Claims          | billing@company.com          | 5 business days   |
| Status Page Subscriptions  | status.company.com           | Automated         |
| Escalation (Enterprise)    | Your dedicated CSM           | 15 minutes (P0)   |
