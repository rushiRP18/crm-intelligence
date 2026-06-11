# API Documentation — CRM Intelligence Platform

**Version:** v2.0  
**Base URL:** `https://api.company.com/v2`  
**Last Updated:** June 1, 2024  
**Document Owner:** Engineering Team

---

## 1. Overview

The CRM Intelligence Platform API provides RESTful access to all platform functionality including contact management, deal pipelines, AI analytics, and automation workflows. The API uses standard HTTP methods, returns JSON responses, and uses Bearer token authentication.

> **⚠️ IMPORTANT: v1 API Deprecation Notice**  
> The v1 API (`https://api.company.com/v1`) has been **sunset as of December 31, 2023**.  
> All clients **must** migrate to v2 immediately. v1 endpoints return HTTP 410 Gone.  
> See Section 3 for migration guide.

---

## 2. Authentication

### 2.1 Authentication Method

All API requests to v2 must include a Bearer token in the `Authorization` header.

**v2 Authentication (Current — Required):**
```http
Authorization: Bearer YOUR_API_KEY_HERE
X-Workspace-ID: your-workspace-id
```

**v1 Authentication (Deprecated — No Longer Accepted):**
```http
X-API-Key: YOUR_API_KEY_HERE   ← THIS FORMAT IS REJECTED IN v2
```

> **Breaking Change:** The `X-API-Key` header format used in v1 is NOT accepted in v2.  
> All requests must use `Authorization: Bearer <token>` format.

### 2.2 Obtaining API Keys

1. Log in to the dashboard at https://app.company.com
2. Navigate to: Settings → API Keys → Generate New Key
3. Select the appropriate scope(s) for your key
4. Store the key securely — it will only be shown once
5. Rotate keys via the same interface; old keys are invalidated immediately upon rotation

### 2.3 API Key Scopes

| Scope | Permission |
|-------|-----------|
| `read:contacts` | Read contact records |
| `write:contacts` | Create and update contacts |
| `read:deals` | Read deal pipeline data |
| `write:deals` | Create and update deals |
| `read:analytics` | Access analytics and reports |
| `admin` | Full access (all scopes) |
| `webhooks` | Manage webhook endpoints |

### 2.4 Required Headers for All Requests

```http
Authorization: Bearer <your-api-key>
Content-Type: application/json
X-Workspace-ID: <your-workspace-id>
Accept: application/json
```

The `X-Workspace-ID` header is **required** in v2 for all requests. Requests missing this header return HTTP 400 Bad Request.

---

## 3. v1 API Deprecation and v2 Migration Guide

### 3.1 v1 Sunset Status

| Date | Event |
|------|-------|
| October 1, 2023 | v1 deprecation announced; migration guide published |
| November 30, 2023 | v1 endpoints began returning deprecation warnings in response headers |
| December 31, 2023 | **v1 API SUNSET — All v1 endpoints now return HTTP 410 Gone** |
| January 1, 2024 | v2 is the only supported API version |

**All v1 requests now return:**
```json
{
  "error_code": "API_VERSION_DEPRECATED",
  "message": "The v1 API was sunset on December 31, 2023. Please migrate to v2.",
  "details": {
    "migration_guide": "https://docs.company.com/api/v2/migration",
    "v2_base_url": "https://api.company.com/v2"
  }
}
```

### 3.2 v2 Breaking Changes from v1

The following breaking changes were introduced in v2. All integrations must be updated to handle these changes.

#### Change 1: Authentication Header Format

```diff
- X-API-Key: YOUR_API_KEY_HERE
+ Authorization: Bearer YOUR_API_KEY_HERE
```

#### Change 2: Required X-Workspace-ID Header

```diff
+ X-Workspace-ID: your-workspace-id    ← NEW REQUIRED HEADER
  Authorization: Bearer YOUR_API_KEY_HERE
```

#### Change 3: Paginated Responses

All list endpoints in v2 return paginated responses. v1 returned flat arrays.

**v1 Response (old — no longer supported):**
```json
[
  {"id": "1", "name": "Alice"},
  {"id": "2", "name": "Bob"}
]
```

**v2 Response (current — required format):**
```json
{
  "data": [
    {"id": "1", "name": "Alice"},
    {"id": "2", "name": "Bob"}
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 247,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false,
    "next_cursor": "eyJpZCI6IjUxIn0="
  }
}
```

**Pagination Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `per_page` | integer | 50 | Results per page (max: 200) |
| `cursor` | string | — | Cursor for cursor-based pagination |

