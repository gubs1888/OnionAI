# CONTRIBUTING — Onion Quality AI

Four teams, five days, one repository. Read this once — it prevents 90% of
merge pain.

## 1. Branching model

```
main        ← protected. Only lead architect merges here (stable demo-able state).
develop     ← integration branch. Feature branches merge HERE via PR.
feature/ml  ← TEAM A
feature/backend ← TEAM B
feature/mobile  ← TEAM C
feature/qa      ← TEAM D
```

Rules:
* **Never commit directly to `main`.** Even the architect.
* Branch from `develop`, PR back into `develop`.
* Name extra branches `feature/<area>-<topic>`, e.g. `feature/ml-augment`.
* Sync daily: `git checkout develop && git pull && git checkout -` then
  `git rebase develop` on your feature branch.
* Before the demo: architect merges `develop → main` and tags `v0.1-demo`.

## 2. Code ownership (protected paths)

| Team | Owns (may change freely) | Must not touch without sign-off |
|---|---|---|
| A — ML/CV | `ml/**` | `backend/app/services/inference.py` (only file!) |
| B — Backend | `backend/**`, `docker-compose.yml`, `.env.example` | `mobile/types/assessment.ts` |
| C — Mobile | `mobile/**` | `backend/app/schemas/**` |
| D — QA/Docs | `docs/**`, `scripts/**`, root `*.md`, CI workflow, all `tests/` additions | any production code |

**Contract files** (`docs/api/API_CONTRACT.md`, `backend/app/schemas/`,
`mobile/types/assessment.ts`, `ml/inference.py` output shape,
`backend/config/grading_config.json` semantics): changes need a 2-minute
stand-up agreement + the architect in the PR. No surprise renames.

**Shared files** (README root, docker-compose, pytest.ini): one PR at a time,
small diffs, announce in team chat before pushing.

## 3. Commit conventions

Conventional commits with an area scope:

```
feat(backend): add batch status filter
feat(ml): add rot annotation guide
feat(mobile): wire results screen to real assessment
fix(api): correct URS rounding
docs(qa): demo script v2
test(backend): 404 envelope for unknown batch
chore: bump expo sdk pin
```

Keep commits small and single-purpose. Never commit `.env`, model weights
(`*.pt`), dataset photos, or `node_modules` — all gitignored already.

## 4. Pull requests

* Target `develop`. One PR per topic; keep them reviewable (< ~400 lines).
* PR description must state: what changed, which contract (if any) is touched,
  how to test it.
* CI must be green (backend tests + ML tests + mobile typecheck).
* One approving review from the owning team is enough; contract PRs need the
  architect too.
* Rebase before merging; no messy merge-commit soup.

## 5. How to avoid conflicts (the 5 golden rules)

1. Stay inside your owned paths — cross-cutting changes go through PRs.
2. All cross-team data moves through the contracts, never by editing the
   other team's code.
3. Pull/rebase `develop` at least every morning.
4. Config values live in `.env` / `grading_config.json`, not in code.
5. When in doubt for >15 minutes, ask in chat — a 2-line message beats a
   2-hour rewrite.

## 6. Definition of done

`code + test + docs + demo-able in DEMO MODE`:

* [ ] Tests added/updated and green (`python -m pytest`, `npm run smoke`)
* [ ] OpenAPI/schemas updated if endpoints changed
* [ ] TODO / DEMO / MOCK markers left where functionality is unfinished
* [ ] No secrets, no big binaries committed
