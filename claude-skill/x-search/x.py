#!/usr/bin/env -S uv run --no-config --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["cryptography"]
# ///
"""x-search: search and read X (Twitter) with twscrape, using the X login already in Chrome.

  x.py login [--profile Default]      copy auth_token + ct0 from Chrome into twscrape (macOS; values never printed)
  x.py login --paste                  any OS: paste "auth_token=...; ct0=..." from x.com DevTools at a hidden prompt
  x.py search "QUERY" [--limit 20]    newest matching tweets (X search operators work: min_faves:20, from:, lang:, since:)
  x.py thread TWEET_ID_OR_URL         the tweet plus its thread
  x.py replies TWEET_ID_OR_URL        replies to a tweet
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
DB = Path(os.environ.get("X_SEARCH_DB", str(HOME / ".config/x-search/accounts.db")))
CHROME = HOME / "Library/Application Support/Google/Chrome"
TWS = shutil.which("twscrape") or str(HOME / ".local/bin/twscrape")
ENV = {**os.environ, "TWS_TELEMETRY": "0"}  # twscrape's anonymous telemetry off
NEEDED = ("auth_token", "ct0")


def chrome_cookies(profile):
    """Read and decrypt the x.com auth_token/ct0 cookies from a Chrome profile (macOS)."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    src = CHROME / profile / "Cookies"
    if not src.exists():
        sys.exit(f"no Chrome cookie database at {src}")
    pw = subprocess.run(
        ["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage"],
        capture_output=True, text=True,
    )
    if pw.returncode:
        sys.exit("could not read 'Chrome Safe Storage' from the Keychain (click Allow on the prompt)")
    key = hashlib.pbkdf2_hmac("sha1", pw.stdout.strip().encode(), b"saltysalt", 1003, 16)

    with tempfile.TemporaryDirectory() as d:  # copy: Chrome keeps the live DB locked
        tmp = Path(d) / "cookies.db"
        shutil.copy2(src, tmp)
        con = sqlite3.connect(str(tmp))
        row = con.execute("select value from meta where key='version'").fetchone()
        version = int(row[0]) if row else 0
        rows = con.execute(
            "select name, encrypted_value, value from cookies "
            "where host_key in ('.x.com', 'x.com') and name in (?, ?)",
            NEEDED,
        ).fetchall()
        con.close()

    out = {}
    for name, enc, plain in rows:
        if plain:
            out[name] = plain
            continue
        if enc[:3] != b"v10":
            continue
        dec = Cipher(algorithms.AES(key), modes.CBC(b" " * 16)).decryptor()
        pt = dec.update(enc[3:]) + dec.finalize()
        pt = pt[: -pt[-1]]  # PKCS7
        if version >= 24:  # newer Chrome prefixes a 32-byte domain hash
            pt = pt[32:]
        out[name] = pt.decode()
    return out


def pasted_cookies():
    import getpass

    raw = getpass.getpass("x.com cookies (auth_token=...; ct0=...): ")
    return dict(kv.strip().split("=", 1) for kv in raw.split(";") if "=" in kv)


def cmd_login(a):
    if not Path(TWS).exists():
        sys.exit("twscrape is not installed: run claude-skill/install.sh from the twscrape fork")
    if a.paste or sys.platform != "darwin":
        c, where = pasted_cookies(), "the pasted cookies"
    else:
        c, where = chrome_cookies(a.profile), f"Chrome profile '{a.profile}'"
    missing = [n for n in NEEDED if n not in c]
    if missing:
        sys.exit(f"{where} has no x.com login (missing {', '.join(missing)}). "
                 "Log in at https://x.com in Chrome, then rerun.")
    DB.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(DB.parent, 0o700)
    header = "; ".join(f"{k}={c[k]}" for k in NEEDED)
    r = subprocess.run([TWS, "--db", str(DB), "add_cookie", "chrome"],
                       input=header, text=True, capture_output=True, env=ENV)
    if r.returncode:
        sys.exit("twscrape add_cookie failed:\n" + r.stderr.strip()[-800:])
    os.chmod(DB, 0o600)
    print(f"ok: X login copied from {where} into {DB}")


def run_tws(args):
    if not DB.exists():
        sys.exit("no X login yet: run `x.py login` first")
    r = subprocess.run([TWS, "--db", str(DB), *args], capture_output=True, text=True, env=ENV)
    docs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    if r.returncode or (not docs and r.stderr.strip()):
        err = r.stderr.strip()[-800:]
        hint = "\n(login may have expired: log in to x.com in Chrome and run `x.py login`)" \
            if re.search(r"No account|inactive|401|403|locked", err, re.I) else ""
        sys.exit(f"twscrape failed:\n{err}{hint}")
    return docs


def tweet_id(s):
    m = re.search(r"status/(\d+)", s)
    return m.group(1) if m else s


def show(docs, width):
    if not docs:
        print("(no results)")
    for t in docs:
        u = t.get("user") or {}
        text = re.sub(r"\s+", " ", t.get("rawContent") or "").strip()
        if width and len(text) > width:
            text = text[:width] + "…"
        stats = f"♥{t.get('likeCount', 0)} ↻{t.get('retweetCount', 0)} 💬{t.get('replyCount', 0)}"
        print(f"{(t.get('date') or '')[:10]}  @{u.get('username', '?')}  {stats}  {t.get('url', '')}")
        print(f"  {text}")
        q = t.get("quotedTweet")
        if q:
            qt = re.sub(r"\s+", " ", q.get("rawContent") or "")[:200]
            print(f"  > quoting @{(q.get('user') or {}).get('username', '?')}: {qt}")
        print()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("login")
    s.add_argument("--profile", default="Default")
    s.add_argument("--paste", action="store_true", help="type the cookies instead of reading Chrome")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--full", action="store_true", help="don't truncate tweet text")
    for name in ("thread", "replies"):
        s = sub.add_parser(name)
        s.add_argument("tweet")
        s.add_argument("--limit", type=int, default=30)
        s.add_argument("--full", action="store_true")
    a = p.parse_args()

    if a.cmd == "login":
        return cmd_login(a)
    width = 0 if a.full else 400
    if a.cmd == "search":
        show(run_tws(["search", a.query, "--limit", str(a.limit)]), width)
    elif a.cmd == "thread":
        show(run_tws(["tweet_thread", tweet_id(a.tweet), "--limit", str(a.limit)]), width)
    elif a.cmd == "replies":
        show(run_tws(["tweet_replies", tweet_id(a.tweet), "--limit", str(a.limit)]), width)


if __name__ == "__main__":
    main()
