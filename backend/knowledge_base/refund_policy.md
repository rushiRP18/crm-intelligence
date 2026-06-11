# Refund Policy & Customer Retention Playbook — CRM Intelligence Platform

**Effective Date:** January 1, 2024  
**Last Updated:** June 1, 2024  
**Document Owner:** Finance, Customer Success & Revenue Operations  
**Version:** 1.8

---

## 1. Refund Policy

### 1.1 General Refund Policy

CRM Intelligence Platform operates on a **no-refund policy after 14 days from the payment date**. All subscription fees are charged in advance and are non-refundable except as explicitly described in this policy.

**Policy Summary:**
- Refund requests must be submitted **within 14 calendar days** of the original payment date
- Requests submitted after 14 days from payment are not eligible for refund
- Partial refunds (pro-rata) are not offered for unused days within a billing period, except on annual plans during the 14-day window
- Refunds, when approved, are processed within 5–10 business days to the original payment method

### 1.2 Eligible Refund Scenarios

The following scenarios may qualify for a refund within the 14-day window:

| Scenario | Eligibility | Notes |
|----------|-------------|-------|
| Customer requests refund within 14 days of payment | Eligible | Full refund of that payment |
| Annual plan purchased, refund within 14 days | Eligible | Full annual payment refunded |
| Duplicate payment (billing error) | Eligible (any time) | Full duplicate charge refunded |
| Service not delivered as described at purchase | Eligible (within 14 days) | Review required |
| Billing error by Company | Eligible (any time) | Full correction applied |

### 1.3 Non-Eligible Refund Scenarios

The following are explicitly **not eligible** for refunds:

- Requests submitted more than 14 days after payment date
- Dissatisfaction with AI-generated content or recommendations (subjective)
- Failure to use the service during the subscription period
- Cancelation of a monthly plan after the current billing cycle has started
- Downgrade from a higher plan (unused higher-tier days are not refunded)
- Non-profit or academic discounts previously applied (the discounted price is final)

### 1.4 How to Submit a Refund Request

1. **Email:** billing@company.com
2. **Subject Line:** "Refund Request — [Account Name] — [Payment Date]"
3. **Required Information:**
   - Account email address
   - Transaction/invoice number
   - Payment date
   - Reason for refund request
   - Amount paid
4. **Deadline:** Request must be received within **14 calendar days** of the payment date (not postmarked — received)
5. **Response Time:** Refund team will respond within 2 business days with a decision

### 1.5 Refund Processing

- Approved refunds are processed within **5–10 business days**
- Refunds are returned to the **original payment method only**
- For annual plans paid by wire transfer or ACH, refunds are processed via the same method
- Company is not responsible for delays caused by the customer's financial institution

---

## 2. SLA Credits (Service Credit Policy)

SLA credits are **not cash refunds**. They are account credits applied to future invoices.

### 2.1 SLA Credit Mechanics

- Credits are calculated per the SLA Policy (see sla_policy.md)
- Credits appear as a line item on the next billing invoice
- Credits are non-transferable between accounts
- Credits expire 12 months from the date of issue
- SLA credits do not stack with promotional credits; the higher credit applies
- Maximum SLA credit per month: 30% of monthly subscription fee

### 2.2 SLA Credit vs. Refund

| Type | Form | Cash? | Expiry |
|------|------|-------|--------|
| SLA Credit (downtime) | Account credit on next invoice | No | 12 months |
| Refund (within 14 days) | Return to original payment method | Yes | N/A |
| Retention Credit (see Section 3) | Account credit | No | 6 months |

---

## 3. Customer Retention & Churn Management Playbook

This section defines the internal response procedures for customers showing churn signals or threatening to cancel. All customer-facing retention offers must be approved by the Account Manager or Customer Success Manager before delivery.

### 3.1 Churn Signal Detection

The following signals trigger a retention workflow in the CRM:

- Customer submits cancellation request
- Customer threatens cancellation in support ticket or email
- Customer NPS score drops to ≤5
- Customer reduces seat count by >50%
- Customer has not logged in for 30+ days (Standard/Pro) or 14+ days (Enterprise)
- Customer mentions a competitor by name in a support ticket
- Customer explicitly requests a refund after 14 days (signal of dissatisfaction)

### 3.2 VIP Customer Churn Protocol

**Definition of VIP Customer:** Any customer meeting one or more of the following criteria:
- Enterprise plan subscriber
- Monthly spend >$500 (Standard/Pro with add-ons)
- Customer tenure >24 months
- Strategic account (partner, investor, high-profile brand)

**VIP Churn Response Protocol:**

**Step 1 — Immediate Escalation (within 2 hours of churn signal detection):**
- Alert assigned Account Manager via Slack/email
- Notify VP of Sales via CRM alert
- Do NOT send generic automated retention emails to VIP customers

**Step 2 — Account Manager Action (within 2 hours):**
- Review account health (usage, tickets, NPS, recent interactions)
- Schedule a personal call with the customer's primary stakeholder
- Prepare personalized retention package (see offers below)

**Step 3 — Retention Package Options for VIP Customers:**

| Customer Situation | Approved Offer | Approval Required |
|-------------------|---------------|------------------|
| Pricing objection | 1 free month credit + lock in current pricing for 12 months | Account Manager |
| Competitor comparison | Product roadmap preview + dedicated onboarding refresh | Account Manager |
| Product dissatisfaction | 1 free month + Executive Sponsor meeting | VP Sales |
| Financial hardship | Payment plan or temporary downgrade + free upgrade back in 90 days | VP Sales + Finance |
| General frustration | 1 free month credit + priority support tier upgrade (temporary 90 days) | Account Manager |

