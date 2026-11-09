# x-search skill for Claude Code

This fork of [twscrape](https://github.com/vladkens/twscrape) also carries `x-search`, a read-only Claude Code skill. With it, Claude can search X and read threads as your own logged-in account.

## Install on a new machine

```sh
git clone https://github.com/Kagura-0001/twscrape ~/code/twscrape
~/code/twscrape/claude-skill/install.sh
```

The script installs the `twscrape` CLI from this checkout with `uv tool install --editable`, so a `git pull` updates it. It also links `claude-skill/x-search` to `~/.claude/skills/x-search`. It needs [uv](https://docs.astral.sh/uv/).

Then log in to x.com in Chrome and run:

```sh
~/.claude/skills/x-search/x.py login          # macOS: reads auth_token + ct0 from Chrome (click Allow on the Keychain prompt)
~/.claude/skills/x-search/x.py login --paste  # any OS: paste the two cookies from x.com DevTools at a hidden prompt
```

The session is saved in `~/.config/x-search/accounts.db` with mode 600. Cookie values are never printed, and twscrape telemetry is turned off.

## Use

```sh
~/.claude/skills/x-search/x.py search 'ICLR "AI review" min_faves:20' --limit 20
~/.claude/skills/x-search/x.py thread https://x.com/user/status/123
~/.claude/skills/x-search/x.py replies 123
```

## Keeping up with upstream

The skill lives only in `claude-skill/`, so upstream changes merge cleanly:

```sh
git fetch upstream && git merge upstream/main && git push
```
