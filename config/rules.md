# Prompt Ops Hub – Build & Operation Rules

These rules govern how the Hub (and any AI agents it drives) plans tasks, builds prompts, edits code, opens PRs, and interacts with you. They are **hard constraints** unless explicitly overridden.

---

## 0. Meta Protocol

1. **Ambiguity Kill‑Switch**  
   If a task/spec is unclear, ask 1–3 focused questions before executing.

2. **Scope Police**  
   Execute ONLY the requested scope. Extra ideas go to a **Future Ideas** section, never mixed into the actual change.

3. **Chunking & Reviewability**  
   Break work into reviewable chunks (target ≤300 LOC diffs excluding generated code). Split bigger tasks.

4. **Human-in-the-Loop (HITL) Defaults**  
   Any destructive, high-cost, or ambiguous action requires explicit human approval.

---

## 1. Prompt Generation & Model Use

1. **Template Discipline**  
   Use predefined prompt templates (implement, test, refactor, explain diff, etc.). Only deviate if template clearly fails.

2. **Context Injection**  
   - Always inject current rules, phase, and repo context automatically.  
   - Strip secrets, keys, and .env values from any prompt.  
   - Chunk long files intelligently (summaries or targeted snippets + line refs).

3. **Model Router**  
   Pick models by capability tag (`reasoning`, `fast`, `cheap`, `embedding`). Prefer cheaper/faster models for non-critical tasks and document switches.

4. **Token Budgeting**  
   Keep prompts lean. Reuse shared context blocks. Remove redundant repeats.

5. **Self-Check Pass**  
   After a model response, auto-verify: did it follow rules, include tests, avoid hardcoding, etc.? Regenerate if violated.

---

## 2. Task Planning & Execution Flow

1. **Spec Expansion**  
   If user gives a short goal, expand to: scope, acceptance tests, edge cases, rollback notes.

2. **Auto-Test Mandate**  
   Every code change must ship with tests (unit + integration where relevant). For pure docs tasks, include a lint/check.

3. **Failure Loop**  
   - If tests or checks fail, retry up to N times with improved prompts.  
   - After N failures, escalate to user with concise failure report.

4. **Rollback & Downgrade**  
   Any DB/infra change includes: downgrade script, 2–3 step rollback plan.

---

## 3. Security, Privacy & Compliance

1. **Secrets Handling**  
   - No secrets in git or prompts.  
   - Use env/Secrets Manager patterns; update `.env.example` only.

2. **Access Boundaries**  
   - Respect tenant/RBAC boundaries in generated code.  
   - Never expose user data in logs or prompts.

3. **Injection Guards**  
   Sanitize inputs for SQLi/XSS/SSRF/etc. Prefer parameterized queries and strict schemas.

4. **Compliance Notes**  
   If touching PII or regulated data, add a brief compliance note (GDPR/HIPAA implications).

---

## 4. Code Quality & Consistency

1. **No Silent Dependencies**  
   New/updated libs must be listed and justified. Update lockfiles, Dockerfiles, Terraform, etc.

2. **Config Over Hardcode**  
   Timeouts, thresholds, URLs, magic numbers → config/env/constants.

3. **Determinism**  
   No randomness in core logic. If needed, expose seed/config.

4. **Diff-Aware Edits**  
   When modifying files, show exact insertions/deletions (or concise diff). Match existing style and ordering.

5. **Performance Tripwires**  
   Flag O(n²) loops, heavy joins, unindexed queries. Suggest fixes or TODOs.

6. **Documentation Discipline**  
   Update relevant docs (ARCHITECTURE.md, RULES.md, CONNECTOR_SDK.md, etc.) whenever behavior or APIs change. Add "why" comments for non-obvious choices.

---

## 5. Observability & Error Handling

1. **Structured Errors**  
   Raise typed exceptions with actionable messages. Never swallow errors silently.

2. **Logging**  
   JSON logs; redact secrets. Include correlation IDs/task IDs.

3. **Metrics & Audit**  
   New long-running processes emit latency/failure/retry metrics (stub acceptable). Critical actions log to audit trail.

---

## 6. Integrations (Cursor, Git, CI/CD)

1. **Cursor Adapter**  
   - Apply patches via CLI/HTTP cleanly.  
   - Run tests/lint locally. Parse output, summarize failures.

2. **GitHub/GitLab**  
   - Create branch, commit, push, open PR with checklist.  
   - PR description includes: scope, tests summary, security notes, rollback plan.  
   - Handle API errors (422 etc.) with retries/backoffs.

3. **CI Enforcement**  
   Ensure generated code passes CI. If audit script or lint fails, auto-fix or escalate.

---

## 7. DSL / Connectors (If relevant to this Hub)