**Step 4 — Post-Retention Follow-up:**
- Document retention outcome in CRM (won/lost/pending)
- Schedule 30-day check-in call
- Flag account for quarterly health review

### 3.3 Standard Customer Churn Protocol

For non-VIP customers (Standard and Pro plans below the VIP threshold):

1. Automated retention email sent within 24 hours of cancellation request
2. If no response in 48 hours: support agent follow-up email
3. If customer engages: offer standard retention package
4. If no engagement after 5 days: process cancellation per customer request

**Standard Retention Package:**
- 15% discount on current plan for the next 3 months (no free months for standard churn)
- Link to updated product documentation and training resources
- Offer to schedule a 30-minute product optimization call

### 3.4 Negative Review / Reputation Risk Protocol

**Trigger:** Customer explicitly threatens to post negative reviews on G2, Capterra, Trustpilot, Reddit, LinkedIn, or other public platforms.

**Escalation:** Immediately notify Customer Success Manager and VP Customer Success.

**Response Protocol:**

1. **Do NOT dismiss or challenge the threat** — acknowledge the customer's frustration empathetically
2. **Do NOT offer refunds not covered by policy** without VP approval
3. **Approved Immediate Offers:**
   - **1-month service credit** applied to next invoice (no cash)
   - **Priority Support tier upgrade** (temporary, 90 days): move customer to next tier's support SLA
   - Personal call from Customer Success VP or Account Manager within 4 business hours
4. **Escalation path:** Customer Success VP → VP Sales → CEO (if Enterprise and strategic account)
5. **Documentation:** Log all communications in CRM with "Reputation Risk" tag
6. **Follow-up:** 14-day and 30-day check-in calls post-resolution
7. **No promises about review removal** — never ask customers to remove reviews as part of compensation

**Important:** If negative review has already been posted publicly, escalate to PR team per Escalation Matrix (escalation_matrix.md).

### 3.5 Annual Churn at Renewal

For annual plan customers who indicate they will not renew:

- Trigger renewal retention workflow 60 days before renewal date
- Account Manager conducts annual business review (QBR) if not already scheduled
- Approved early-renewal offer: 5% additional discount if renewed 30+ days early
- Last-resort offer (VP approval): 2 additional months free on next annual term

---

## 4. Account Cancellation Process

### 4.1 How to Cancel

Customers may cancel their subscription through any of the following methods:
- **Self-serve:** Account Settings → Subscription → Cancel Plan (monthly plans only)
- **Email:** billing@company.com with subject "Account Cancellation — [Account Name]"
- **Support ticket:** support.company.com → "Account Management" category

### 4.2 Cancellation Timing

| Plan Type | When Cancellation Takes Effect |
|-----------|-------------------------------|
| Monthly plan | End of current billing cycle |
| Annual plan | End of current annual term |
| Enterprise | Per negotiated contract terms |

- Access to paid features is maintained until the cancellation effective date
- No charges are incurred after the cancellation effective date

### 4.3 Post-Cancellation Data Retention

**Data Retention Period: 30 days post-cancellation**

Upon account cancellation:

1. Account is placed in "Cancelled" status immediately
2. Data (contacts, deals, conversations, reports) is retained for **30 days** from the cancellation effective date
3. During the 30-day retention period, customers may reactivate their account and all data will be restored
4. After 30 days: **all customer data is permanently and irreversibly deleted** from Company systems
5. Backups containing customer data are purged within 60 days of cancellation

**Data Export:** Customers are strongly encouraged to export their data before cancellation. Data export tools are available in Account Settings → Data Export. Exports can be requested in CSV, JSON, or PDF format.

### 4.4 GDPR Right to Erasure (Article 17)

Customers and their data subjects may request erasure of personal data ("right to be forgotten") at any time, independent of account cancellation.

**Process:**
1. Submit a verified erasure request to: dpo@company.com
2. Subject line: "GDPR Erasure Request — [Account Name or Data Subject Name]"
3. Identity verification required (government-issued ID or signed request from authorized account holder)
4. **Processing Time:** Data deletion completed within **30 days** of receiving a verified request
5. **Confirmation:** Written confirmation of deletion sent upon completion
6. **Exceptions:** Company may retain data required by law (e.g., financial records, fraud prevention) with notification to requester

**Note:** GDPR erasure requests apply to personal data only. Anonymized or aggregated analytical data may be retained.

---

## 5. Special Circumstances and Executive Escalation

### 5.1 Refund Exception Process

For cases outside the standard 14-day window where a refund may be warranted (e.g., extraordinary circumstances, billing system errors, legal mandate):

- Customer must email billing@company.com with a detailed explanation
- Billing team escalates to Finance Manager for review
- Finance Manager makes final decision within 5 business days
- All exception refunds require Finance Manager approval (>$500) or VP Finance approval (>$2,000)

### 5.2 Chargebacks

If a customer initiates a credit card chargeback without first contacting Company:
1. Company will respond to the chargeback with full documentation
2. Account is temporarily suspended pending chargeback resolution
3. If chargeback is found in Company's favor, account reinstatement requires resolution of dispute
4. Repeated chargebacks may result in permanent account termination

---

## 6. Contact Information

| Purpose | Contact | Response Time |
|---------|---------|--------------|
| Refund Requests | billing@company.com | 2 business days |
| Account Cancellation | billing@company.com | 1 business day |
| GDPR Erasure | dpo@company.com | Within 30 days |
| Data Export Assistance | support@company.com | 2 business days |
| Retention / Account Health | Your Account Manager | Per VIP protocol |
| Escalation (VIP) | customersuccess@company.com | 2 hours |
