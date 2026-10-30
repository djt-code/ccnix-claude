# ccnix-claude

The Claude Code side of [ccnix](https://github.com/djt-code/ccnix) and
[ccnix-mod](https://github.com/djt-code/ccnix-mod): skills and other
harness material for working on them.

- `skills/architecture-decision/`: evaluate an existing codebase after a
  burst of changes and decide how to consolidate it, as an ADR in the repo
  with the user as decider, then execute the ADR with the test suite as the
  oracle. Proven on ccnix's ADR-0001 (2026-10-29).

- `githooks/`: a scan for environment-specific and sensitive details
  before anything reaches these public repos. `commit-msg` checks the
  staged diff and message; `pre-push` checks every outgoing commit. Each
  first matches `~/.config/ccnix-claude/sensitive.txt` (your own list of
  regular expressions, kept out of every repo), then asks Claude Sonnet
  through the Claude Code CLI (your claude.ai login). It blocks on a match
  or a "block" finding, prints "warn" findings, and stops if it can't run.
  `githooks/install.sh` points ccnix, ccnix-mod and this repo at it
  (`core.hooksPath`); `--no-verify` skips it on purpose.

To use a skill in a project, put it where Claude Code looks:
`<project>/.claude/skills/<name>/SKILL.md`, or `~/.claude/skills/<name>/`
for every project (a junction to this repo's folder keeps it in sync).
