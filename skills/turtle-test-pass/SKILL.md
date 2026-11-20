---
name: turtle-test-pass
description: The companion of /turtle-field-report. After a ccnix release, have the Claude model driving a turtle in game test the release's in-game checks. Use for "write the next field test suite", "put the test plan on the turtle", "launch the test pass", "close the issues from the turtle's results". Writes a test plan from the open needs-in-game-test issues, with evidence rules so a pass proves the fix, installs it on the turtle's disk, gives the user the launch steps, and afterwards turns the results into closed issues, bugs and the next field report.
argument-hint: "<computer ID of the turtle> [release, e.g. 0.54.0]"
---

# /turtle-test-pass

`/turtle-field-report` turns the turtle's findings into fixes and a
release. This skill checks the release in the real game, with the turtle
as the tester, and feeds what it finds back into the next field report.
Together they make one loop:

  field report → ADR → release → **test plan → test pass → results** → field report

One pass is one plan, `tests-v<N>.md`. Its checks are the release's
`needs-in-game-test` issues, and its results close them.

## 1. What to test

- **The release's checks:** the open sub-issues of the pass's parent
  `needs-in-game-test` issue (its ADR's), on the ccnix board. Add older
  open checks the turtle can do where it is: the label across both repos
  (`gh issue list -l needs-in-game-test` in ccnix and ccnix-mod).
- **The last test pass:** its results file on the turtle
  (`/claude/test-<...>-results.md`). Read it for the scratch area's corners,
  what was skipped and why, and what failed. A FAIL fixed since is a
  check again.
- **The turtle's own newer reports** (`report_harness_v<N>.md` written
  since the release): a fault it hit that the release claims to fix is
  a check too.
- **Leave out** what needs the other base, more than about 300 fuel,
  materials the turtle can't cheaply get, or a player's hands for long.
  Those stay open for the player.

## 2. Write the plan

Use the last plan as the pattern (v5 was `tests-0.54.md`, v6
`tests-v6.md`, both on turtle 10's disk). It's written for the model,
in its terms (T.* calls, messages it will see, files under `/claude`).

- **Ground rules first:**
  - a results file, one line per check, written after every check;
  - resume.txt is the harness's;
  - never end a reply until the last check: ask in chat with
    `ask = true`;
  - the scratch area, snapshot at the start and checked at the end;
  - the budget, and never go to the other base;
  - the player told at each part;
  - a report kept as it works.
- **Parts by area:**
  - Part 0 (start of session) first: the news, retiring helpers,
    equipment, the setup;
  - then the sandbox, tools, store, building;
  - the harness last, and a reboot check, if any, last of all.
- **Each check:** an ID, its issue number `(#N)`, what to do, and what
  should happen, with the exact message the new code prints.
- **The rigour rules**, in the ground rules and in each check (proven
  on v6):
  1. **Evidence:** each check names what only the new code gives (a
     message, value or list, and what the old code did instead). A PASS
     quotes it. A right result without it is **INCONCLUSIVE**, and its
     issue stays open.
  2. **Validity gates:** check the setup a measurement needs before
     trusting it. For example, the tick-rate ratio (`os.clock` against
     `realtime`: about 3 at `/tick rate 60`, 1 at 20) before and after
     timing checks. A wrong setup makes the check INCONCLUSIVE.
  3. **Helpers that replace T:** after retiring helpers, `helpers()`
     lists the helper names T has too. A check whose function a helper
     still replaces is marked so on its line.
  4. **Shared resources:** where features compete (the two equipment
     sides: pickaxe, modem, chat box, chunk controller), a check of them
     together. Record each side and the item counts before and after; the
     chunk controller's side never changes.
  5. **State at each part's start** (sides, tick ratio, free slots,
     fuel), and the setup in Part 0 (ROM version, chunk controller side).
     A leftover is caught where it happened.
  6. **Pass ranges** for anything measured ("9 to 11 s", not "about
     10").
- **File names:** list the turtle's `/claude` first (step 4). The
  report is the next free `report_harness_v<N>.md`. The turtle writes
  its own reports between passes, so the number may have moved on.
- Save the plan in the user's Downloads and the scratchpad. It holds the
  issue numbers but nothing private. It stays off the public repos, as
  it's about one world.

## 3. The ROM on the server

The plan tests a release, so the server must run it.

- **Read the server log's last "ccnix ROM:" line**, read-only:
  `sudo -n grep -a "ccnix ROM" <minecraft_dir>/logs/latest.log | tail -1`.
  The host and paths are in ccnix-mod's ansible inventory and
  host_vars (gitignored; `minecraft_dir` in group_vars).
- **If it's older**, the user updates it in game: `/ccnix rom update`,
  then `/ccnix rom update confirm` (op; it pulls the server's ROM
  checkout and reloads). That's their command: put it in the launch
  steps, don't run it.

## 4. Install the plan on the turtle

The disk is `<minecraft_dir>/world/computercraft/computer/<id>/`, and
`/claude` on the turtle is its `claude/`.

- **Read first:**
  - list `claude/`, and check the plan's name and the report name are
    free;
  - check `du -sb` of the computer against `computer_space_limit` in
    `<minecraft_dir>/config/computercraft-server.toml`;
  - check `resume.txt`: if there is one, a goal is under way, so ask
    before going on.
- **Write as the server's user**, so the game can read it:
  `ssh <user>@<host> "sudo -n -u minecraft tee <dir>/claude/tests-v<N>.md
  >/dev/null" < tests-v<N>.md`. Then compare `sha256sum` on both sides.
- **Only the plan.** Never overwrite a file of the turtle's (its
  notes, helpers, reports and results are its own). Never copy or print
  `claude.key`.

