# rwh-overlay Architecture Design

**Date**: 2026-04-23
**Owner**: austinxyz
**Status**: Draft, awaiting user review

---

## Spec Location Note

This file is written to `personal/rwh/docs/superpowers/specs/` temporarily for
review. The `personal/rwh/` directory will be classified as a **read-only
upstream mirror** of `kgajjala/rwh` (see Section 4), so this spec will migrate
to `rwh-overlay/docs/superpowers/specs/` as part of the first overlay commit
(migration step 6). It is intentionally left uncommitted in rwh.

---

## 1. Problem Statement

The user has three types of investment-analysis content that currently collide
in one directory:

1. **Upstream framework and analyses** maintained by `kgajjala/rwh` (BKNG, LLY,
   WING, UNH, SCHW, etc.), which the user wants to keep pulling updates from
   without ever editing.
2. **Personal ticker analyses** the user authors using the upstream framework
   (currently NVTS, OKLO, POET, WOLF; more to come).
3. **Third-party observations** from Yun Chen's WeChat group, curated into
   structured opinions (`wiki/opinions/chen-yun.md`, sourced from
   `raw/analyses/chen.md`).

These three content streams need to be published as **one unified stock
knowledge base** in the user's existing Quartz v4 site
(`austinxyz/second-brain`), while source attribution is preserved and upstream
updates never conflict with personal edits.

## 2. Goals

- **G1** Upstream remains pristine. Only `git pull` against kgajjala/rwh; zero
  local commits into it.
- **G2** Personal content lives in a single owned GitHub repo
  (`austinxyz/rwh-overlay`) with clean git history.
- **G3** Quartz presents one unified Tickers tree, with a source badge
  (`[Upstream]` / `[Austin]` / `[Chen via Austin]`) on each page.
- **G4** The merge mechanism is a local build script; Quartz itself is not
  modified. Syncthing transparently carries the built artifact to the NAS
  Docker container.
- **G5** Adding a new ticker, updating an existing overlay ticker, or pulling
  upstream updates is a single-digit-step operation.

## 3. Non-Goals (YAGNI)

- **NG1** No automated OCR / scraping pipeline for Chen's WeChat screenshots.
  Chen's content is manually curated (low frequency, high judgment).
- **NG2** No extension mechanism for upstream tickers (e.g., appending a
  section to upstream `BKNG/thesis.md`). If the user wants to modify an
  upstream ticker, the policy is "PR upstream or write your own complete
  replacement in overlay" — no auto-merging of fragments.
- **NG3** No multi-user collaboration. Overlay is single-maintainer.
- **NG4** No Quartz v4 plugin changes. The existing `kbLinkRewrite.ts` stays
  as-is; all merging happens at the content-build layer upstream of Quartz.

## 4. Architectural Decisions (D1–D9)

Each decision is numbered as discussed during brainstorming. Chosen option is
marked **(✓)**; rationale follows each.

### D1: Overlay uses same `wiki/tickers/` path as upstream — not a renamed path
- **(✓) (a)** `rwh-overlay/wiki/tickers/NVTS/` — matches upstream structure;
  merge is a simple `shutil.copytree`.
- (b) `rwh-overlay/wiki/my-tickers/NVTS/` — rejected. Introduces name-rewriting
  in the build script; D4's `--ignore-existing` policy already prevents
  accidental overwrite.

### D2: No git submodule
- **(✓) (a)** `rwh` and `rwh-overlay` are independent sibling clones. Build
  script finds them via relative paths (configurable by env vars).
- (b) Submodule — rejected. Each upstream pull would force a submodule-pointer
  bump commit in overlay; noisy history for no real benefit.

### D3: `stock-kb/` lives as a sibling of the two repos
- **(✓) (a)** `~/projects/personal/stock-kb/`.
- (b) Other Syncthing path — user may redirect via env var.
- (c) Inside overlay repo with gitignore — rejected (too easy to accidentally
  commit build artifacts).

### D4: Overlay does not go through Syncthing
- **(✓) (a)** Overlay's authoritative sync is git (local ↔ GitHub). Only
  `stock-kb/` is in Syncthing scope.
- (b) Rejected. Mixing git and Syncthing on the same directory creates
  conflict-resolution ambiguity.

