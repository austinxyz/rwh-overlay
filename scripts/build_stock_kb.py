#!/usr/bin/env python3
"""Build the merged stock knowledge base from upstream (rwh) + overlay.

Pure-Python replacement for the original bash+rsync design (rsync was not
available on the user's Windows environment).

Env vars (with CLI-flag overrides):
  RWH_DIR      path to kgajjala/rwh clone           (default: ../rwh)
  OVERLAY_DIR  path to rwh-overlay clone            (default: this file's repo root)
  OUTPUT_DIR   path to emit the merged KB           (default: ../stock-kb)
  SKIP_PULL    if set, skip `git pull` on RWH_DIR   (useful in tests)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

DERIVED_FILES = {"index.md", "watchlist.md", "log.md"}


def env_path(name: str, default: Path) -> Path:
    val = os.environ.get(name)
    return Path(val).resolve() if val else default.resolve()


def preflight(rwh: Path, overlay: Path) -> None:
    if not (rwh / "wiki").is_dir():
        sys.exit(f"ERROR: RWH_DIR={rwh} does not contain wiki/")
    if not (overlay / "wiki").is_dir():
        sys.exit(f"ERROR: OVERLAY_DIR={overlay} does not contain wiki/")


def git_pull(rwh: Path) -> None:
    print("Pulling upstream (fast-forward only)...")
    subprocess.run(
        ["git", "-C", str(rwh), "pull", "--ff-only", "origin", "main"],
        check=True,
    )


def clean_output(output: Path) -> None:
    print(f"Cleaning {output}/wiki/...")
    if (output / "wiki").exists():
        shutil.rmtree(output / "wiki")
    (output / "wiki").mkdir(parents=True)
    (output / "raw").mkdir(parents=True, exist_ok=True)


def copy_tree_excluding_derived(src: Path, dst: Path) -> None:
    """Copy src -> dst recursively, skipping index.md/watchlist.md/log.md at any depth."""
    for root, _dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for name in files:
            if name in DERIVED_FILES:
                continue
            shutil.copy2(Path(root) / name, dst / rel / name)


def overlay_copy_with_skip(overlay_wiki: Path, output_wiki: Path) -> tuple[list[Path], list[Path]]:
    """Walk overlay/wiki; copy files only if destination is missing.

    Returns (copied_relpaths, skipped_relpaths). `skipped_relpaths` captures
    any overlay file that was shadowed by an upstream equivalent — the build
    surfaces these as warnings so the user can re-scope.
    """
    copied: list[Path] = []
    skipped: list[Path] = []
    for root, _dirs, files in os.walk(overlay_wiki):
        rel_dir = Path(root).relative_to(overlay_wiki)
        (output_wiki / rel_dir).mkdir(parents=True, exist_ok=True)
        for name in files:
            if name in DERIVED_FILES:
                continue
            rel = rel_dir / name
            src = Path(root) / name
            dst = output_wiki / rel
            if dst.exists():
                skipped.append(rel)
            else:
                shutil.copy2(src, dst)
                copied.append(rel)
    return copied, skipped


def run_injector(py: str, paths: list[Path], source: str) -> None:
    """Invoke inject_frontmatter.py with many paths in a single subprocess."""
    if not paths:
        return
    cmd = [py, str(SCRIPT_DIR / "inject_frontmatter.py"), "--source", source] + [str(p) for p in paths]
    subprocess.run(cmd, check=True)


def tag_all_upstream(py: str, output_wiki: Path) -> None:
    paths = [p for p in output_wiki.rglob("*.md")]
    print(f"Tagging {len(paths)} upstream files (source: upstream)...")
    run_injector(py, paths, "upstream")


def tag_overlay_copies(py: str, output_wiki: Path, copied: list[Path]) -> None:
    """Tag files that were freshly copied from the overlay (not shadowed)."""
    austin: list[Path] = []
    observation: list[Path] = []
    for rel in copied:
        if rel.suffix != ".md":
            continue
        abs_path = output_wiki / rel
        if not abs_path.is_file():
            continue
        if rel.parts and rel.parts[0] == "opinions":
            observation.append(abs_path)
        else:
            austin.append(abs_path)
    print(f"Tagging {len(austin)} overlay files as austin and {len(observation)} as austin-observation...")
    run_injector(py, austin, "austin")
    run_injector(py, observation, "austin-observation")


def copy_raw(overlay: Path, output: Path) -> None:
    if not (overlay / "raw").is_dir():
        return
    print("Copying overlay raw/...")
    shutil.copytree(overlay / "raw", output / "raw", dirs_exist_ok=True)


def copy_claude(rwh: Path, overlay: Path, output: Path) -> None:
    print("Copying CLAUDE instructions...")
    up = rwh / "CLAUDE.md"
    if up.is_file():
        shutil.copy2(up, output / "CLAUDE.upstream.md")
    ov = overlay / "CLAUDE.overlay.md"
    if ov.is_file():
        shutil.copy2(ov, output / "CLAUDE.overlay.md")


def generate_derived(py: str, rwh: Path, overlay: Path, output: Path) -> None:
    print("Generating index.md (en)...")
    subprocess.run([py, str(SCRIPT_DIR / "gen_index.py"),
                    "--wiki-root", str(output / "wiki"),
                    "--output", str(output / "wiki" / "index.md"),
                    "--lang", "en"], check=True)
    print("Generating index.zh.md...")
    subprocess.run([py, str(SCRIPT_DIR / "gen_index.py"),
                    "--wiki-root", str(output / "wiki"),
                    "--output", str(output / "wiki" / "index.zh.md"),
                    "--lang", "zh"], check=True)
    print("Generating watchlist.md (en)...")
    subprocess.run([py, str(SCRIPT_DIR / "gen_watchlist.py"),
                    "--wiki-root", str(output / "wiki"),
                    "--output", str(output / "wiki" / "watchlist.md"),
                    "--lang", "en"], check=True)
    print("Generating watchlist.zh.md...")
    subprocess.run([py, str(SCRIPT_DIR / "gen_watchlist.py"),
                    "--wiki-root", str(output / "wiki"),
                    "--output", str(output / "wiki" / "watchlist.zh.md"),
                    "--lang", "zh"], check=True)
    print("Merging log.md...")
    subprocess.run([py, str(SCRIPT_DIR / "merge_log.py"),
                    "--upstream", str(rwh / "wiki" / "log.md"),
                    "--overlay",  str(overlay / "overlay-log.md"),
                    "--output",   str(output / "wiki" / "log.md")], check=True)


def main() -> int:
    repo_root = SCRIPT_DIR.parent
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rwh-dir", type=Path, default=None)
    ap.add_argument("--overlay-dir", type=Path, default=None)
    ap.add_argument("--output-dir", type=Path, default=None)
    ap.add_argument("--skip-pull", action="store_true", default=False)
    args = ap.parse_args()

    rwh = (args.rwh_dir or env_path("RWH_DIR", repo_root.parent / "rwh")).resolve()
    overlay = (args.overlay_dir or env_path("OVERLAY_DIR", repo_root)).resolve()
    output = (args.output_dir or env_path("OUTPUT_DIR", repo_root.parent / "stock-kb")).resolve()
    skip_pull = args.skip_pull or bool(os.environ.get("SKIP_PULL"))

    print(f"RWH_DIR      = {rwh}")
    print(f"OVERLAY_DIR  = {overlay}")
    print(f"OUTPUT_DIR   = {output}")

    preflight(rwh, overlay)

    py = sys.executable

    if not skip_pull:
        git_pull(rwh)

    clean_output(output)
    print("Copying upstream wiki/ (excluding derived files)...")
    copy_tree_excluding_derived(rwh / "wiki", output / "wiki")
    tag_all_upstream(py, output / "wiki")

    print("Copying overlay wiki/ (skipping files that shadow upstream)...")
    copied, shadowed = overlay_copy_with_skip(overlay / "wiki", output / "wiki")
    tag_overlay_copies(py, output / "wiki", copied)

    copy_raw(overlay, output)
    copy_claude(rwh, overlay, output)
    generate_derived(py, rwh, overlay, output)

    ticker_count = sum(1 for p in (output / "wiki" / "tickers").iterdir() if p.is_dir()) \
        if (output / "wiki" / "tickers").is_dir() else 0
    print("Build complete.")
    print(f"   Total tickers:  {ticker_count}")
    print(f"   Output:         {output}")
    if shadowed:
        print("WARNING: Overlay files shadowed by upstream (kept upstream, skipped overlay):")
        for rel in shadowed:
            print(f"     - {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
