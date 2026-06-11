# Compliance FAQ — CRM Intelligence Platform

**Effective Date:** January 1, 2024  
**Last Updated:** June 1, 2024  
**Document Owner:** Legal, Security & Data Privacy  
**Data Protection Officer (DPO):** dpo@company.com  
**Version:** 3.1

---

## 1. Overview

This document addresses frequently asked questions about CRM Intelligence Platform's compliance posture, certifications, data handling practices, and regulatory commitments. For detailed legal agreements, contact legal@company.com.

---

## 2. HIPAA Compliance

### Q: Is CRM Intelligence Platform HIPAA compliant?

**A:** Yes, for Enterprise plan customers. CRM Intelligence Platform supports HIPAA-compliant deployments with appropriate contractual protections in place.

**Requirements for HIPAA compliance:**
1. Customer must be on the **Enterprise plan**
2. A signed **Business Associate Agreement (BAA)** must be in place before handling any Protected Health Information (PHI)
3. Customer must configure their workspace with HIPAA-appropriate settings (provided during Enterprise onboarding)

### Q: What is a Business Associate Agreement (BAA)?

**A:** A BAA is a legally required contract under HIPAA that governs how a Business Associate (Company) handles PHI on behalf of a Covered Entity (the customer). It outlines permitted uses, required safeguards, and breach notification obligations.

**To request a BAA:**
- Contact your Account Executive or email legal@company.com
- Subject: "BAA Request — [Company Name]"
- BAA is available exclusively for Enterprise plan customers
- Allow 5–7 business days for legal review and execution

### Q: Where is data stored for HIPAA-compliant deployments?

**A:** All data for HIPAA-enabled Enterprise accounts is stored exclusively in:
- **Cloud Provider:** Amazon Web Services (AWS)
- **Region:** `us-east-1` (US East - Northern Virginia) — a HIPAA-eligible AWS region
- **No cross-region data replication** to non-HIPAA-eligible regions
- Dedicated infrastructure (no multi-tenant storage) available for qualifying Enterprise accounts

### Q: How is data encrypted for HIPAA compliance?

**A:** CRM Intelligence Platform implements comprehensive encryption:

| Data State | Encryption Standard |
|-----------|-------------------|
| **Data at rest** | AES-256 (Advanced Encryption Standard, 256-bit keys) |
| **Data in transit** | TLS 1.3 (Transport Layer Security 1.3) |
| **Database backups** | AES-256 with separate key management |
| **API keys and secrets** | PBKDF2 with SHA-256, 100,000 iterations |

- Encryption keys managed via AWS Key Management Service (KMS)
- Customer-managed encryption keys (CMEK) available for qualifying Enterprise accounts
- Key rotation performed annually or on demand

### Q: Does HIPAA compliance apply to all plans?

**A:** No. HIPAA-compliant deployments and BAA execution are **only available on the Enterprise plan**. Standard and Pro plan customers must not use the platform for storing or processing PHI without an active BAA, as this would violate HIPAA regulations.

---

## 3. GDPR Compliance

### Q: Is CRM Intelligence Platform GDPR compliant?

**A:** Yes. CRM Intelligence Platform is compliant with the General Data Protection Regulation (EU) 2016/679 (GDPR). We act as a Data Processor for your customer data, and you act as the Data Controller.

### Q: What is a Data Processing Agreement (DPA)?

**A:** A DPA is a legally binding contract required under GDPR Article 28 that governs how CRM Intelligence Platform (as Data Processor) processes personal data on behalf of customers (as Data Controllers).

**To request a DPA:**
- Email: dpo@company.com
- Subject: "DPA Request — [Company Name]"
- DPAs are available to **all paid plan customers** (Standard, Pro, Enterprise)
- Standard DPA available for download from: https://company.com/legal/dpa
- Custom DPA addendums: available for Enterprise customers through legal@company.com

### Q: What are our obligations under GDPR Article 20 (Data Portability)?

**A:** Data subjects have the right to receive their personal data in a structured, commonly used, machine-readable format and to transmit it to another controller.

**Our Process:**
- Submit data portability requests to: dpo@company.com
- **Response Window: 30 calendar days** from receipt of verified request
- Data provided in: JSON, CSV, or structured export format
- For complex requests (large data volumes), we may extend by an additional 60 days with notification within the initial 30-day window
- Identity verification is required before fulfilling portability requests

### Q: What about the GDPR Right to Erasure (Article 17)?

**A:** Data subjects have the right to request deletion of their personal data ("right to be forgotten").

