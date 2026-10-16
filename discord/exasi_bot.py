#!/usr/bin/env python3
"""exasi_bot.py — least-privilege Discord bot for the EXA-SI client server.

Scope (AGENTS.md directive 11 — EXA-SI is an external, client-owned server,
outside the org and the RSSI mandate):
  * READ one command channel, acting ONLY on messages from the authorized
    operator id — each is a PROPOSAL surfaced to the orchestrator, NEVER an
    autonomous offensive action (directive 2 / human-in-the-loop).
  * WRITE sanitized-by-intent engagement notifications to the client-dedicated
    channel — the ONE place engagement / pentest-in-progress info may go.
  * Before posting it VERIFIES the channel exists; if not, it ABORTS and reports,
    never publishing anywhere else.

stdlib only (no discord.py — jarvis directive 13), REST over https://discord.com.
Least-privilege: the bot is scoped on the server to the two channels; it needs
only View Channel + Read Message History (commands) and + Send Messages / Embed
Links (notifications). It performs NO offensive action and holds NO engagement
logic — it is a transport between the client channel and the orchestrator.

Config (env; redteam-agent/.env — see template.env):
    DISCORD_EXASI_BOT_TOKEN     bot token (secret; .env / Vaultwarden)
    EXASI_COMMANDS_CHANNEL_ID   channel the bot reads (operator commands)
    EXASI_NOTIFY_CHANNEL_ID     OPTIONAL default notify channel; the real target is
                                the engagement's channel, passed with --channel
    EXASI_AUTHORIZED_USER_ID    only this Discord user id is obeyed
    EXASI_POLL_INTERVAL         listen poll seconds (default 10)

Usage:
    discord/exasi_bot.py --verify [--channel ID]        # check channels are reachable
    discord/exasi_bot.py --notify TEXT [--channel ID]    # post to the engagement channel (exists-guard)
    discord/exasi_bot.py --listen                        # poll the command channel, surface proposals
    discord/exasi_bot.py --selftest                      # offline: validate guards + filters, no network

The bot is NOT restricted to a single channel: one client/engagement has one
channel (scope.md `exasi_channel`), passed with --channel per engagement.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://discord.com/api/v10"
UA = "redteam-agent-exasi (https://pirates.re, 0.1)"
MAX_CONTENT = 2000  # Discord message hard limit

# Injection point so --selftest can run the guard/filter logic without network.
# Signature: (method, path, token, body_or_None) -> (status:int, obj:dict|list|None)
_API_OVERRIDE = None


def _api(method: str, path: str, token: str, body=None):
    if _API_OVERRIDE is not None:
        return _API_OVERRIDE(method, path, token, body)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", "Bot " + token)
    req.add_header("User-Agent", UA)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            obj = json.loads(raw) if raw else None
        except ValueError:
            obj = None
        return e.code, obj


class Config:
    def __init__(self, env=None):
        env = env if env is not None else os.environ
        self.token = env.get("DISCORD_EXASI_BOT_TOKEN", "")
        self.commands = env.get("EXASI_COMMANDS_CHANNEL_ID", "")
        self.notify = env.get("EXASI_NOTIFY_CHANNEL_ID", "")
        self.authorized = env.get("EXASI_AUTHORIZED_USER_ID", "")
        try:
            self.interval = max(5, int(env.get("EXASI_POLL_INTERVAL", "10")))
        except ValueError:
            self.interval = 10

    def missing(self, *names) -> list[str]:
        return [n for n in names if not getattr(self, n)]


def channel_exists(cid: str, token: str) -> bool:
    """True iff GET /channels/<cid> succeeds (the directive-11 pre-post guard)."""
    if not cid:
        return False
    status, _ = _api("GET", "/channels/%s" % cid, token)
    return status == 200


def post_notify(cfg: Config, text: str, channel_id: str | None = None) -> bool:
    """Post an engagement notification to a client channel — after verifying it exists.

    The target is the ENGAGEMENT's channel (scope.md `exasi_channel`), passed per
    call; `channel_id` wins, else the optional default `EXASI_NOTIFY_CHANNEL_ID`.
    There is no single fixed channel — one client/engagement, one channel
    (directive 11). Returns True on success. If the channel does not exist, it
    ABORTS and reports, never publishing anywhere else.
    """
    if cfg.missing("token"):
        print("exasi_bot: cannot notify — missing token", file=sys.stderr)
        return False
    target = channel_id or cfg.notify
    if not target:
        print("exasi_bot: no target channel — pass --channel <id> (the engagement's "
              "exasi_channel) or set EXASI_NOTIFY_CHANNEL_ID.", file=sys.stderr)
        return False
    if not channel_exists(target, cfg.token):
        print("exasi_bot: channel %s not found — ABORTING post (directive 11); "
              "nothing published anywhere else." % target, file=sys.stderr)
        return False
    content = text if len(text) <= MAX_CONTENT else text[:MAX_CONTENT - 1] + "…"
    status, obj = _api("POST", "/channels/%s/messages" % target, cfg.token,
                       {"content": content})
    if status in (200, 201):
        print("exasi_bot: notification posted to %s" % target)
        return True
    print("exasi_bot: post failed (HTTP %s): %s" % (status, (obj or {}).get("message", "")),
          file=sys.stderr)
    return False


def fetch_proposals(cfg: Config, after: str | None):
    """Return (new_after, [(id, content)]) for messages from the AUTHORIZED user
    only. These are PROPOSALS — the bot never executes them (HITL, directive 2)."""
    if not cfg.authorized:
        print("exasi_bot: EXASI_AUTHORIZED_USER_ID unset — refusing to treat any "
              "message as a command.", file=sys.stderr)
        return after, []
    path = "/channels/%s/messages?limit=50" % cfg.commands
    if after:
        path += "&after=%s" % after
    status, msgs = _api("GET", path, cfg.token)
    if status != 200 or not isinstance(msgs, list):
        print("exasi_bot: cannot read commands channel (HTTP %s)" % status, file=sys.stderr)
        return after, []
    # Discord returns newest-first; process oldest-first and track the max id.
    out = []
    new_after = after
    for m in sorted(msgs, key=lambda x: int(x.get("id", "0"))):
        mid = m.get("id")
        author = (m.get("author") or {})
        if author.get("bot"):
            continue
        if str(author.get("id")) != str(cfg.authorized):
            continue  # not from the authorized operator — ignored
        out.append((mid, m.get("content", "")))
        new_after = mid
    return new_after, out


# ----------------------------------------------------------------- commands

def cmd_verify(cfg: Config, channel_id: str | None = None) -> int:
    if cfg.missing("token"):
        print("exasi_bot: DISCORD_EXASI_BOT_TOKEN unset", file=sys.stderr)
        return 2
    ok = True
    # commands channel is required; notify is per-engagement (the one passed with
    # --channel, else the optional default), so it is only checked when present.
    checks = [("commands", cfg.commands, True)]
    tgt = channel_id or cfg.notify
    if tgt:
        checks.append(("notify", tgt, True))
    for label, cid, required in checks:
        if not cid:
            print("  %-9s channel: UNSET%s" % (label, "" if not required else " (required)"))
            ok = ok and not required
            continue
        exists = channel_exists(cid, cfg.token)
        print("  %-9s channel %s: %s" % (label, cid, "OK" if exists else "NOT FOUND"))
        ok = ok and exists
    print("exasi_bot: verify %s" % ("OK" if ok else "FAILED"))
    return 0 if ok else 1


def cmd_notify(cfg: Config, text: str, channel_id: str | None = None) -> int:
    return 0 if post_notify(cfg, text, channel_id) else 1


def cmd_listen(cfg: Config) -> int:
    miss = cfg.missing("token", "commands", "authorized")
    if miss:
        print("exasi_bot: cannot listen — missing %s" % ", ".join(miss), file=sys.stderr)
        return 2
    print("exasi_bot: listening on channel %s (authorized=%s, every %ds). "
          "Proposals are surfaced, never executed (HITL)."
          % (cfg.commands, cfg.authorized, cfg.interval))
    after = None
    # Prime `after` to "now" so we only react to new messages.
    after, _ = fetch_proposals(cfg, after)
    while True:
        after, props = fetch_proposals(cfg, after)
        for mid, content in props:
            print("exasi_bot: PROPOSAL from operator (msg %s): %s" % (mid, content))
            print("  -> relayed to the orchestrator; NOT executed by the bot "
                  "(directive 2 / engagement gate applies).")
        time.sleep(cfg.interval)


def _selftest() -> int:
    """Offline checks of the guards/filters with a mocked API — no network."""
    global _API_OVERRIDE
    results = []

    def check(name, cond):
        results.append((name, bool(cond)))

    # 1) post_notify aborts when the channel does not exist.
    calls = {"posted": 0}

    def fake_missing(method, path, token, body):
        if method == "GET" and path.startswith("/channels/"):
            return 404, {"message": "Unknown Channel"}
        if method == "POST":
            calls["posted"] += 1
            return 200, {"id": "1"}
        return 400, None

    _API_OVERRIDE = fake_missing
    cfg = Config({"DISCORD_EXASI_BOT_TOKEN": "x", "EXASI_NOTIFY_CHANNEL_ID": "999"})
    r = post_notify(cfg, "hello")
    check("post aborts when channel missing", r is False and calls["posted"] == 0)

    # 2) post_notify succeeds + truncates when the channel exists.
    sent = {}

    def fake_ok(method, path, token, body):
        if method == "GET" and path.startswith("/channels/"):
            return 200, {"id": "999", "type": 0}
        if method == "POST":
            sent["content"] = body["content"]
            return 201, {"id": "2"}
        return 400, None

    _API_OVERRIDE = fake_ok
    r = post_notify(cfg, "y" * 5000)
    check("post ok when channel exists", r is True)
    check("content truncated to limit", len(sent.get("content", "")) <= MAX_CONTENT)

    # 3) fetch_proposals obeys ONLY the authorized user and skips bots.
    def fake_msgs(method, path, token, body):
        return 200, [
            {"id": "10", "author": {"id": "AUTH", "bot": False}, "content": "recon please"},
            {"id": "11", "author": {"id": "SOMEONE", "bot": False}, "content": "rm things"},
            {"id": "12", "author": {"id": "AUTH", "bot": True}, "content": "echo"},
        ]

    _API_OVERRIDE = fake_msgs
    cfg2 = Config({"DISCORD_EXASI_BOT_TOKEN": "x", "EXASI_COMMANDS_CHANNEL_ID": "1",
                   "EXASI_AUTHORIZED_USER_ID": "AUTH"})
    _, props = fetch_proposals(cfg2, None)
    check("only authorized-user messages surface", [c for _, c in props] == ["recon please"])

    # 4) with no authorized id, nothing is ever treated as a command.
    cfg3 = Config({"DISCORD_EXASI_BOT_TOKEN": "x", "EXASI_COMMANDS_CHANNEL_ID": "1"})
    _, props3 = fetch_proposals(cfg3, None)
    check("no authorized id -> no commands", props3 == [])

    _API_OVERRIDE = None
    ok = all(p for _, p in results)
    for name, passed in results:
        print("  [%s] %s" % ("PASS" if passed else "FAIL", name))
    print("exasi_bot: selftest %s" % ("OK" if ok else "FAILED"))
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip().splitlines()[0])
        print("usage: exasi_bot.py --verify | --notify TEXT | --listen | --selftest",
              file=sys.stderr)
        return 2
    if argv[0] == "--selftest":
        return _selftest()
    cfg = Config()
    # Optional --channel <id> (the engagement's exasi_channel) for verify/notify.
    channel_id = None
    rest = list(argv)
    if "--channel" in rest:
        i = rest.index("--channel")
        if i + 1 >= len(rest):
            print("exasi_bot: --channel needs an id", file=sys.stderr)
            return 2
        channel_id = rest[i + 1]
        del rest[i:i + 2]
    if rest[0] == "--verify":
        return cmd_verify(cfg, channel_id)
    if rest[0] == "--notify":
        if len(rest) < 2:
            print("exasi_bot: --notify needs TEXT", file=sys.stderr)
            return 2
        return cmd_notify(cfg, " ".join(rest[1:]), channel_id)
    if rest[0] == "--listen":
        return cmd_listen(cfg)
    print("exasi_bot: unknown command %r" % argv[0], file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
