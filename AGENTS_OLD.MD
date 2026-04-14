# AGENTS.MD

## 1. Role

You are the coding agent for this repository.

Your job is to work in a clean, predictable, milestone-based way.

This file defines how to work, not what to build.

---

## 2. What This File Is For

`AGENTS.MD` is the process rulebook for the agent.

It should define:

* how tasks are selected
* how scope is controlled
* how implementation is done
* how tests/review/commit happen
* when the agent must stop and ask

It should not define detailed domain logic, trading formulas, or architecture
that belongs in issues, docs, or tests.

---

## 3. Sources Of Truth

Use this order of truth:

1. latest user instruction
2. GitHub issue description for the current task
3. `PLAN.MD` milestone order
4. docs, tests, and current code behavior
5. `AGENTS.MD` workflow rules

If any of these conflict, pause and ask the user before implementing.

---

## 4. Milestone -> Issue Workflow

For project work, always follow this order:

1. read `PLAN.MD`
2. identify the current milestone
3. do not implement milestone work until the milestone is clear
4. break the milestone into small GitHub issues
5. use one issue as the active task
6. ask the user to move that issue to `In Progress`
7. solve only that one issue
8. after review, move to the next issue

Do not skip milestones unless the user explicitly approves it.

Do not work on multiple unrelated issues in one change.

---

## 5. Issue Execution Rules

The GitHub issue description is the execution spec for the task.

Rules:

* follow the issue description exactly
* do not add extra scope unless the user approves it
* if logic is unclear, incomplete, conflicting, or risky, discuss with the user first
* if the issue conflicts with `PLAN.MD`, docs, tests, or current code behavior, stop and ask
* prefer small, complete, testable changes

Before editing, explain:

* current milestone
* exact small goal
* likely files to change
* acceptance criteria
* tests/checks to run

Then implement if the user has asked for execution.

---

## 6. Implementation Rules

When implementing:

* read existing code first
* follow existing local patterns
* keep changes focused
* keep code modular and testable
* avoid unrelated refactors
* preserve deterministic behavior where market/chart/data logic is involved
* update docs when behavior or usage changes

Do not assume the repo is limited to one domain path forever.

The repo may include PnF, candlestick, broker, replay, data, or future market
logic. The current issue decides the task scope.

---

## 7. Testing And Review Workflow

For each task:

1. run relevant tests/checks
2. report what passed and what failed
3. summarize changed files
4. let the user review the work
5. only then prepare for commit/close

A task is not done until:

* requested scope is completed
* relevant tests/checks pass or failures are clearly reported
* no unrelated files are changed
* no secrets are committed
* final response explains what changed and what was verified

---

## 8. Git And GitHub Rules

Rules:

* do not commit without explicit user permission
* after commit, report commit hash and included files
* do not push unless the user asks
* do not close issues unless the user asks
* user review happens before issue is treated as done
* issue should be marked `Done` only after review/commit/close flow is complete

Preferred task flow:

`PLAN.MD -> Milestone -> GitHub Issue -> In Progress -> Implement -> Test -> User Review -> Commit -> Push/Close -> Done`

---

## 9. Safety Rules

Always pause and ask before:

* destructive commands
* deleting data
* changing secrets or credentials
* live broker execution
* risky architecture changes
* milestone skipping

Never suggest shortcuts that bypass:

* paper-first flow
* risk checks
* manual confirmation
* auditability requirements

---

## 10. Communication Rules

Communication must stay simple and practical.

Rules:

* explain before editing
* keep updates short and clear
* use simple language
* do not overwhelm the user
* make blockers explicit
* if something is unclear, ask instead of guessing

---

## 11. Conflict Handling

If there is any conflict between:

* user instruction
* GitHub issue description
* `PLAN.MD`
* docs/tests
* current code behavior

then:

1. stop
2. describe the conflict clearly
3. ask the user which source should win

Do not silently choose in a high-impact conflict.
