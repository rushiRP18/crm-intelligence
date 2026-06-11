# Escalation Matrix — CRM Intelligence Platform

**Effective Date:** January 1, 2024  
**Last Updated:** June 1, 2024  
**Document Owner:** Customer Success, Legal, Security & Engineering  
**Version:** 2.0  
**Classification:** Internal Use Only

---

## 1. Purpose

This Escalation Matrix defines the mandatory escalation paths, response owners, time-to-escalate requirements, and critical behavioral rules for all high-stakes situations encountered by CRM Intelligence Platform staff. All customer-facing teams (Support, Customer Success, Sales) must adhere to this matrix.

> **CRITICAL:** When in doubt, escalate. Never handle a high-risk situation alone.

---

## 2. Escalation Matrix — Quick Reference

| Situation | Priority | Primary Owner | Escalation Path | Time to Escalate | Key Rule |
|-----------|----------|--------------|-----------------|-----------------|----------|
| Legal threats / Cease & Desist | P0 | Legal Counsel | legal@company.com | **Within 1 hour** | DO NOT reply to sender |
| Security incident / Ransomware | P0 | SecOps Team | security@company.com + CTO | **Immediate** | NEVER reply to attacker |
| VIP Churn risk | P1 | Account Manager | Account Manager + VP Sales | **Within 2 hours** | Offer retention package |
| GDPR requests | P1 | DPO | dpo@company.com | **Within 24 hours** | Auto-acknowledge to sender |
| Press / Media inquiries | P1 | PR Team | pr@company.com | **Immediate** | Do not comment without approval |
| P0 Infrastructure incident | P0 | Engineering Lead | Eng Lead + Account Team + CEO (if Enterprise) | **Immediate** | Per SLA protocol |
| Reputation crisis (3+ reviews) | P1 | CS VP + PR | customersuccess@company.com + pr@company.com | **Within 2 hours** | No promises about review removal |
| Investor inquiries | P2 | CEO/CFO | ceo@company.com + cfo@company.com | **Within 4 hours** | Do not confirm/deny fundraising |

---

## 3. Detailed Escalation Procedures

---

### 3.1 Legal Threats / Cease & Desist Letters

**Trigger Events:**
- Receipt of a Cease & Desist (C&D) letter
- Customer or third party explicitly threatens legal action in writing or verbally
- Receipt of attorney/law firm correspondence on behalf of a third party
- Patent infringement claim or assertion
- Demand letter of any kind from legal counsel

**⚠️ CRITICAL RULE:** DO NOT reply to the sender. Do not acknowledge, deny, or comment. Do not forward without legal review. Immediately preserve all correspondence.

**Escalation Path:**
1. **T+0:** Do not respond; preserve all original correspondence (do not edit, do not delete)
2. **T+0 to T+1 hour:** Forward to **Legal Counsel** at legal@company.com with subject: "URGENT: Legal Threat — [Brief Description] — [Date]"
3. **T+1 hour:** If Legal does not acknowledge within 1 hour, call the Legal Counsel's emergency mobile number (available from VP Operations)
4. **T+1 hour:** Notify VP Operations and CEO via Slack DM: "Legal threat received — escalated to legal team"
5. **All further communication:** Handled exclusively by Legal Counsel or designated outside counsel

**Documentation Required:**
- Original correspondence (scan physical; screenshot/PDF digital)
- Context: date received, method of delivery, any prior interactions with the sender
- Logged in the incident tracker with tag: "LEGAL THREAT"

**Post-Escalation:**
- Do not discuss the matter with other colleagues or externally
- Do not post about it on internal or external channels
- Only legal team may communicate with the sender or their attorneys

---

### 3.2 Security Incidents / Ransomware / Data Breaches

**Trigger Events:**
- Detection of ransomware or malware in Company systems
- Unauthorized access to customer or Company data
- Data exfiltration (suspected or confirmed)
- Credential compromise of admin or service accounts
- Phishing attack that resulted in credential entry
- Unusual large-scale data deletion or encryption
- Receipt of ransom demand

**⚠️ CRITICAL RULE:** NEVER reply to the attacker. Do not pay ransom without Board/Legal approval. Immediately isolate affected systems. Preserve evidence.

