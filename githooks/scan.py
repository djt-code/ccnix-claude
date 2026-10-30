#!/usr/bin/env python3
"""Keep environment-specific and sensitive details out of public repos.

    scan.py commit <message-file>     (commit-msg: the staged diff and the message)
    scan.py push                      (pre-push: every outgoing commit, diff and message;
                                       git passes the refs on stdin)

Two checks, in order:

1. Literals.  Each line of ~/.config/ccnix-claude/sensitive.txt (or
   $CCNIX_SENSITIVE) is a regular expression for something that must
   never be published: your hosts, subnets, usernames, paths.  The list
   lives outside every repo, so it isn't published either.  A match
   blocks, without asking a model.
2. Sonnet.  The same text goes to Claude Sonnet through the Claude Code
   CLI (`claude -p`, your claude.ai login), which reports anything that
   looks environment-specific or secret.  A finding it marks "block"
   blocks; "warn" is printed and lets it through.

Fails closed: if the scan can't run, the commit or push stops.
`--no-verify` skips it on purpose; CCNIX_SCAN=off does the same.
CCNIX_CLAUDE names the CLI if it isn't on the path or in VS Code's
Claude Code extension.
"""
import glob, json, os, re, shutil, subprocess, sys

MODEL = os.environ.get("CCNIX_SCAN_MODEL", "sonnet")
CHUNK = 120_000                # characters of diff per model call

PROMPT = """You review text that is about to be committed or pushed to a PUBLIC git repository (a Minecraft/ComputerCraft hobby project: Lua programs, a Java mod, Ansible, docs). Find anything that reveals the author's own environment or is secret, so it can be removed before publishing.

Report ("block"):
- hostnames, domains or URLs of the author's own private machines or services (not public sites)
- real IP addresses or subnets of the author's networks: an address in an inventory, a deployment note, a log, a commit message about a deployment
- usernames of the author's accounts or machines, home-directory paths (C:\\Users\\name, /home/name, /c/Users/name), local folder names that identify the machine
- network interface names, MAC addresses, machine names taken from a real machine
- credentials of any kind: passwords, tokens, API keys, private keys, session cookies
- email addresses other than in a commit's author line

Allowed (do not report):
- documentation addresses and names: 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24, example.com/.net/.org, placeholders like <you>, admin, devserver, eth0
- addresses that are part of the program or its tests: the in-game CC networks (10.x.x.x in ccnix's docs, help and sims), made-up addresses in unit tests and fixtures
- public URLs of the project itself (github.com/djt-code/..., raw.githubusercontent.com/djt-code/...), Maven/Modrinth/CurseForge/NeoForge download URLs
- version numbers, commit hashes, file paths inside the repo

Use "warn" for things that are probably fine but worth a second look. Quote the exact text. Report nothing you are unsure is real; an empty list is the common answer."""

SCHEMA = {
    "type": "object",
    "properties": {"findings": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "severity": {"type": "string", "enum": ["block", "warn"]},
            "where": {"type": "string", "description": "file and line, or 'commit message'"},
            "text": {"type": "string"},
            "why": {"type": "string"},
        },
        "required": ["severity", "where", "text", "why"]}}},
    "required": ["findings"],
}

ZERO = "0" * 40


def git(*args, input=None):
    return subprocess.run(["git", *args], input=input, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=True).stdout


def fail(msg):
    print("scan: " + msg, file=sys.stderr)
    print("scan: stopped. Fix it, or skip the scan on purpose with --no-verify.", file=sys.stderr)
    sys.exit(1)


def outgoing():
    """The commits a push sends, as `git log -p` text, from pre-push's stdin."""
    parts = []
    for line in sys.stdin.read().splitlines():
        try:
            local_ref, local_sha, remote_ref, remote_sha = line.split()
        except ValueError:
            continue
        if local_sha == ZERO:
            continue                                    # a delete sends nothing
        rng = [local_sha, "--not", "--remotes"] if remote_sha == ZERO else [f"{remote_sha}..{local_sha}"]
        if not git("rev-list", *rng).strip():
            continue
        parts.append(git("log", "-p", "--no-color", "--submodule=short",
                         "--format=COMMIT %H%nMESSAGE:%n%B%nDIFF:", *rng))
    return "\n".join(parts)


def literals(text):
    path = os.environ.get("CCNIX_SENSITIVE") or os.path.expanduser("~/.config/ccnix-claude/sensitive.txt")
    if not os.path.exists(path):
        print(f"scan: no {path}: only the model checks (one regex per line there)", file=sys.stderr)
        return []
    hits = []
    for pat in open(path, encoding="utf-8").read().splitlines():
        pat = pat.strip()
        if not pat or pat.startswith("#"):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if re.search(pat, line):
                hits.append((pat, n, line.strip()[:160]))
    return hits


def cli():
    c = os.environ.get("CCNIX_CLAUDE") or shutil.which("claude")
    if c:
        return c
    found = glob.glob(os.path.expanduser("~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude*"))
    found = [f for f in found if os.path.basename(f) in ("claude", "claude.exe")]
    if found:
        return max(found, key=lambda f: [int(x) for x in re.findall(r"\d+", f.split("claude-code-")[1].split("-")[0])])
    fail("no Claude Code CLI found (set CCNIX_CLAUDE to it)")


def ask(text):
    claude, findings, cost = cli(), [], 0.0
    chunks = [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)] or [""]
    for i, chunk in enumerate(chunks, 1):
        r = subprocess.run(
            [claude, "-p", "--model", MODEL, "--tools", "", "--strict-mcp-config",
             "--no-session-persistence", "--output-format", "json",
             "--json-schema", json.dumps(SCHEMA), "--system-prompt", PROMPT,
             f"Review this text (part {i} of {len(chunks)}), given on stdin."],
            input=chunk, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        try:
            out = json.loads(r.stdout)
            got = out.get("structured_output") or json.loads(out.get("result") or "{}")
            findings += got["findings"]
            cost += out.get("total_cost_usd") or 0
        except Exception:
            fail(f"the model's answer couldn't be read (exit {r.returncode}): {(r.stderr or r.stdout)[:400]}")
    return findings, cost, len(chunks)


def main():
    if os.environ.get("CCNIX_SCAN", "").lower() == "off":
        return
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "commit":
        msg = open(sys.argv[2], encoding="utf-8").read()
        msg = "\n".join(l for l in msg.splitlines() if not l.startswith("#"))
        text = "MESSAGE:\n" + msg + "\nDIFF:\n" + git("diff", "--cached", "--no-color", "--submodule=short")
    elif mode == "push":
        text = outgoing()
    else:
        fail("usage: scan.py commit <message-file> | push")
    if not text.strip():
        return

    hits = literals(text)
    if hits:
        for pat, n, line in hits:
            print(f"scan: matches {pat!r}: {line}", file=sys.stderr)
        fail(f"{len(hits)} line(s) match the sensitive list")

    findings, cost, calls = ask(text)
    block = [f for f in findings if f["severity"] == "block"]
    for f in findings:
        print(f"scan: {f['severity']}: {f['where']}: {f['text']!r}: {f['why']}", file=sys.stderr)
    print(f"scan: {MODEL}, {calls} call(s), {len(findings)} finding(s), ~${cost:.3f} at API list prices", file=sys.stderr)
    if block:
        fail(f"{len(block)} finding(s) to fix before this is published")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        fail(f"git failed: {e.stderr.strip()[:300]}")
    except subprocess.TimeoutExpired:
        fail("the model took over 5 minutes")
