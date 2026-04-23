#!/usr/bin/env python3
"""Inject a `source` frontmatter key into one or more markdown files.

Idempotent: if `source:` is already set, the file is untouched.
"""
import argparse
import sys
from pathlib import Path

import frontmatter


def inject(path: Path, source: str) -> bool:
    """Return True if the file was modified, False if skipped."""
    text = path.read_text(encoding="utf-8")
    post = frontmatter.loads(text)
    if post.get("source"):
        return False
    post["source"] = source
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True,
                    choices=["upstream", "austin", "austin-observation"])
    ap.add_argument("paths", nargs="+", type=Path)
    args = ap.parse_args()

    for p in args.paths:
        if not p.is_file():
            print(f"skip (not a file): {p}", file=sys.stderr)
            continue
        if p.suffix != ".md":
            continue
        if inject(p, args.source):
            print(f"tagged {args.source}: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
