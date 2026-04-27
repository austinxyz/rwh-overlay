# kb-sync

Build the merged stock knowledge base from upstream (rwh) + overlay into `../stock-kb/`.

`stock-kb` is a plain output directory (no git) — it is always regenerated from rwh + rwh-overlay.

## Arguments

Optional: `--skip-pull` — skip the `git pull` on the upstream rwh repo (useful offline or when upstream hasn't changed).

## Steps

### 1. Run the build script

```bash
py scripts/build_stock_kb.py $ARGUMENTS
```

If the script exits non-zero, stop immediately and show the error output. Do not proceed.

### 2. Confirm completion

Report the summary line from the build output (tickers count, output path), then:

"KB 同步完成：`../stock-kb/` 已重新生成。"
