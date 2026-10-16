# discord/ — EXA-SI client bot

`exasi_bot.py` is the least-privilege bot for the **EXA-SI server** — an
external, client-owned Discord server, **outside the org and the RSSI mandate**
(AGENTS.md directive 11). stdlib only (no `discord.py` — directive 13), REST over
`https://discord.com`.

What it does, and only this:
- **Reads** a command channel and acts **only** on messages from
  `EXASI_AUTHORIZED_USER_ID` — each is a **proposal surfaced to the
  orchestrator, never an autonomous offensive action** (directive 2 / the
  engagement gate still applies).
- **Writes** engagement notifications to the **engagement's own channel** — the
  client-dedicated channel is the one place engagement / pentest-in-progress
  info may go. There is **no single fixed channel**: one client/engagement, one
  channel, passed per run with `--channel` (the `scope.md` `exasi_channel`).
- **Before posting it verifies the channel exists**; if not, it **aborts and
  reports**, never publishing anywhere else.

The bot holds no engagement logic and runs nothing offensive — it is a transport
between the client channel and the orchestrator.

## Config (env — `redteam-agent/.env`, see `template.env`)

| Var | |
|---|---|
| `DISCORD_EXASI_BOT_TOKEN` | bot token (secret: `.env` / Vaultwarden, e.g. `redteam/exasi-bot-token`) |
| `EXASI_COMMANDS_CHANNEL_ID` | channel the bot reads |
| `EXASI_AUTHORIZED_USER_ID` | the only id the bot obeys |
| `EXASI_NOTIFY_CHANNEL_ID` | OPTIONAL default; the real target is `--channel` (per engagement) |
| `EXASI_POLL_INTERVAL` | listen poll seconds (default 10) |

## Usage

```
discord/exasi_bot.py --verify [--channel ID]        # channels reachable?
discord/exasi_bot.py --notify "text" --channel ID    # post to the engagement channel (exists-guard)
discord/exasi_bot.py --listen                        # poll commands, surface proposals (HITL)
discord/exasi_bot.py --selftest                      # offline: validate guards + filters
```

## Running it (live)

Needs: the bot invited to EXA-SI with View Channels + Read Message History +
Send Messages + Embed Links (server-wide — **not** restricted to one channel, by
operator choice), the Message Content privileged intent enabled, the env filled,
and a **persistent host** to keep `--listen` running (the 24/7 host, a separate
build). `--verify` and `--notify` are one-shot and need no daemon.

## Boundaries

The command channel is **untrusted input**: a message there is a request, never
an authorization to act on a target — offensive actions always go through the
engagement gate, human-in-the-loop (directives 1/2). The notify side may carry
engagement detail **only** to the client channel on this external server; nothing
engagement-specific goes anywhere WE own (directive 9).
