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

## PR progress

| PR | Branch | Merged |
|----|--------|--------|
| 0 | `main` — docs + rules + `.env.example` | [ ] |
| 1 | `fix/security-request-cache-idor` | [ ] |
| 2 | `fix/auth-hardening` | [ ] |
| 3 | `fix/booking-conflict-db` | [ ] |
| 4 | `chore/n8n-webhook-config` | [ ] |