**Escalation Path:**
1. **T+0:** Isolate affected systems (disconnect from network — do NOT power off if ransomware, to preserve volatile memory)
2. **T+0:** Alert **SecOps Team** immediately at security@company.com AND via Slack #security-incidents channel
3. **T+0:** Notify **CTO** directly via phone/Slack DM — do not wait for email response
4. **T+15 min:** If CTO not reachable, notify CEO
5. **T+30 min:** SecOps initiates incident response plan (IRP-001)
6. **T+1 hour:** If data breach confirmed, begin GDPR 72-hour notification clock assessment
7. **T+2 hours:** Legal Counsel notified for regulatory and liability assessment
8. **T+4 hours:** Prepare customer communication (do not send without Legal/CEO approval)

**Do NOT:**
- Reply to ransom demands or communications from attacker
- Attempt to negotiate without Legal/Board approval
- Power off systems without SecOps guidance (destroys forensic evidence)
- Restore from backups before forensic capture
- Announce publicly without PR team coordination

**External Resources:**
- Incident Response retainer firm: [IR Firm Name] — contact via VP Security
- Cyber insurance carrier: [Insurance Carrier] — policy number in secure vault
- FBI Cyber Division: 1-855-292-3937 (if criminal referral warranted)

---

### 3.3 VIP Customer Churn Risk

**Trigger Events:**
- VIP customer (Enterprise, >$500/mo spend, or >24 months tenure) submits cancellation request
- VIP customer threatens cancellation in writing or verbally
- VIP customer NPS drops to ≤5
- VIP customer has 3+ unresolved support tickets older than 7 days
- VIP customer reduces seat count by >50%

**Escalation Path:**
1. **T+0:** CRM alert fires; Account Manager assigned receives immediate Slack notification
2. **T+0 to T+2 hours:** Account Manager reviews account health in CRM and contacts VP Sales via Slack
3. **T+2 hours:** Account Manager AND VP Sales jointly develop retention package (see Refund Policy — Section 3.2)
4. **T+2 hours:** Account Manager initiates personal outreach to customer (call preferred over email)
5. **T+4 hours if no contact:** VP Sales personally reaches out to customer's C-level stakeholder if known
6. **Offer authorization limits:**
   - Account Manager can authorize: 1 free month + priority support upgrade
   - VP Sales can authorize: 2 free months + locked pricing for 12 months
   - CEO approval required: Any offer >$5,000 in credits or 3+ months free

**Documentation:**
- Log all retention activities in CRM under "Churn Risk" tag
- Record outcome: Won (retained), Lost (cancelled), Pending
- Schedule 30-day check-in if retained

**Approved Retention Offers (within 2 hours):**

| Situation | Offer | Approval |
|-----------|-------|----------|
| Pricing objection | 1 month free + 12-month price lock | Account Manager |
| Product issue | Free month + executive meeting + roadmap preview | VP Sales |
| Competitor comparison | 2 months free + dedicated migration support | VP Sales |
| Financial hardship | Payment plan + temporary downgrade with free upgrade in 90 days | VP Sales + Finance |

---

### 3.4 GDPR Data Subject Requests

**Trigger Events:**
- Receipt of any request citing GDPR rights (erasure, portability, access, rectification, objection)
- Receipt of correspondence from a Data Protection Authority (DPA) or regulator
- Customer or end user invokes "right to be forgotten" or other GDPR rights

**Escalation Path:**
1. **T+0:** Acknowledge receipt to the requesting party with an automated or templated response (see template below)
2. **T+0:** Log request in the GDPR request tracker (link in internal wiki)
3. **T+24 hours:** Forward complete request details to DPO at dpo@company.com
4. **T+24 hours:** DPO assigns ownership and begins identity verification process
5. **T+30 days:** Maximum response/fulfillment time per GDPR Articles 12–22

**Auto-Acknowledge Template (send immediately upon receipt):**
```
Subject: Re: Your Data Request — Reference [AUTO-GENERATED-ID]

Dear [Name],

Thank you for contacting CRM Intelligence Platform regarding your data rights request.

We have received your request and it has been assigned Reference ID: [REF-ID].

In accordance with GDPR requirements, we will respond to your request within 
30 calendar days. If we require additional time due to the complexity of your 
request, we will notify you within the initial 30-day period.

If you have questions in the meantime, please contact our Data Protection Officer 
at dpo@company.com, referencing the above ID.

Sincerely,
Privacy Team
CRM Intelligence Platform
dpo@company.com
```