**Our Process:**
1. Submit erasure request to: dpo@company.com
2. Subject: "GDPR Erasure Request — [Data Subject Name]"
3. Identity or authorization verification required
4. **Processing Time:** Deletion completed within **30 calendar days** of receiving a verified request
5. Written confirmation of deletion provided upon completion
6. **Exceptions:** We may retain data required by legal obligation (e.g., accounting records, fraud prevention logs) — customer notified of any such retention

### Q: Who is the Data Protection Officer (DPO)?

**A:**
- **DPO Contact:** dpo@company.com
- **Postal Address:** Privacy Office, CRM Intelligence Platform, [Company Address]
- The DPO is available for all data subject inquiries, GDPR requests, and regulator communications
- EU Representative: [EU Representative Name], [EU Address] (GDPR Article 27 requirement)

### Q: Where is EU customer data stored?

**A:**
- **Default:** US data centers (AWS us-east-1)
- **EU Data Residency:** Available on Enterprise plan — data stored in AWS `eu-west-1` (EU West - Ireland)
- EU data residency must be configured at account setup; migration between regions available for Enterprise customers
- Sub-processors list: available at https://company.com/legal/sub-processors

### Q: What are the Standard Contractual Clauses (SCCs) for international transfers?

**A:** For EU customers whose data is processed in the US, we use the EU Standard Contractual Clauses (SCCs) as the legal mechanism for international data transfer under GDPR Chapter V. SCCs are incorporated into our DPA. Contact dpo@company.com for copies.

### Q: What GDPR rights can data subjects exercise?

| GDPR Right | Article | How to Submit | Response Time |
|-----------|---------|--------------|--------------|
| Right of Access | Art. 15 | dpo@company.com | 30 days |
| Right to Rectification | Art. 16 | dpo@company.com | 30 days |
| Right to Erasure | Art. 17 | dpo@company.com | 30 days |
| Right to Restriction | Art. 18 | dpo@company.com | 30 days |
| Right to Portability | Art. 20 | dpo@company.com | 30 days |
| Right to Object | Art. 21 | dpo@company.com | 30 days |

---

## 4. SOC 2 Compliance

### Q: Is CRM Intelligence Platform SOC 2 certified?

**A:** Yes. CRM Intelligence Platform has achieved **SOC 2 Type II** certification.

**Details:**
- **Certification Level:** SOC 2 Type II (covers a period of operational effectiveness, not just point-in-time design)
- **Trust Service Criteria:** Security, Availability, Confidentiality
- **Auditor:** Independent third-party CPA firm (AICPA-accredited)
- **Audit Period:** Annual; most recent report covers the 12-month period ending September 30, 2023

### Q: How do I access the SOC 2 report?

**A:**
- SOC 2 Type II reports are available **under Non-Disclosure Agreement (NDA)**
- To request access:
  1. Email security@company.com with subject: "SOC 2 Report Request — [Company Name]"
  2. Execute our standard NDA (or provide your preferred NDA template for review)
  3. Report will be shared via secure document portal within 3 business days of NDA execution
- SOC 2 bridge letters are available for periods between audit completions

### Q: What controls does SOC 2 cover?

**A:** Our SOC 2 report covers the following control domains:
- Logical and physical access controls
- Change management
- Risk assessment
- Vendor management
- Monitoring and incident response
- Data encryption and key management
- Business continuity and disaster recovery

---

## 5. ISO 27001

### Q: Is CRM Intelligence Platform ISO 27001 certified?

**A:** ISO 27001 certification is **in progress**. Target completion: **Q2 2024**.

**Current Status:**
- Gap assessment: Completed (Q1 2023)
- Control implementation: Completed (Q3 2023)
- Internal audit: Completed (Q4 2023)
- Stage 1 audit: Completed (Q1 2024)
- Stage 2 certification audit: Scheduled Q2 2024
- Certification body: [Accredited ISO 27001 Certification Body]

Customers who require ISO 27001 certification prior to Q2 2024 completion should contact sales to discuss options, including reviewing our SOC 2 Type II report as an interim alternative.

---

## 6. Data Residency

### Q: Where is my data stored by default?

**A:** By default, all customer data is stored in the **United States** on AWS infrastructure.

| Data Type | Default Location | EU Option |
|-----------|-----------------|-----------|
| Contact and deal data | AWS us-east-1 | AWS eu-west-1 (Enterprise) |
| Analytics and reports | AWS us-east-1 | AWS eu-west-1 (Enterprise) |
| AI/ML model outputs | AWS us-east-1 | AWS eu-west-1 (Enterprise) |
| Audit logs | AWS us-east-1 | AWS eu-west-1 (Enterprise) |
| Backups | AWS us-east-1 + us-west-2 (DR) | AWS eu-west-1 + eu-central-1 (DR) |

