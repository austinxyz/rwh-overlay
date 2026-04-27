# kb-sync

Build the merged stock knowledge base from upstream (rwh) + overlay, then report what changed and optionally commit to stock-kb.

## Arguments

Optional: `--skip-pull` — skip the `git pull` on the upstream rwh repo (useful offline or when upstream hasn't changed).

## Steps

### 1. Run the build script

```bash
py scripts/build_stock_kb.py $ARGUMENTS
```

If the script exits non-zero, stop immediately and show the error output. Do not proceed.

### 2. Show what changed

Run a git diff on the output repo to see what files were added, modified, or deleted:

```bash
git -C ../stock-kb diff --stat HEAD
```

If the output is empty (no changes), report: "KB 内容无变化 — 已是最新。" and stop here.

### 3. Ask to commit

Show the diff summary and ask the user:

"以上文件已更新至 `../stock-kb/`。是否提交并推送？（yes / no）"

Wait for an explicit response. If the user says no, stop here.

### 4. Commit and push

Stage all changes and commit:

```bash
git -C ../stock-kb add -A
git -C ../stock-kb commit -m "sync: rebuild from rwh-overlay $(date +%Y-%m-%d)"
git -C ../stock-kb push
```

If push fails, report the error and stop. Do not force push.

### 5. Confirm completion

Report: "KB 同步完成：`../stock-kb/` 已提交并推送。"