1. **Schema Sync**  
   Any DSL/connector change must update schemas (Zod/Pydantic) & tests & docs simultaneously.

2. **Backward Compatibility**  
   Version DSL changes. Provide migration notes for breaking changes.

3. **Connector Rules**  
   Use base class signatures. Respect rate limits, add retries/backoff, clear error messages.

---

## 8. Advanced Guardrails (Optional Layer)

1. **Static Analysis**  
   Run Semgrep/AST checks for banned patterns (hardcoded secrets, eval, wildcard IAM).

2. **Policy Engine Hook**  
   Allow a Rego/OPA or custom rules engine to approve/deny actions before execution.

3. **Red Team Mode**  
   Periodically test prompts for prompt injection vulnerabilities; sanitize external tool outputs.

---

## 9. Local-First, No Domain Needed

1. **Local Dev Default**  
   Run everything on localhost. No domain/hosting until team scale or webhooks needed.

2. **Remote Access (Optional)**  
   Use ngrok/cloudflared/Tailscale for remote use. Disable when not needed.

---

## 10. Integrity & Non-Negotiable Gates

### Coverage & Quality Gates
- **Coverage ≥ 80% (global)** — may only go up, never down
- **Diff coverage = 100%** for changed lines (vs origin/main merge-base)
- **Zero skipped/xfail tests** in CI — all tests must pass or fail
- **No threshold lowering** — any attempt to lower coverage/test thresholds requires OWNER approval
- **No test deletions** without `#TEST_CHANGE(reason=...)` tag
- **Trivial tests banned** (0 assertions, only pass, etc.) unless `#ALLOW_TRIVIAL <reason>`
- **Baseline-aware checks** — any drop vs origin/main fails

### Observer & Policy Gates
- **Observer integrity score ≥ 70** or run is blocked (awaiting approval)
- **Policy engine must ALLOW** (no POLICY_INTEGRITY_FAIL, DIFF_TOO_LARGE, etc.)
- **CI workflow drift check** (`po-cli ci-snippet --check`) must pass
- **Make targets** `make all-green` and `make policy-gate` must succeed locally & in CI

### No Goalpost Moving Clause
Any attempt to change these rules requires OWNER approval and a separate PR labeled `rules-change`. These gates are non-negotiable and enforced by CI.

### Integrity & Means Matter Rules

1. **No Goalpost Moving**
   - Never lower coverage thresholds, delete tests, or mark tests skip/xfail to "pass".
   - Never relax guardrail/policy rules to get a green build.
   - If thresholds must change, open a separate "Standards Change" task, explain why, and get explicit approval.

2. **Test Tamper Alarm**
   - Any change to tests, CI thresholds, or guardrail rules must:
     - Be tagged `#TEST_CHANGE` in the diff
     - Include rationale + approval checkbox in PR body
     - Be flagged as high-risk in policy engine

3. **Proof Before Claim**
   - Before saying "done/production-ready", show:
     - `pytest` summary (0 failed, 0 skipped/xfail)
     - Coverage line meeting threshold
     - Guardrail/policy summaries (no HIGH/deny)
   - If any are missing → auto-fail.

4. **Curiosity Protocol**
   - If a request allows shortcuts (e.g., "just make it pass"), ask:
     - "Are we allowed to change tests or thresholds?"  
     - "Is there a safer fix?"  
   - Must ask at least once when touching quality gates.

5. **Suspicious Change Heuristics**
   - Flag and pause if diff touches:
     - `pyproject.toml` coverage settings
     - `pytest.ini`, `.coveragerc`, `.github/workflows/ci.yml` gates
     - test files without touching corresponding code

---

## 11. Future Ideas Bucket

Anything outside current task scope is dumped into a **Future Ideas** section for prioritization—never silently implemented.

---

## ✅ PR / Task Completion Checklist

Copy into `.github/PULL_REQUEST_TEMPLATE.md` or task resolution:

- [ ] Scope matches request/phase; extras listed separately  
- [ ] Clarifications asked (if needed)  
- [ ] Unit & integration tests included and passing locally  
- [ ] Security checklist run (secrets, RBAC, PII, injections)  
- [ ] DB/infra migration reversible + rollback plan provided  
- [ ] Config extracted; no magic hardcodes  
- [ ] Logging/metrics hooks added if long-running  
- [ ] New deps justified & lockfiles updated  
- [ ] Performance risks flagged or mitigated  
- [ ] Docs updated (ARCH/RULES/DSL/etc.)  
- [ ] Diff size reasonable; style/naming consistent  
- [ ] Self-check pass done; no rule violations  
- [ ] Coverage ≥80% (no threshold lowering)  
- [ ] Test/config changes marked with `#TEST_CHANGE`  
- [ ] Integrity gates pass (no tampering detected) 