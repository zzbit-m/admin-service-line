# Code Review Remediation Tracker

Single source of truth for code-review fixes. Check off items in the PR that implements them.

**Run tests:** `pytest tests/ -v`

## Required environment variables (fail-fast at boot)

| Variable | Required from | Notes |
|----------|---------------|-------|
| `SECRET_KEY` | PR2 | Non-empty, not `changeme` |
| `LINE_CHANNEL_ID` | PR2 | LINE login |
| `LINE_MESSAGING_CHANNEL_SECRET` | PR2 | LINE webhook signature |
| `N8N_WEBHOOK_URL` | PR4 | n8n event dispatch |

See [`.env.example`](../.env.example) for the full template.

---

## Critical

| Done | Issue | PR | Status |
|------|-------|-----|--------|
| [x] | Request cache IDOR — cache returned before ownership check | PR1 | Done |
| [x] | LINE users store plaintext `LINE_OAUTH` as password | PR2 | Done |

## High

| Done | Issue | PR | Status |
|------|-------|-----|--------|
| [x] | Admin approve does not re-check booking conflicts (race) | PR3 | Done |
| [x] | Hardcoded `localhost:5678` n8n webhook URLs (5 sites) | PR4 | Done |
| [x] | LINE webhook accepts requests when messaging secret unset | PR2 | Done |
| [x] | Deactivated users (`is_active=false`) not blocked | PR2 | Done |

## Medium (backlog — not in this batch)

| Done | Issue | PR | Status |
|------|-------|-----|--------|
| [ ] | Sync Redis blocks async event loop | — | Backlog |
| [ ] | Attachment list owner-only; admins cannot view | — | Backlog |
| [ ] | Upload trusts client `Content-Type` only | — | Backlog |
| [ ] | S3/MinIO URLs unauthenticated | — | Backlog |
| [ ] | Open self-registration | — | Backlog |
| [x] | Missing `start_time < end_time` validation on create | PR3 | Done |
| [ ] | Internal errors leaked to LINE users on postback | — | Backlog |
| [ ] | `Request = None` defaults on several routes | — | Backlog |

## Low (backlog)

| Done | Issue | PR | Status |
|------|-------|-----|--------|
| [x] | Default `SECRET_KEY=changeme` in code | PR2 | Done |
| [ ] | CORS `allow_origins=["*"]` | — | Backlog |
| [ ] | No unique DB constraint on `line_user_id` | — | Backlog |
| [ ] | LINE login does not refresh `full_name` | — | Backlog |
| [x] | Admin webhook POST missing explicit timeout | PR4 | Done |

---

## PR progress

| PR | Branch | Merged |
|----|--------|--------|
| 0 | `main` — docs + rules + `.env.example` | [x] |
| 1 | `fix/security-request-cache-idor` | [x] |
| 2 | `fix/auth-hardening` | [x] |
| 3 | `fix/booking-conflict-db` | [x] |
| 4 | `chore/n8n-webhook-config` | [x] |