### D5: Frontmatter source values
- **(✓) (a)** `source: upstream` / `source: austin` / `source: austin-observation`
- (b) GitHub handles (`source: kgajjala` / `source: austinxyz`) — rejected as
  less portable (couples content metadata to identity that can change).

### D6: Build stack is pure Python
- **(✓) (b)** `scripts/build_stock_kb.py` orchestrates and performs all
  file-tree operations (`shutil.copytree` with `dirs_exist_ok`, manual walk
  for `--ignore-existing` semantics). Helper modules handle frontmatter
  injection and derived file generation (needs `python-frontmatter`).
  **Revision history**: originally (a) bash + rsync + python, but rsync is
  not available in the user's Windows `git-bash` environment and Scoop's
  `main` bucket failed to provide it reliably. Pure Python eliminates the
  external dependency and makes the pipeline trivially cross-platform.
- (a) bash + rsync + python — rejected; rsync unavailable on Windows
  git-bash, and the one-time setup friction isn't worth the semantic purity.
- (c) TypeScript — rejected (over-tooled for a file-tree merge).

### D7: `personal/rwh/` stays in place, with a pre-commit hook guard
- **(✓) (a) + (c)** Keep `personal/rwh/` as the upstream mirror dir; add
  `.git/hooks/pre-commit` that aborts any commit attempt with an explanatory
  message. Protects against muscle-memory commits.
- (b) Rename/move — rejected (churn for no real gain).

### D8: `raw/analyses/chen.md` is committed to overlay git
- **(✓) (a)** Commit it. Assumes `austinxyz/rwh-overlay` is a **private**
  GitHub repo. Enables version history of Chen's evolving picks.
- (b) gitignore — available as fallback if Chen's content becomes sensitive.
- (c) Deferred folder pattern — unnecessary for now.

### D9: Claude Code's working directory for ticker work is always `rwh-overlay/`
- **(✓) (a)** Explicit. CLAUDE.overlay.md instructs Claude to read
  `../rwh/CLAUDE.md` and `../rwh/wiki/frameworks/` for framework reference but
  write only inside the overlay repo.