**DPA/Regulator Correspondence:**
- Immediately forward to DPO AND Legal Counsel
- Do NOT respond to regulators without DPO/Legal approval
- Response timeline: Per regulator's specified deadline (typically 30 days)

---

### 3.5 Press / Media Inquiries

**Trigger Events:**
- Journalist or media outlet contacts any Company employee (phone, email, LinkedIn, social media)
- Request for comment on Company, product, a customer, or an incident
- Request for interview (CEO, product team, etc.)
- Inquiry about a reported incident or negative news story

**⚠️ CRITICAL RULE:** Do not comment, confirm, or deny ANYTHING to press/media without explicit PR team approval. Even "no comment" should come from PR.

**Escalation Path:**
1. **T+0:** Do not respond to the inquiry in any way
2. **T+0:** Forward the inquiry (call summary or email forward) to **PR team** at pr@company.com immediately
3. **T+0:** Notify CEO/Communications lead via Slack #media-inquiries channel
4. **PR team response time:** PR team will prepare approved statement or talking points within 4 business hours
5. **If after hours:** CEO/COO on-call to authorize holding statement if needed

**Employees Must:**
- Say: "I'm not the right person to comment on this — I'll connect you with our communications team."
- Provide PR contact: pr@company.com
- Immediately notify PR team of the inquiry

**Employees Must NOT:**
- Share any customer information, financial data, or internal details
- Comment on ongoing incidents, outages, or legal matters
- Confirm or deny funding, acquisitions, partnerships, or strategic plans
- Post on personal social media about Company news without PR approval

---

### 3.6 P0 Infrastructure Incidents

**Trigger Events:**
- Platform-wide outage (per SLA Policy definition of P0)
- API unavailability >5 minutes
- Complete authentication failure
- Data loss event (any scale)
- Security breach with operational impact

**Escalation Path (per SLA Policy):**
1. **T+0:** On-call engineer paged automatically by monitoring system
2. **T+0 to T+15 min:** On-call engineer acknowledges and begins triage
3. **T+15 min (no ack):** Engineering Lead automatically paged
4. **T+30 min (unresolved):** CTO notified via phone/Slack
5. **T+1 hour (unresolved):** VP Engineering + entire on-call engineering team mobilized
6. **T+1 hour (Enterprise customer affected):** Account Manager AND Customer Success VP notified; customer notified per SLA
7. **T+1 hour (Enterprise customer affected):** CEO notified by CTO
8. **T+2 hours (P0 target resolution):** If not resolved, escalate to all-hands engineering response

**Communication Requirements:**
- Status page updated within 10 minutes of P0 detection
- Enterprise customers personally notified within 15 minutes (phone, then email)
- Internal Slack #incidents channel: update every 15 minutes during active P0
- Post-mortem/RCA delivered within 24 hours of resolution (per SLA Policy Section 4)

**Severity Override Authority:**
- Any engineer can declare P0; no approval needed to escalate
- To de-escalate from P0 to P1: requires Engineering Lead + CTO agreement

---

### 3.7 Reputation Crisis (3+ Negative Reviews Threatened or Posted)

**Trigger Events:**
- Single customer or coordinated group threatens to post 3+ negative reviews
- Discovery of 3+ negative reviews posted simultaneously on major platforms (G2, Capterra, Trustpilot, Reddit, LinkedIn)
- Social media thread gaining traction with negative sentiment about Company
- Negative press coverage from credible publication

**Escalation Path:**
1. **T+0:** Ticket or detection logged; Support/CS team member notifies Customer Success VP immediately
2. **T+0 to T+1 hour:** Customer Success VP and PR team convene (Slack huddle/call)
3. **T+2 hours:** Joint response strategy developed by CS VP + PR team
4. **If reviews already posted:** PR team leads response; do not post defensive company replies without PR approval
5. **If customers are threatening:** CS team leads outreach with approved offers (see below)

