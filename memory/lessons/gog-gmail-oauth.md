# Lesson — gog Gmail OAuth can silently fail (invalid_grant)

Date: 2026-04-01

## Symptom
Running:

```bash
GOG_KEYRING_PASSWORD=$(cat /data/.openclaw/.gog-keyring-password) \
GOG_ACCOUNT=brandongkirksey@gmail.com \
gog gmail search 'job application OR interview OR hiring OR offer letter newer_than:3d' --json
```

returned:

- `invalid_grant` — `Token has been expired or revoked.`

## Implication
Daily briefing can miss employer-related emails until re-auth is performed.

## Fix (next action)
Re-auth the `gog` Gmail connection for `brandongkirksey@gmail.com` (refresh OAuth token), then re-run the saved search.