## 5. The launch steps (for the user)

Give them as a numbered list, each with what they should see:

1. **The ROM, if step 3 found it old:** `/ccnix rom update`, then
   `confirm`. The chat answer should name the new version.
2. **Reboot the turtle** (Ctrl+R held at it), so it boots the new ROM.
   `ccnix version` at its shell should show the release.
3. **Players:** someone at hand for the checks that need them; say
   which, and roughly when (the parts). The turtle asks in chat and
   SKIPs after its timeout.
4. **Start claude with the plan's options**, for example
   `claude --steps 400 --cache 1h`. A check of the kept options (E2 in
   v6) depends on them.
5. **The goal,** one line (the prompt reads one line of 512 characters
   at most): `Run the test plan /claude/tests-v<N>.md: read it whole
   first, then follow it to its end.`
6. **What to expect:**
   - the "ccnix was updated" news first;
   - chat at each part;
   - the reboot check last, when the player holds Ctrl+R at the turtle,
     and after it the "You were interrupted (reboot)" start.

## 6. After the run

- **Fetch** the turtle's files as `/turtle-field-report` step 1 does,
  into a new dated folder.
- **Read the results file**, and go through it line by line:
  - **PASS with its evidence:** close the issue with a comment: what the
    turtle saw, the evidence quoted, the pass and its date.
  - **FAIL:** a `bug` issue of its own (the check's text, what
    happened, the whole why), linked from the check, which stays open.
  - **INCONCLUSIVE or SKIP:** a comment saying why, and the issue stays
    open for the next pass or the player.
  - Close a parent issue once all its sub-issues are closed.
- **Then `/turtle-field-report`** on the pass's report: its FAILs and
  its friction are the next ADR's evidence. Give the user the counts,
  the FAILs, the INCONCLUSIVEs, and the issues closed.

## Tips

1. **A plan is only as good as its evidence lines.** "It worked" from
   the model is a claim. The message only the new code prints is proof.
2. **Ask the turtle for numbers**: counts, seconds, slots, sides. They
   make a FAIL a bug report, not an impression.
3. **Keep the reboot check last.** It cuts the session, and everything
   after it depends on the resume working.
