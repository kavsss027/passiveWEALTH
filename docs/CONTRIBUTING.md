# CONTRIBUTING.md
# Contribution Guidelines

---

## Branch Naming

```
feature/short-description       new functionality
fix/short-description           bug fix
refactor/short-description      refactor without behaviour change
docs/short-description          documentation only
test/short-description          test additions or fixes
```

Examples:
```
feature/split-handler
fix/dividend-ex-date-eligibility
refactor/sequencer-sort-logic
test/bonus-calculation-edge-cases
```

---

## Commit Message Format

```
type(scope): short description

Longer explanation if needed. Reference which document governs
this logic if relevant.
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Scopes: `split`, `bonus`, `dividend`, `sequencer`, `engine`, `pipeline`, `api`, `db`, `core`

Examples:
```
feat(dividend): implement ex-date eligibility check per CORPORATE_ACTION_LOGIC.md

fix(sequencer): correct same-date priority order — split must precede bonus

test(engine): add reconstruction test using real INFY 2004 split event

docs(schema): document NUMERIC(20,4) decision in DATABASE_SCHEMA.md
```

---

## Before Opening a PR

Run the full check sequence:

```
make lint       # black + mypy
make test       # full pytest suite
make test-cov   # coverage report — must be 90%+ on corporate_actions/ and reconstruction/
```

If any of these fail, the PR will be blocked by the PM agent.

---

## PR Description Template

Every PR must include:

```
## What this changes
Brief description of what was built or fixed.

## Which phase this belongs to
Phase X — [Phase name from DEVELOPMENT_SEQUENCE.md]

## Which documents govern this logic
- CORPORATE_ACTION_LOGIC.md — section X
- RECONSTRUCTION_ENGINE.md — section Y

## How to verify
Steps to test manually beyond the automated suite.

## Known limitations or follow-up tasks
Any shortcuts taken, edge cases deferred, or follow-up work needed.
```

---

## Files That Require Extra Review

The following require two reviewers or PM agent explicit approval before merge:

- `corporate_actions/split.py`
- `corporate_actions/bonus.py`
- `corporate_actions/dividend.py`
- `corporate_actions/sequencer.py`
- `reconstruction/engine.py`
- `reconstruction/state_machine.py`
- `reconstruction/quantity_tracker.py`
- `database/models/` — any file
- `core/exceptions.py`

---

## What Blocked PRs Look Like

The PM agent will block a PR and add a review comment if any of these are found:

- float used instead of Decimal for any monetary or quantity value
- Engine module importing from repository layer
- Router containing business logic
- Missing test file for a new corporate action handler
- Test using random or non-deterministic values for financial calculations
- SQLAlchemy 1.x query style used
- Pydantic v1 validator syntax used
- Untyped exception raised from engine code

Fix all blockers before requesting re-review.