#### Change 4: Webhook Signature Validation (HMAC-SHA256)

v2 webhooks include a cryptographic signature for security validation. v1 had no signature verification.

**v2 Webhook Request Headers:**
```http
X-Webhook-Signature: sha256=a3f2b1c4d5e6...
X-Webhook-Timestamp: 1703980800
X-Webhook-ID: evt_01HJ...
Content-Type: application/json
```

**Signature Validation Algorithm:**
```python
import hmac
import hashlib

def validate_webhook_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """
    Validate incoming webhook signature.
    
    Args:
        payload_body: Raw request body bytes
        signature_header: Value of X-Webhook-Signature header
        secret: Your webhook signing secret (from dashboard)
    
    Returns:
        True if signature is valid, False otherwise
    """
    # Remove "sha256=" prefix
    expected_prefix = "sha256="
    if not signature_header.startswith(expected_prefix):
        return False
    
    provided_sig = signature_header[len(expected_prefix):]
    
    # Compute HMAC-SHA256
    computed_sig = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(computed_sig, provided_sig)
```

**Important Webhook Security Notes:**
- Always validate the signature before processing webhook payload
- Reject requests with signatures that do not match
- Check `X-Webhook-Timestamp` to prevent replay attacks (reject if >300 seconds old)
- Webhook secrets are rotatable in dashboard → Settings → Webhooks

---

## 4. Rate Limiting

### 4.1 Rate Limits by Plan

| Plan       | Rate Limit           | Burst Allowance |
|------------|---------------------|----------------|
| Free       | 100 requests/minute  | 150 requests (1 minute burst) |
| Standard   | 1,000 requests/minute | 1,500 requests (1 minute burst) |
| Pro        | 5,000 requests/minute | 7,500 requests (1 minute burst) |
| Enterprise | 10,000 requests/minute | Configurable   |

Rate limits are applied per API key, per workspace.

### 4.2 Rate Limit Headers

Every API response includes rate limit information in the response headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1703980860
X-RateLimit-Window: 60
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed per window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when the rate limit window resets |
| `X-RateLimit-Window` | Length of rate limit window in seconds |

### 4.3 Rate Limit Exceeded Response

When the rate limit is exceeded, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 13
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1703980860
```

```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "You have exceeded the rate limit of 1000 requests per minute.",
  "details": {
    "limit": 1000,
    "window_seconds": 60,
    "retry_after_seconds": 13,
    "upgrade_url": "https://app.company.com/settings/billing"
  }
}
```

**Best Practices for Rate Limit Handling:**
- Implement exponential backoff when receiving 429 responses
- Use the `Retry-After` header to determine when to retry
- Cache responses where appropriate to reduce API calls
- Use webhook subscriptions instead of polling for real-time data

---

## 5. Error Response Format

All errors from the v2 API follow a consistent format:

```json
{
  "error_code": "MACHINE_READABLE_CODE",
  "message": "Human-readable description of the error",
  "details": {
    "field": "additional context",
    "documentation": "https://docs.company.com/api/v2/errors#ERROR_CODE"
  }
}
```

### 5.1 Standard Error Codes

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 400 | `BAD_REQUEST` | Malformed request body or missing required fields |
| 400 | `MISSING_WORKSPACE_ID` | `X-Workspace-ID` header is missing |
| 401 | `UNAUTHORIZED` | Missing or invalid `Authorization` header |
| 401 | `INVALID_API_KEY` | API key is invalid, expired, or revoked |
| 403 | `FORBIDDEN` | Valid key but insufficient scope for this operation |
| 404 | `NOT_FOUND` | Resource does not exist or not accessible to this workspace |
| 409 | `CONFLICT` | Resource already exists (e.g., duplicate email) |
| 410 | `API_VERSION_DEPRECATED` | v1 API endpoint requested; v1 was sunset Dec 31, 2023 |
| 422 | `VALIDATION_ERROR` | Request body fails validation; `details` contains field errors |
| 429 | `RATE_LIMIT_EXCEEDED` | Rate limit exceeded; see `Retry-After` header |
| 500 | `INTERNAL_SERVER_ERROR` | Unexpected server error; contact support if persistent |
| 503 | `SERVICE_UNAVAILABLE` | Planned or unplanned service disruption |

### 5.2 Validation Error Example

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request body contains invalid or missing fields.",
  "details": {
    "errors": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "Must be a valid email address"
      },
      {
        "field": "phone",
        "code": "REQUIRED",
        "message": "Phone number is required for this operation"
      }
    ]
  }
}
```

