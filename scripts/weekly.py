"""Rewrite the "This week" block in README.md from GitHub and worklog.

Run from anywhere:  python3 scripts/weekly.py [--dry-run]
Covers the last full Monday-Sunday week (Asia/Tokyo). Only aggregate numbers leave this machine:
public repos are named, private repos are summed, and worklog contributes session counts and hours.
Never print an API response here; the launchd log is plain text on disk.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

LOGIN = "hakupao"
SELF_REPO = f"{LOGIN}/{LOGIN}"
TZ = ZoneInfo("Asia/Tokyo")
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- weekly:start -->", "<!-- weekly:end -->"
WORKLOG_ROOT = Path(os.environ.get("WORKLOG_ROOT", Path.home() / "Project/worklog"))
WORKLOG_CREDS = Path(os.environ.get("WORKLOG_HOME", Path.home() / ".worklog")) / "credentials.toml"
AGENT_NAMES = {"claude-code": "Claude Code", "codex": "Codex"}
MAX_PUBLIC = 4

QUERY = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){id
contributionsCollection(from:$from,to:$to){restrictedContributionsCount
commitContributionsByRepository(maxRepositories:100){repository{nameWithOwner name url isPrivate}contributions{totalCount}}}}}"""

# Commits by one author on a repository's default branch, within a time range.
BRANCH_QUERY = """query($owner:String!,$name:String!,$since:GitTimestamp!,$until:GitTimestamp!,$id:ID!){
repository(owner:$owner,name:$name){defaultBranchRef{target{... on Commit{
history(since:$since,until:$until,author:{id:$id}){totalCount}}}}}}"""


def last_week(today):
    end = today - timedelta(days=today.weekday() + 1)  # the Sunday before this week
    return end - timedelta(days=6), end


def toml_strings(path):
    """Top-level `key = "value"` pairs; enough for worklog's config.toml and credentials.toml."""
    pairs = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("["):
            break
        m = re.match(r'\s*([A-Za-z_]+)\s*=\s*"([^"]*)"', line)
        if m:
            pairs[m.group(1)] = m.group(2)
    return pairs


def graphql(query, **fields):
    gh = shutil.which("gh") or "/opt/homebrew/bin/gh"
    args = [gh, "api", "graphql", "-f", f"query={query}"]
    for key, value in fields.items():
        args += ["-f", f"{key}={value}"]
    out = subprocess.run(args, capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit("weekly: GitHub query failed (gh exit %d)" % out.returncode)
    return json.loads(out.stdout)["data"]


def default_branch_commits(name_with_owner, user_id, since, until):
    owner, name = name_with_owner.split("/", 1)
    ref = graphql(BRANCH_QUERY, owner=owner, name=name, since=since, until=until, id=user_id)["repository"]["defaultBranchRef"]
    return ref["target"]["history"]["totalCount"] if ref else 0


def github(start, end):
    since, until = f"{start.isoformat()}T00:00:00+09:00", f"{end.isoformat()}T23:59:59+09:00"
    user = graphql(QUERY, login=LOGIN, **{"from": since, "to": until})["user"]
    cc = user["contributionsCollection"]
    # GitHub reports private-repo work only as restrictedContributionsCount (commits, PRs, issues,
    # unnamed), even to the owner's gh token; a private repo that does come back named is summed in too.
    public, private = [], cc["restrictedContributionsCount"]
    for row in cc["commitContributionsByRepository"]:
        repo, n = row["repository"], row["contributions"]["totalCount"]
        if repo["nameWithOwner"] == SELF_REPO:
            continue
        if repo["isPrivate"]:
            private += n
            continue
        # A contribution count also includes commits on gh-pages, and glassbox publishes a snapshot
        # commit there every 10 minutes. Count the default branch only, so the number means work done.
        n = default_branch_commits(repo["nameWithOwner"], user["id"], since, until)
        if n:
            public.append((repo["name"], repo["url"], n))
    public.sort(key=lambda r: -r[2])
    return public, private


def worklog(start, end):
    api = toml_strings(WORKLOG_ROOT / "config.toml").get("api_url", "").rstrip("/")
    creds = toml_strings(WORKLOG_CREDS)
    if not api or not creds.get("api_token"):
        sys.exit("weekly: worklog api_url or api_token missing")
    req = urllib.request.Request(f"{api}/api/dashboard?from={start}&to={end}", headers={
        "Authorization": f"Bearer {creds['api_token']}",
        "CF-Access-Client-Id": creds.get("access_client_id", ""),
        "CF-Access-Client-Secret": creds.get("access_client_secret", ""),
        "Accept": "application/json",
        "User-Agent": "hakupao-profile-weekly",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            dash = json.load(resp)
    except Exception as e:  # the message only, never the body
        sys.exit(f"weekly: worklog request failed ({type(e).__name__} {getattr(e, 'code', '')})")
    # Whitelist: nothing else from the dashboard (task titles, requesters, summaries) is read.
    # overview.minutes also holds hand-logged note time, so hours come from the agents alone;
    # parallel sessions add up, hence "agent time" in the README rather than working hours.
    agents = [(AGENT_NAMES.get(a["agent"], a["agent"]), a["sessions"], a["minutes"])
              for a in dash["ai"]["by_agent"] if a["sessions"]]
    return agents, dash["overview"]["active_days"]


def render(start, end, public, private, agents, active_days):
    span = f"{start:%b %-d} – {end:%b %-d, %Y}"
    lines = [START, f'<sub>{span} · refreshed every Monday from GitHub and '
             f'<a href="https://github.com/hakupao/worklog-public">worklog</a></sub>', ""]
    if public:
        shown = ", ".join(f"[**{n}**]({u}) · {c}" for n, u, c in public[:MAX_PUBLIC])
        more = sum(c for *_, c in public[MAX_PUBLIC:])
        lines.append(f"- 📦 Public commits: {shown}" + (f", +{more} more" if more else ""))
    if private:
        lines.append(f"- 🔒 {private} contributions in private repos")
    if agents:
        sessions = sum(n for _, n, _ in agents)
        hours = sum(m for *_, m in agents) / 60
        split = " · ".join(f"{a} {n}" for a, n, _ in agents)
        lines.append(f"- 🤖 {sessions} AI agent sessions ({split}) · {hours:.0f} h of agent time over {active_days} days")
    if len(lines) == 3:
        lines.append("- A quiet week.")
    lines.append(END)
    return "\n".join(lines)


def main():
    start, end = last_week(datetime.now(TZ).date())
    block = render(start, end, *github(start, end), *worklog(start, end))
    if "--dry-run" in sys.argv:
        print(block)
        return
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        sys.exit("weekly: markers not found in README.md")
    README.write_text(pattern.sub(lambda _: block, text), encoding="utf-8")
    print(f"weekly: README updated for {start} – {end}")


if __name__ == "__main__":
    main()
