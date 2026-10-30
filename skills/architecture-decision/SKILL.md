---
name: architecture-decision
description: Evaluate an existing codebase after a burst of changes and decide how to consolidate it, or record any architecture decision as an ADR. Use for "go over everything since X and simplify", "organize the stack around the new additions", a review of a design proposal, or a choice between two mechanisms that do one job. Produces an ADR in the repo with the user as decider, then executes its action items with a test suite as the oracle.
argument-hint: "<what to evaluate or decide>"
---

# /architecture-decision

An Architecture Decision Record (ADR) that comes from the code, and a way of
executing it that proves each step changed nothing it shouldn't. Written for
a small team (often one person) with codependent repos and a test suite.

## 1. Scope and oracle, before anything else

- **Scope by history.** Name the commit range or feature set ("everything
  since `<sha>`", "the last N commits"). Read `git log` and the diffstat,
  not just the tree.
- **Establish the oracle.** Run the whole test or simulation suite **twice**
  and diff the two outputs. Fix any line that differs (timings, table
  addresses, `pairs` order) before anything else: a suite that isn't
  byte-for-byte repeatable can't prove a refactor changed nothing. Save the
  output as the baseline.
- **State the forces** you already know: what the user values (simplicity,
  real-protocol compatibility, review time), platform limits, installed
  clients that constrain renames, sibling repos that must change in step.

## 2. Evidence: one read-only reviewer per subsystem

For anything over a few thousand lines, fan out one read-only agent per area
(boot/deploy, the shell layer, the network, the programs, the libraries, the
tests/docs...). Each brief says:

- the files, the commit range, the README section to read (not the whole README);
- what to look for: duplicated mechanisms, repeated helpers, rename
  leftovers (classified: live compatibility vs plain text), dead code,
  docs contradicted by code, test gaps;
- **verify every premise you hand it** ("files are CRLF", "help is stale") —
  reviewers should check and correct you, and they will;
- the report format: ranked by value against risk; each finding with
  `path:line` evidence and duplicates quoted side by side, the concrete
  change, rough size, **which test covers it or "untested"**, and whether a
  sibling repo needs a matching change; a closing "checked and fine" list.

Keep their conclusions, not their file dumps.

## 3. The ADR

Write it into the repo (`doc/adr/NNNN-<slug>.md`), status **Proposed**, the
user as **Decider**. Commit it before acting on anything in it.

```markdown
# ADR-NNNN: Title
**Status:** Proposed | Accepted | Superseded   **Date:**   **Deciders:**
## Context        — the range, the forces, the method, the reviewers' conclusions in a paragraph
## Decision       — one numbered line per decision
## Options Considered
### D1. <the overlap>
| | A: keep both | B: fold A into B | C: fold B into A / delete |
|---|---|---|---|
| Complexity | | | |
| Lines | | | |
| Verification | the test that proves it, or "untested" | | |
| Blast radius | siblings, installed clients, docs | | |
| Familiarity | | | |
<one paragraph: which, and why>
## Trade-off Analysis   — where the pass spends risk and where it declines to
## Consequences         — easier / harder / revisit
## Action Items         — phases, one line each: what, size, the test, sibling impact
```

- **One section per overlap.** Two mechanisms doing one job (two schedulers,
  two startup paths, a rule encoded twice) is one decision with the options
  keep both (and why), fold A into B, fold B into A, delete one. A
  comparative table per decision is denser than a table per option and
  reads better.
- **Honest accounting beats a tidy answer.** "Merging would add ~100 lines
  to delete ~150 and rewrite tested code" is a legitimate reason to keep two.
- **Separate what's decided-unless-objected from what's the user's call**
  (anything touching installed devices, other people's workflows, a
  consciously deferred choice). Put the user's calls in a numbered list in
  the chat with a recommendation each, and ask for numbers back.
- **Phase the action items:** 0 safety net (repeatability, scenarios for
  what has none, a scenario for the thing the big decision relies on);
  1 defects found on the way (one commit each); 2 mechanical consolidations
  (no decision needed); 3 the decisions, after acceptance; 4 docs, siblings,
  pointer bumps, mark Accepted.

Phases 0–2 start while the user reads. Phase 3 waits.

## 4. Executing it

- **Implementation agents in isolated worktrees**, one per disjoint file
  set, with a brief that quotes the reviewer's evidence and names the
  covering test. Protocol for each: run the suite before the first edit;
  after every item `--check`/lint, the full suite, and a diff against the
  before-output that must be **empty unless the item changes a test** (then
  exactly that, explained); one commit per item in the repo's message style;
  no pushing; report commits, diffs, deviations, branch and worktree.
- Tell agents to **suffix their scratch files** (a shared scratchpad gets
  overwritten mid-run) and, when a generator rewrites many files (help
  pages, line endings), to **stage only the ones whose content changed**.
- **Review each branch's diff yourself**, then `git cherry-pick <base>..<branch>`
  onto main (linear history), run the suite against the baseline, push, and
  `git worktree remove` + `git branch -D`. Re-baseline after each merge.
- A deviation from the brief with a reason ("the literal recipe breaks
  `seq 5 -2 0`") is what you want from an agent; accept it when the reason
  holds.
- **Siblings:** a separate agent per sibling repo; bump submodule pointers
  last (the dependency's first, then the dependant's), and push the
  dependency before the dependant so no pointer dangles.

## 5. Closing

Mark the ADR **Accepted** with the user's answers recorded, tick the action
items, note what the user still has to verify in the real environment, and
leave the baseline reproducible for the next pass.

## Tips

1. **Name the commit range in the request**; "the whole stack" scopes nothing.
2. **State constraints upfront**: the user's taste for simplicity, platform
   limits, what's installed where. They shape every option table.
3. **The suite is the argument.** If a proposal has no test, say "untested"
   in the table; that's where the risk is, and often where a Phase 0
   scenario should go first.