---

## 6. Core API Endpoints

### 6.1 Contacts

#### List Contacts
```http
GET /v2/contacts
Authorization: Bearer <token>
X-Workspace-ID: <workspace-id>

Query Parameters:
  page         (int)    Page number, default: 1
  per_page     (int)    Results per page, default: 50, max: 200
  search       (str)    Full-text search across name, email, company
  tags         (str)    Comma-separated tag filter
  created_after (str)  ISO 8601 datetime filter
```

#### Create Contact
```http
POST /v2/contacts
Authorization: Bearer <token>
X-Workspace-ID: <workspace-id>
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane.doe@example.com",
  "phone": "+1-555-0100",
  "company": "Acme Corp",
  "tags": ["vip", "enterprise"],
  "custom_fields": {}
}
```

### 6.2 Deals / Opportunities

#### List Deals
```http
GET /v2/deals
Authorization: Bearer <token>
X-Workspace-ID: <workspace-id>

Query Parameters:
  stage        (str)    Filter by pipeline stage
  owner_id     (str)    Filter by deal owner
  min_value    (float)  Minimum deal value
  max_value    (float)  Maximum deal value
```

### 6.3 Analytics

#### Get Analytics Summary
```http
GET /v2/analytics/summary
Authorization: Bearer <token>
X-Workspace-ID: <workspace-id>

Query Parameters:
  period       (str)    Options: 7d, 30d, 90d, 1y, custom
  start_date   (str)    ISO 8601 (required if period=custom)
  end_date     (str)    ISO 8601 (required if period=custom)
```

---

## 7. Webhooks

### 7.1 Available Webhook Events

| Event | Trigger |
|-------|---------|
| `contact.created` | New contact added |
| `contact.updated` | Contact record modified |
| `contact.deleted` | Contact deleted |
| `deal.stage_changed` | Deal moved to new pipeline stage |
| `deal.won` | Deal marked as Won |
| `deal.lost` | Deal marked as Lost |
| `subscription.upgraded` | Customer upgrades plan |
| `subscription.cancelled` | Customer cancels |
| `invoice.payment_failed` | Payment fails |

### 7.2 Webhook Payload Structure

```json
{
  "id": "evt_01HJ2K3M4N5P6Q7R8S9T",
  "type": "deal.stage_changed",
  "created_at": "2024-01-15T10:30:00Z",
  "workspace_id": "ws_abc123",
  "data": {
    "deal_id": "deal_xyz789",
    "previous_stage": "Proposal",
    "new_stage": "Negotiation",
    "deal_value": 45000.00,
    "currency": "USD"
  }
}
```

### 7.3 Webhook Retry Policy

- Webhooks are retried on failure (non-2xx response or timeout)
- Retry schedule: immediate → 5 min → 30 min → 2 hours → 8 hours → 24 hours
- Maximum retry attempts: 6 (over ~35 hours)
- After 6 failures, the webhook is marked as failed and an alert is sent to the account admin
- Webhook timeout: 30 seconds per attempt

---

## 8. SDK and Client Libraries

Official client libraries are available for:

| Language | Package | Repository |
|----------|---------|-----------|
| Python | `pip install crm-intel-sdk` | github.com/company/crm-python-sdk |
| Node.js | `npm install @company/crm-sdk` | github.com/company/crm-node-sdk |
| Go | `go get github.com/company/crm-go` | github.com/company/crm-go |
| Ruby | `gem install crm_intel` | github.com/company/crm-ruby |

---

## 9. API Changelog

| Version | Date | Changes |
|---------|------|---------|
| v2.0 | Jan 1, 2024 | GA release; v1 sunset |
| v2.1 | Feb 15, 2024 | Added cursor-based pagination; new AI endpoints |
| v2.2 | Apr 1, 2024 | Webhook HMAC-SHA256 signature added; v2.1 signatures deprecated |
| v2.3 | Jun 1, 2024 | Rate limit burst allowances added; new analytics endpoints |

---

## 10. Support and Resources

| Resource | URL |
|----------|-----|
| API Documentation | https://docs.company.com/api/v2 |
| API Status | https://status.company.com |
| Postman Collection | https://docs.company.com/api/postman |
| Migration Guide (v1→v2) | https://docs.company.com/api/v2/migration |
| Developer Community | https://community.company.com |
| API Support | apisupport@company.com |
