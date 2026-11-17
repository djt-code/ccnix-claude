---
name: turtle-field-report
description: Close the self-improvement loop between a Claude model driving a ccnix turtle in game (turtle/claude.lua) and the code it drives (turtlelib, the claude harness). Use when the in-game model has written a report or notes, or for "pull /claude off the turtle", "another harness and turtlelib pass from the turtle's notes", "what has the turtle learned". Fetches the turtle's files and log, turns its findings into an ADR with the user as decider, builds the accepted items with the sims as the oracle, ships them, and tells the turtle what changed so its next report starts from there.
argument-hint: "<computer ID of the turtle> [what to focus on]"
---

# /turtle-field-report

The in-game model is a user of turtlelib and of the harness that nobody
else can be: it builds real things for days and writes down what got in
its way. This skill turns that into general improvements, then hands the
result back to it. One pass is one ADR.

Run it with `/architecture-decision` beside you: steps 3 to 5 are that
skill's method applied to field evidence. This page says what's
different.

## 1. Fetch the field data (read-only on the server)

- **Which turtle:** its computer ID (the user knows it; the label isn't
  in the files). Its disk is `world/computercraft/computer/<id>/` on the
  server (the dev server's world path is in the ccnix-mod ansible
  inventory and host_vars, both gitignored; a singleplayer world is under
  the instance's `saves/<world>/computercraft/computer/<id>/`).
- **Stream, don't write on the server:** `ssh <user>@<host> "sudo -n tar
  -C <computer dir> -cf - --exclude=ccnix/turtle/claude.key claude ccnix
  .settings .ccsh_history" | tar -xf - -C <dest>`. Never copy
  `claude.key` (the API key), and never print it.
- **What you get:** `claude/` (the model's own folder: reports,
  `memories/`, `helpers.lua`, plans, scripts), `ccnix/turtle/claude.log`
  and `claude.log.1` (the harness log: `start:`, `goal:`, `tokens:`,
  `goal done:`, retries), and turtlelib's state (`.chests`,
  `.protected`, `.map/`, `.build`, `.turtlepos`...).
- **Where:** a dated folder outside every repo (the user's Downloads or
  the scratchpad), `turtle<id>-claude-<yyyymmdd>`. Tell the user the
  full path.
- **Privacy:** these files hold the player's name, coordinates and
  whatever the player typed. Nothing of them goes into the public repos
  verbatim: write `<player>`, describe places generically ("a lava moat",
  not the castle's coordinates), and let the commit hook scan.

## 2. Evidence: three read-only reviewers, in parallel

Spawn them in the background with briefs that point at the files (not
your conclusions) and ask for `path:line` or log-timestamp evidence.

1. **Field evidence.** The report, the memories, the log, the helpers,
   the state files. What the report doesn't say; the field evidence for
   each of its top items (or "none beyond the report", or a
   contradiction); each helper in `helpers.lua` (what it wraps, general
   or world-specific); the T.* functions used most and the errors hit
   repeatedly; the harness numbers (sessions, goals, tool calls, tokens,
   cache, retries, clears); anything odd in the state files.
2. **Library gaps.** Every request and defect claim in the report checked
   against `turtle/turtlelib.lua`, `turtle/tl/*.lua`, `help/turtlelib.txt`
   and `turtle/tl/index.txt`: EXISTS (and did the model just not know?),
   PARTIAL, MISSING, BUG (confirmed in code), or WRONG (the report
   misread the code). Work items by module with size, covering sim, and
   what `mine`/`farm`/`mow`/`build` rely on.
3. **The harness.** The same for `turtle/claude.lua` and
   `sim/claude_drive.lua`: tools, system prompt, context editing,
   caching, the log, helpers.lua loading. Proposals with the API facts
   they rely on, marked "needs checking" when the code doesn't already
   use the feature (check them with the claude-api skill before they
   reach the ADR).

**Check the reviewers too.** Spot-check each claim the ADR leans on
by reading the cited lines whole (`sed -n`), not with a narrow grep: a
pattern that wants text after the match misses a line that ends sooner,
and a true finding looks false. And read the log's coverage first: it
rotates, so it may hold only the last few hours; earlier days survive
only in the model's notes. `.ccsh_history` shows the options the user
really runs claude with.

**The model's report is a user's report.** It is often right about what
hurt and sometimes wrong about why. "EXISTS, but not in the index" is a
documentation fix, not a new function; a "silent" failure may be a
message it never saw because the output was cleared.

## 3. The ADR (`doc/adr/NNNN-<slug>.md` in ccnix)

As `/architecture-decision` writes it, with these habits:

- **Number it** after the last ADR in `doc/adr/`, and commit it
  (Proposed) by pull request before acting on it.
- **Context** names the turtle, the dates, the report and the reviewers'
  conclusions in a paragraph, and quotes the log numbers.
- **Group by what changes, not by the report's sections:** safety (digs
  near liquids, budgets), feedback (every refusal says why, loud
  failures), the model's knowledge (index, help, the system prompt),
  new functions, harness features. A defect is Phase 1; a missing
  documentation line is Phase 2; a new function or tool is a decision.
