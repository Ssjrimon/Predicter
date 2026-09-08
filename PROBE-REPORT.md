# Diagnostic Probe Report

## git remote -v

```
origin	https://github.com/Ssjrimon/Predicter (fetch)
origin	https://github.com/Ssjrimon/Predicter (push)
```

## git config --list --show-origin | grep -iE 'url|credential|proxy|insteadof|extraheader'

```
file:/root/.gitconfig	http.proxyauthmethod=basic
file:.git/config	remote.origin.url=https://github.com/Ssjrimon/Predicter
command line:	credential.interactive=false
command line:	url.https://github.com/.insteadof=git@github.com:
command line:	url.https://github.com/.insteadof=ssh://git@github.com/
```

## git ls-remote origin main

```
2157c3097ad377424c1cd40a1115fbd9ae78f8f4	refs/heads/main
```

## git push --dry-run origin HEAD:refs/heads/main

```
Everything up-to-date
```

## python3 --version

```
Python 3.11.15
```

## cd natdef && python3 -m natdef status

```
ledger        /home/user/Predicter/natdef/intel-ledger.json
brief         13
cutoff        2026-09-06T19:30Z
updated       2026-09-07
revision      D — canonical; renderer-backed
contents      10 threads, 70 sources (10 current), 189 events, 31 horizon, 13 archive, 130 verification entries
node map      14 nodes, 20 edges, 17 archival entries
latest brief  2026-09-06 (Sunday) — daily-brief-2026-09-06.html
briefs/       13 delivered brief file(s) on disk
rendered      4/4 page(s) present
console       present, current
```

## cd natdef && python3 -m unittest discover -s tests -t . 2>&1 | tail -5

```
..................................................................................................................
----------------------------------------------------------------------
Ran 114 tests in 0.775s

OK
```

## TOOLS

- Web search tool available: WebSearch
- MCP tools available: Yes (mcp__github__ suite including subscribe_pr_activity, unsubscribe_pr_activity, create_pull_request, and 150+ additional MCP tools across various services including Figma, Zapier, Gmail, Google Drive, Spotify, etc.)
- Repository checkout status: Already checked out (did not require cloning)
