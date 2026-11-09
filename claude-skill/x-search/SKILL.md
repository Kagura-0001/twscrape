---
name: x-search
description: Search X (Twitter) posts and read tweet threads/replies from the terminal, using the user's own X login copied from Chrome. Use when the user wants views, anecdotes or announcements from X/Twitter (e.g. what researchers say about a conference, a paper, a policy), or gives an x.com/twitter.com status link to read.
---

# x-search

`~/.claude/skills/x-search/x.py <command>` is a uv script; it fetches its own `cryptography` dependency. It wraps the user's twscrape fork (https://github.com/Kagura-0001/twscrape), which calls X's web API as the user's logged-in account. twscrape telemetry is turned off. If `twscrape` is missing, the fork's `claude-skill/install.sh` installs it and links this skill.

## Reading

- `x.py search "QUERY" [--limit 20] [--full]` returns the newest matching tweets with date, author, likes/retweets/replies, link and text. X search operators work in the query. Add `min_faves:20` to skip low-signal posts. `from:user`, `lang:en`, `since:2026-11-01` and `"exact phrase"` also work.
- `x.py thread <id|url>` prints a tweet and its thread. `x.py replies <id|url>` prints the replies.

This runs on the user's real account, so search like a person reading. Use a few targeted queries (fewer than about 15 per task) and read the threads that matter; never loop or bulk-scrape. Never post, like, follow or DM: this skill is read-only.

## Login

`x.py login` reads the `auth_token` and `ct0` cookies for x.com from Chrome's Default profile. It decrypts them with the Chrome Safe Storage key from the macOS Keychain, so macOS shows a Keychain prompt that the user must Allow. It then saves them to `~/.config/x-search/accounts.db` (mode 600) and never prints the values.

Have the user run it themselves with `! ~/.claude/skills/x-search/x.py login`, after they have logged in at x.com in Chrome. On a machine without macOS Chrome, use `x.py login --paste`: the user pastes `auth_token=...; ct0=...` from x.com DevTools at a hidden prompt. Rerun login whenever a command says the login expired.