- **Fold the helpers in deliberately:** a general helper from
  `helpers.lua` becomes a T function only with a sim and a help entry;
  the turtle then deletes its own copy (step 6 tells it to).
- **Defaults are the user's:** anything that changes what an existing
  program does (a refusal on by default, a new limit, a changed default
  like `maxHeight`) is a numbered decision with a recommendation.
- **The user's calls** go in the chat as a numbered list, a
  recommendation each, and wait. Phases 0 to 2 go ahead meanwhile.

## 4. Phase 0: the oracle and the failures as scenarios

- `python sim/run.py` twice, diffed: it must repeat byte for byte (the
  runner pins the clock and the random seed; a check that prints a table
  address or the time is a fix). Save the output as the baseline in the
  scratchpad.
- **Each field failure becomes a sim scenario first**, that fails on
  today's code: the dig beside lava, the junk trip that fails inside a
  protected area, the stale progress line. The fix then turns it green
  and changes nothing else in the baseline.

## 5. Build, release, deploy

- One branch and pull request per phase or module (ADR-0009 flow: CI
  green, merge yourself), one commit per item. After each item: `--check`,
  the full suite, and a diff against the baseline that is empty except
  for the item's own checks. Re-baseline after each merge.
- Regenerate help (`python sim/mkhelp.py`): `help/turtlelib.txt` and
  `turtle/tl/index.txt` are what the in-game model reads. Keep index
  lines short; they cost tokens on every request.
- Bump `deploy/version` (a feature: minor) only once the user says ok:
  the release waits for them. Then the release and the lockstep bump in
  ccnix-mod run. UNTESTED.md gets each item's in-game check, in a
  section with its own `needs-in-game-test` issue (the number in the
  heading). The server takes the ROM with `/ccnix rom update` (the user's
  command) or a new jar.

## 6. Hand it back to the turtle

The loop closes only if the in-game model learns what changed.

- **What's new:** the harness tells the model, at the start of a
  session, what changed in turtlelib and the harness since the version
  it last ran. Write that pass's lines into the release's changelog
  section the harness reads, short and in the model's terms: "T.digCell
  exists now (your helpers.lua digCell can go)", "T.inside takes a list".
- **Its helpers:** list which of its `helpers.lua` functions the pass
  replaced, so it can retire them itself (the files are its own; don't
  edit them on the server).
- **The next report:** ask the user to give the turtle a goal like "read
  what's new, update helpers.lua and your notes, and keep
  /claude/report_harness_v<N+1>.md as you work". The ADR's Consequences
  name what the next report should watch.

## 7. Closing

Mark the ADR Accepted with the user's answers, tick its items, move what
the user tried (or the next field report shows working) into
UNTESTED.md's Tested section, ticking and closing the section's issue, and
keep the fetched folder until the next pass (it is the "before" picture).

## Tips

1. **Read the report first, the log second.** The log says what happened;
   the report says what the model thought happened. The gap between them
   is where the best fixes are.
2. **Count before fixing.** "807 fuel for 58 blocks" is an argument;
   "it felt slow" isn't. Quote the numbers in the ADR.
3. **Prefer making a failure loud over making it impossible.** A refusal
   with a reason teaches the model; a silent workaround teaches nothing.
