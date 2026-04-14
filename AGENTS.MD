# AGENTS.MD

## 1. Role

You are a coding agent working on this repository.
Follow structured, milestone-driven development.
Make safe, minimal, and deterministic changes.

---

## 2. Purpose

This file defines **process rules only**.
Do NOT include or rely on domain logic here.

All domain logic (PnF, trading rules, architecture) must live in:

* docs
* code
* tests
* GitHub issues

---

## 3. Source of Truth (priority order)

1. User instruction
2. Active GitHub issue
3. PLAN.MD (current milestone)
4. Docs / tests / existing code
5. AGENTS.MD

If conflict occurs → follow this order.

---

## 4. Milestone Workflow

* Work strictly milestone-by-milestone from `PLAN.MD`
* Identify current milestone
* Break into small GitHub issues
* Work on **one issue at a time**
* Ensure issue is marked `In Progress` before starting
* After completion → request review → then move to next issue

Do NOT skip milestones.

---

## 5. Issue Execution Rules

Before coding:

* Understand the issue fully
* Read relevant code and docs

During coding:

* Keep changes small and focused
* Do NOT modify unrelated code
* Preserve existing behavior unless required

After coding:

* Ensure issue requirements are fully met
* Update docs if needed

---

## 6. Implementation Rules

* Read existing code before editing
* Prefer simple, clear solutions
* Avoid over-engineering
* Maintain deterministic behavior
* Follow existing structure and patterns

---

## 7. Testing & Review

* Add/update tests when required
* Verify behavior before marking complete
* Do NOT assume correctness without validation

---

## 8. Git & Commit Rules

* Do NOT commit without explicit user permission
* Do NOT push automatically
* Keep commits small and meaningful

---

## 9. Safety Rules

STOP and ask the user before:

* Destructive operations (delete/reset/migrate)
* Using secrets or environment values
* Enabling live trading or broker execution
* Large architectural changes
* Skipping milestones

Default to **safe behavior**.

---

## 10. Communication

Keep responses:

* Clear
* Short
* Actionable

Before making changes (when needed):

* State goal
* Files to change
* Any risks or assumptions

---

## 11. Conflict Handling

If unclear or conflicting:

* Pause
* Explain the issue
* Ask for clarification

Never guess in critical logic.

---

## 12. Key Principles

* Small steps
* Deterministic behavior
* Safety first
* Follow PLAN.MD
* One issue at a time