### Q: Can I choose EU data residency?

**A:** Yes. EU data residency is available on the **Enterprise plan**.

- Data is stored exclusively in AWS `eu-west-1` (Ireland)
- Disaster recovery backup in AWS `eu-central-1` (Frankfurt)
- No data leaves the EU region
- Must be configured at account inception; retroactive migration requires coordinated migration project (contact CSM)
- EU data residency included in Enterprise pricing; no additional surcharge

### Q: What regions are HIPAA-eligible?

**A:** Currently, only `us-east-1` is configured as a HIPAA-eligible region for our infrastructure. EU data residency is not currently available for HIPAA-compliant deployments.

---

## 7. Penetration Testing

### Q: Does CRM Intelligence Platform conduct penetration testing?

**A:** Yes. We conduct **annual third-party penetration tests** performed by an independent security firm.

**Pentest Details:**
- **Frequency:** Annual (minimum)
- **Scope:** External network, web application (API), internal network, social engineering (spot checks)
- **Methodology:** OWASP Top 10, PTES (Penetration Testing Execution Standard), OWASP API Security Top 10
- **Last Completed:** Q3 2023
- **Next Scheduled:** Q3 2024
- **Remediation:** All Critical and High findings remediated within 30 days of report; Medium within 90 days

### Q: Can customers perform their own penetration tests?

**A:** Yes, with prior written authorization:
1. Submit pentest request to security@company.com at least **14 business days** in advance
2. Provide: scope, methodology, testing window (dates/times), testing tools, testing IP ranges
3. Company will review and provide written authorization if approved
4. Scope limitations apply: no denial-of-service testing, no cross-tenant testing, no social engineering of Company employees
5. Results must be shared with Company security team within 30 days of test completion

### Q: How are security vulnerabilities reported?

**A:**
- **Responsible Disclosure Program:** https://company.com/security/responsible-disclosure
- **Email:** security@company.com (PGP key available on request)
- **Bug Bounty:** Private program via HackerOne (invitation-only for qualified researchers)
- Response to disclosures: within 2 business days

---

## 8. Additional Compliance & Security Information

### Q: What is your data breach notification process?

**A:**
- Security incidents are managed by the SecOps team (security@company.com)
- Affected customers are notified within **72 hours** of confirmed breach (meeting GDPR Article 33 requirement for supervisory authority notification)
- Individual data subjects notified per GDPR Article 34 requirements when risk is high
- Enterprise customers receive direct notification from their CSM + written incident report
- Post-incident forensic report provided within 30 days

### Q: What sub-processors do you use?

**A:** A complete and current list of sub-processors is maintained at: https://company.com/legal/sub-processors  
Customers are notified of sub-processor changes via email with 30 days' notice. Enterprise customers may object to new sub-processor additions per the terms of their DPA.

### Q: What is your data retention policy for operational data?

| Data Type | Retention Period |
|-----------|----------------|
| Customer account data | Duration of subscription + 30 days |
| API access logs | 90 days |
| Security audit logs | 2 years |
| Financial/billing records | 7 years (US tax law requirement) |
| Support ticket records | 3 years |
| AI model interaction logs | 90 days (anonymized after 30 days) |

### Q: Do you support Single Sign-On (SSO)?

**A:** Yes. SSO/SAML 2.0 is available on the Enterprise plan.

- Supported identity providers: Okta, Azure AD, Google Workspace, OneLogin, Ping Identity, and any SAML 2.0-compliant IdP
- SCIM 2.0 provisioning/deprovisioning supported
- Contact your Account Manager to configure SSO

---

## 9. Quick Reference — Compliance Contacts

| Topic | Contact | Response Time |
|-------|---------|--------------|
| GDPR Requests (all types) | dpo@company.com | 30 days max |
| DPA Request | dpo@company.com | 5 business days |
| BAA Request (HIPAA) | legal@company.com | 5–7 business days |
| SOC 2 Report Request | security@company.com | 3 business days (post-NDA) |
| Security Vulnerabilities | security@company.com | 2 business days |
| Pentest Authorization | security@company.com | 14 business days |
| Data Breach Notification | Via status page + email | 72 hours |
| Legal / Privacy Inquiries | legal@company.com | 5 business days |
| General Compliance Questions | compliance@company.com | 3 business days |