- (b) Allow working from `rwh/` with write-guard — rejected (weaker invariant;
  build script's `--ignore-existing` is a backstop, not the primary fence).

## 5. Three-Repo Topology

```
┌──────────────────────────────┐     ┌──────────────────────────────┐
│   kgajjala/rwh (upstream)    │     │ austinxyz/rwh-overlay        │
│   — read-only mirror         │     │   (private, user-owned)      │
│                              │     │                              │
│   wiki/tickers/{BKNG,LLY,..} │     │ wiki/tickers/{NVTS,OKLO,..}  │
│   wiki/frameworks/           │     │ wiki/opinions/chen-yun.md    │
│   CLAUDE.md                  │     │ raw/analyses/chen.md         │
│                              │     │ CLAUDE.overlay.md            │
│   Pull-only (G1)             │     │ scripts/build_stock_kb.py    │
└──────────────┬───────────────┘     └──────────────┬───────────────┘
               │                                     │
               └──────────────┬──────────────────────┘
                              ▼
              ┌─────────────────────────────────┐
              │   build_stock_kb.py (local)     │
              │   Merges both trees,            │
              │   injects source frontmatter,   │
              │   generates derived files       │
              └───────────────┬─────────────────┘
                              ▼
              ┌─────────────────────────────────┐
              │   ~/projects/personal/stock-kb/ │
              │   (derived, not in any git)     │
              │   ← Syncthing source            │
              └───────────────┬─────────────────┘
                              ▼
              NAS: /volume1/docker/stock/content/wiki
                              ▼
              Docker container mount (read-only)
                              ▼
              Quartz renders → one unified stock KB
```

## 6. Physical Directory Layout

```
~/projects/personal/
├── rwh/                              ← git clone kgajjala/rwh (read-only)
│   ├── wiki/tickers/{BKNG,LLY,..}/
│   ├── wiki/frameworks/
│   ├── CLAUDE.md                     ← upstream framework (do not edit)
│   └── .git/hooks/pre-commit         ← guard: block commits (see Appendix A)
│
├── rwh-overlay/                      ← git clone austinxyz/rwh-overlay (new)
│   ├── wiki/
│   │   ├── tickers/
│   │   │   ├── NVTS/{overview,thesis,financials,changelog}.md
│   │   │   ├── OKLO/...
│   │   │   ├── POET/...
│   │   │   └── WOLF/...
│   │   └── opinions/
│   │       └── chen-yun.md
│   ├── raw/
│   │   └── analyses/
│   │       └── chen.md               ← manual Chen observation log
│   ├── scripts/
│   │   ├── build_stock_kb.py         ← orchestrator
│   │   ├── inject_frontmatter.py     ← adds source: field to .md files
│   │   ├── gen_index.py              ← derives wiki/index.md
│   │   ├── gen_watchlist.py          ← derives wiki/watchlist.md
│   │   └── merge_log.py              ← combines two log.md into one
│   ├── docs/superpowers/specs/       ← this spec lives here post-migration
│   ├── overlay-log.md                ← your own operation log (raw input)
│   ├── CLAUDE.overlay.md             ← overlay-specific rules
│   ├── README.md
│   └── .gitignore
│
└── stock-kb/                         ← derived build output (not in any git)
    ├── wiki/
    │   ├── tickers/                  ← merged tree
    │   │   ├── BKNG/...              ← source: upstream
    │   │   ├── NVTS/...              ← source: austin
    │   │   └── ...
    │   ├── opinions/chen-yun.md      ← source: austin-observation
    │   ├── frameworks/               ← source: upstream
    │   ├── index.md                  ← generated
    │   ├── watchlist.md              ← generated
    │   └── log.md                    ← merged from both sides
    ├── raw/analyses/chen.md          ← copied from overlay (for completeness)
    ├── CLAUDE.upstream.md            ← copied from rwh/CLAUDE.md
    └── CLAUDE.overlay.md             ← copied from overlay
```

## 7. Build Pipeline Semantics

### 7.1 `scripts/build_stock_kb.py`

**Inputs** (all overridable via env vars or CLI flags):
- `RWH_DIR` (default: `../rwh`)
- `OVERLAY_DIR` (default: `.`, i.e., the overlay repo itself)
- `OUTPUT_DIR` (default: `../stock-kb`)
- `SKIP_PULL` (default false; tests use it to bypass `git pull`)

**Steps** (all implemented in Python stdlib + `python-frontmatter`):

1. **Pull upstream**: `subprocess.run(["git", "-C", RWH_DIR, "pull", "--ff-only", "origin", "main"])`
2. **Clean output**: `shutil.rmtree(OUTPUT_DIR/"wiki", ignore_errors=True)`
   and recreate.
3. **Copy upstream into output**:
   `shutil.copytree(RWH_DIR/"wiki", OUTPUT_DIR/"wiki", dirs_exist_ok=True,
   ignore=shutil.ignore_patterns("index.md", "watchlist.md", "log.md"))`
4. **Tag upstream files**: walk `$OUTPUT_DIR/wiki/` for `*.md`, call
   `inject_frontmatter.inject(path, "upstream")` (idempotent).
5. **Copy overlay with "ignore-existing" semantics**: walk
   `$OVERLAY_DIR/wiki/`; for each file, copy to output only if the
   destination does not already exist. Record any skipped overlay-shadow
   attempts and emit a warning listing them at the end. This is the
   enforcement point for decision Q4-A.
6. **Tag overlay-originated files**: for each `.md` path that was copied in
   step 5, call `inject_frontmatter.inject(dest_path, "austin")` (or
   `"austin-observation"` for paths under `opinions/`). Because the
   injector is idempotent, files shadowed by an upstream equivalent keep
   their `source: upstream` tag.
7. **Copy raw**:
   `shutil.copytree(OVERLAY_DIR/"raw", OUTPUT_DIR/"raw", dirs_exist_ok=True)`
   (upstream's `raw/` holds only `.gitkeep` placeholders; skip).
8. **Copy CLAUDE**:
   `shutil.copy(RWH_DIR/"CLAUDE.md", OUTPUT_DIR/"CLAUDE.upstream.md")`
   and the overlay counterpart to `CLAUDE.overlay.md`.
9. **Generate derived files** via imported helper modules:
   - `gen_index.generate(OUTPUT_DIR/"wiki", OUTPUT_DIR/"wiki/index.md")`
   - `gen_watchlist.generate(OUTPUT_DIR/"wiki", OUTPUT_DIR/"wiki/watchlist.md")`
   - `merge_log.generate(RWH_DIR/"wiki/log.md", OVERLAY_DIR/"overlay-log.md", OUTPUT_DIR/"wiki/log.md")`
10. **Report**: print counts of upstream / overlay tickers, Chen update date,
    stale tickers (>90 days since last financials update), and any shadow
    attempts caught in step 5.

**Helper modules** (importable from the orchestrator, each also runnable as a
CLI for unit testing):

- `inject_frontmatter.py` — exposes `inject(path: Path, source: str) -> bool`
- `gen_index.py` — exposes `generate(wiki_root: Path, output: Path) -> None`
- `gen_watchlist.py` — exposes `generate(wiki_root: Path, output: Path) -> None`
- `merge_log.py` — exposes `generate(upstream: Path, overlay: Path, output: Path) -> None`

### 7.2 Derived-file generators

- **`gen_index.py`**: scans `wiki/tickers/*/overview.md` frontmatter; groups
  by `source`; renders two tables (Upstream, Austin) with ticker + one-line
  summary + last-updated date.
- **`gen_watchlist.py`**: scans each ticker's `changelog.md` latest entry;
  extracts conviction / action / price-target delta; renders a sorted table.
  Unchanged from upstream's current watchlist format, but now automated.
- **`merge_log.py`**: reads the two log sources, preserves the existing code
  fence wrapping (per CLAUDE.md rendering rule), interleaves entries by
  timestamp, writes to output.

### 7.3 Frontmatter contract

Every `.md` under `$OUTPUT_DIR/wiki/` carries at minimum:

```yaml
---
source: upstream | austin | austin-observation
ticker: NVTS            # optional, for ticker pages
updated: 2026-04-22
---
```

Quartz layout reads `source` and renders a badge in a post-layout slot.
(Exact Quartz wiring is deferred — the content-layer contract is defined here;
the Quartz template change is a small follow-on task.)

## 8. Migration Plan (one-time execution)

Performed once to transition from current mixed state into the target topology.

1. **(User)** Create empty GitHub repo `austinxyz/rwh-overlay` (private).
2. Initialize overlay locally:
   `mkdir ~/projects/personal/rwh-overlay && cd ~/projects/personal/rwh-overlay`
   `git init && git remote add origin git@github.com:austinxyz/rwh-overlay.git`
3. Move personal content from `rwh/` to `rwh-overlay/`:
   - `wiki/tickers/{NVTS,OKLO,POET,WOLF}/` → `rwh-overlay/wiki/tickers/`
   - `wiki/opinions/chen-yun.md` → `rwh-overlay/wiki/opinions/`
   - `raw/analyses/chen.md` → `rwh-overlay/raw/analyses/`
4. Extract user-authored edits from shared files:
   - `wiki/log.md` diff vs. upstream: harvest new LOG lines into
     `rwh-overlay/overlay-log.md`.
   - `CLAUDE.md` diff vs. upstream: harvest new rules into
     `rwh-overlay/CLAUDE.overlay.md`.
   - `wiki/index.md` / `wiki/watchlist.md`: **discard** (derived files; will
     be regenerated).
5. Restore `rwh/` to pristine upstream state:
   `cd ~/projects/personal/rwh && git checkout -- wiki/index.md wiki/log.md wiki/watchlist.md CLAUDE.md`
   Verify `git status` is clean (apart from `.claude/` / `.stignore` local
   files the user wants to keep).
6. First overlay commit:
   - Add this spec (move from `rwh/docs/superpowers/specs/` to
     `rwh-overlay/docs/superpowers/specs/`).
   - Add `README.md`, `CLAUDE.overlay.md`, `scripts/build_stock_kb.py`,
     helper Python scripts, `.gitignore`.
   - `git add . && git commit -m "Initial overlay migrated from local rwh workdir"`
   - `git push -u origin main`
7. First build: `cd ~/projects/personal/rwh-overlay && py scripts/build_stock_kb.py`
   Verify `~/projects/personal/stock-kb/` looks right.
8. Wire Syncthing: configure the Syncthing share on
   `~/projects/personal/stock-kb/` → NAS `/volume1/docker/stock/content/`.
   Back up the current NAS contents first if they're from a previous flow.
9. Install `rwh/.git/hooks/pre-commit` guard (see Appendix A).
10. Acceptance: load the Quartz site; verify:
    - Upstream tickers (BKNG, LLY, WING, UNH, SCHW, DASH, PG, RKT, SHOP) present with `[Upstream]` badge.
    - Overlay tickers (NVTS, OKLO, POET, WOLF) present with `[Austin]` badge.
    - `chen-yun.md` under opinions with `[Chen via Austin]` badge.
    - Cross-KB wikilinks still work (kbLinkRewrite.ts unaffected).

## 9. Day-to-Day Workflows

### 9.1 Upstream has new commits
Nothing manual. Next build (`py scripts/build_stock_kb.py`, either on-demand or
daily cron) pulls kgajjala/rwh, regenerates stock-kb, Syncthing propagates.

### 9.2 Add a new overlay ticker (e.g., PLTR)
- `cd ~/projects/personal/rwh-overlay`
- Claude generates `wiki/tickers/PLTR/{overview,thesis,financials,changelog}.md`
  following the upstream 15-section framework (read from `../rwh/CLAUDE.md`
  and `../rwh/wiki/frameworks/`).
- Claude appends one line to `overlay-log.md`.
- `py scripts/build_stock_kb.py`
- `git add . && git commit -m "Add PLTR thesis" && git push`

### 9.3 Update Chen observations
- Claude appends new dated block to `raw/analyses/chen.md`.
- Claude re-compiles relevant sections of `wiki/opinions/chen-yun.md` (merge,
  not overwrite).
- Claude appends one line to `overlay-log.md`.
- Build + commit + push as above.

### 9.4 Modify framework (user-specific rule additions)
Edit `CLAUDE.overlay.md` only. `rwh/CLAUDE.md` is never touched. The build
script copies both into the output; Claude loads both when working in
stock-kb context.

## 10. Open Questions / Future Work

- **Quartz badge rendering**: This spec defines the content-layer contract
  (`source` frontmatter). The Quartz-layer template change to render the
  badge is a small follow-on task, out of scope for this spec.
- **Automation cadence**: Whether to run the build on a post-commit git hook,
  a daily cron, or manually per session is a user-preference decision — all
  three work; starting with manual-per-session is lowest friction.
- **Ticker extension escape hatch**: If in 6 months the user finds themselves
  repeatedly wanting to append to upstream tickers (e.g., translation files,
  Q2 updates before kgajjala has processed them), revisit Q4 and consider a
  lightweight `_extensions/` merge mechanism (Option B from Q4). Defer until
  demand is proven.
- **Upstream PR flow**: If any of the user's additions (framework rules,
  ticker analyses) are general enough to contribute back, establish a PR flow
  to kgajjala. Not urgent.

## 11. Success Criteria

- [ ] `personal/rwh/` has no uncommitted changes after migration; any
  attempted commit is blocked by pre-commit hook.
- [ ] `austinxyz/rwh-overlay` exists, has an initial commit with all migrated
  personal content, and is pushed to GitHub.
- [ ] `py scripts/build_stock_kb.py` runs cleanly and produces
  `~/projects/personal/stock-kb/` in under 10 seconds.
- [ ] Quartz site shows all upstream and overlay tickers in one unified tree.
- [ ] Each page has a correct `source` frontmatter field.
- [ ] Pulling a new commit in `rwh/` and re-running the build reflects the
  new content in Quartz within one Syncthing cycle.

## Appendix A: rwh Pre-commit Hook

`~/projects/personal/rwh/.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "❌ ERROR: personal/rwh/ is a read-only upstream mirror."
echo "   Author your content in personal/rwh-overlay/ instead."
echo "   See docs/superpowers/specs/2026-04-23-rwh-overlay-architecture-design.md"
exit 1
```

`chmod +x` required. This is a soft guard — user can bypass with
`git commit --no-verify` if they ever need to, but it prevents muscle-memory
accidents.

## Appendix B: Example Minimal `.gitignore` for rwh-overlay

```
# Build artifacts
/build/
# Note: stock-kb/ lives as a sibling dir, not inside overlay,
# so it does not need a .gitignore entry here (D3-(a)).

# Local Claude state
.claude/settings.local.json

# Python
__pycache__/
*.pyc
.venv/

# OS
.DS_Store
Thumbs.db
```

`raw/analyses/chen.md` is deliberately **not** ignored (per D8-(a)).