**Approved Offers for Reputation Risk Situations:**
- 1-month service credit (account credit, not cash)
- Priority Support tier upgrade (temporary, 90 days)
- Personal call from Customer Success VP within 4 business hours
- Escalated product feedback session with Product team (positions customer as influencer, not just complainant)

**DO NOT:**
- Ask customers to remove reviews as a condition of receiving credit
- Respond defensively or confrontationally to negative reviews
- Make promises about product changes you cannot commit to
- Offer cash refunds not covered by policy without VP Finance approval

**Review Response Guidelines (for public review platforms):**
- Responses must be drafted by CS team and approved by PR before posting
- Response tone: empathetic, constructive, professional
- Never name-call or invalidate the reviewer's experience
- Provide path to resolution: "We'd like to connect — please contact [email]"

---

### 3.8 Investor / Financial Inquiries

**Trigger Events:**
- Inquiry from known or unknown investor about Company financials, fundraising, valuation, or strategy
- Request for financial projections, investor deck, or cap table information
- Questions about merger, acquisition, or IPO plans
- Press inquiries about investment rounds

**⚠️ CRITICAL RULE:** Do not confirm or deny any fundraising status, financial metrics, valuation, or strategic plans without explicit CEO/CFO authorization.

**Escalation Path:**
1. **T+0:** Do not respond to the inquiry
2. **T+0 to T+4 hours:** Forward inquiry to CEO (ceo@company.com) and CFO (cfo@company.com)
3. **CEO/CFO** will determine appropriate response and spokesperson
4. **Known investor (existing shareholder):** Investor Relations handled by CFO; CEO engaged for strategic matters
5. **Unknown/prospective investor:** CFO screens and routes appropriately
6. **If part of active fundraise:** All communications routed through legal counsel and investment banker (if applicable)

**Standard Holding Response (if you must respond before CEO/CFO guidance):**
```
"Thank you for reaching out. For investor-related inquiries, 
please contact our executive team directly at investors@company.com. 
We'll make sure the right person follows up with you promptly."
```

---

## 4. Escalation Contact Directory

| Role | Name | Email | Emergency |
|------|------|-------|-----------|
| Legal Counsel | [Legal Counsel] | legal@company.com | See internal wiki |
| Data Protection Officer (DPO) | [DPO Name] | dpo@company.com | See internal wiki |
| SecOps Team | Security Operations | security@company.com | #security-incidents Slack |
| Chief Technology Officer (CTO) | [CTO Name] | cto@company.com | See internal wiki |
| Chief Executive Officer (CEO) | [CEO Name] | ceo@company.com | See internal wiki |
| Chief Financial Officer (CFO) | [CFO Name] | cfo@company.com | See internal wiki |
| VP Sales | [VP Sales Name] | vpsales@company.com | See internal wiki |
| VP Customer Success | [CS VP Name] | customersuccess@company.com | See internal wiki |
| VP Engineering | [VP Eng Name] | vpengineering@company.com | See internal wiki |
| PR Team | Communications | pr@company.com | See internal wiki |
| Investor Relations | IR Team | investors@company.com | Via CEO/CFO |

*Emergency contact numbers are stored in the Company secure vault (1Password) and are accessible to all managers and above.*

---

## 5. General Escalation Principles

1. **When in doubt, escalate.** It is always better to over-escalate than to under-escalate a sensitive situation.
2. **Preserve everything.** In all high-risk situations, preserve all communications and evidence before taking any action.
3. **Do not go it alone.** No individual contributor should handle a high-risk escalation without manager involvement.
4. **Time targets are maximums, not goals.** Aim to escalate faster than the defined window whenever possible.
5. **Document everything.** All escalations must be logged in the incident tracker with timestamps, actions taken, and outcomes.
6. **Follow up.** Every escalation should have a defined owner responsible for resolution and follow-up communication.
7. **Learn from incidents.** All P0 and legal/security incidents require a post-mortem/lessons-learned document within 2 weeks.

---

## 6. Matrix Review and Updates

This escalation matrix is reviewed quarterly by the following stakeholders:
- VP Customer Success
- VP Engineering
- Legal Counsel
- DPO
- VP Sales
- VP Operations

**Next Review Date:** September 1, 2024  
**Document Location:** Internal Wiki → Legal & Compliance → Escalation Matrix  
**Most Recent Version:** https://company.com/internal/escalation-matrix
