#!/usr/bin/env python3
"""Find the user stories whose product code changed since they were analysed.

Every analysed story records the product commit it was checked against
(`code_commit`) and the code it depends on (`code_paths`, plus every
`path/file:line` reference in its text, e.g. in Open questions). This script
pulls the product repo, diffs each story's paths from its `code_commit` to
HEAD and reports what changed.

Stories whose code didn't change are marked as checked right away (their
`code_commit` moves to HEAD). Affected stories keep their old commit until
someone reviews the changes and runs `--mark`.

Usage:
    python3 scripts/code_impact.py                   # pull, report, mark unaffected stories
    python3 scripts/code_impact.py --no-pull         # same without git pull
    python3 scripts/code_impact.py --mark "<story path>" ...   # reviewed: move code_commit to HEAD

Standard library only.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from qase_sync import fm_list, fm_value, set_fm, split_frontmatter, story_files

PRODUCT = Path(__file__).resolve().parent.parent / ".product" / "tutti-frutti"
# `services/users-service/app/main.py:104`, `ui/src/hooks/useAuth.tsx` (inside backticks or parentheses)
REF = re.compile(r"\b((?:services|ui|proto|docs|scripts)/[\w.\-/]+\.\w+)(?::(\d+))?")


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", "-C", str(PRODUCT), *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.exit(f"error: git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def story_paths(frontmatter: str, body: str) -> tuple[list[str], dict[str, list[str]]]:
    """The story's code paths: `code_paths` plus files referenced in the text, with their line refs."""
    lines: dict[str, list[str]] = {}
    for path, line in REF.findall(body):
        lines.setdefault(path, [])
        if line and line not in lines[path]:
            lines[path].append(line)
    paths = list(dict.fromkeys(fm_list(frontmatter, "code_paths") + list(lines)))
    return paths, lines


def mark(path: Path, head: str) -> None:
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    path.write_text(f"---\n{set_fm(frontmatter, 'code_commit', head)}\n---\n{body}", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--no-pull", action="store_true", help="don't git pull the product repo first")
    ap.add_argument("--mark", nargs="+", type=Path, metavar="STORY",
                    help="the changes were reviewed: set code_commit of these stories to HEAD")
    args = ap.parse_args()

    if not args.no_pull and not args.mark:
        pulled = subprocess.run(["git", "-C", str(PRODUCT), "pull", "--ff-only", "--quiet"],
                                capture_output=True, text=True)
        if pulled.returncode != 0:
            print(f"warning: git pull failed, using the local copy ({pulled.stderr.strip()[:200]})")
    head = git("rev-parse", "--short", "HEAD")

    if args.mark:
        for path in args.mark:
            mark(path, head)
            print(f"{path.name}: code_commit = {head}")
        return

    print(f"product HEAD: {head} {git('log', '-1', '--format=%s (%cr)')}")
    for path in story_files():
        frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
        name = f"{path.name} ({fm_value(frontmatter, 'id')})"
        base = fm_value(frontmatter, "code_commit")
        paths, line_refs = story_paths(frontmatter, body)
        if not base:
            print(f"\n{name}: no code_commit, can't tell what changed (set it after the next analysis)")
            continue
        if subprocess.run(["git", "-C", str(PRODUCT), "cat-file", "-e", f"{base}^{{commit}}"],
                          capture_output=True).returncode:
            print(f"\n{name}: code_commit {base} is not in the product history (rebased?); review by hand")
            continue
        if base == head or git("rev-parse", "--short", base) == head:
            print(f"\n{name}: up to date ({head})")
            continue
        if not paths:
            print(f"\n{name}: no code_paths and no file references; can't tell what changed")
            continue

        commits = git("rev-list", "--count", f"{base}..HEAD")
        stat = git("diff", "--numstat", f"{base}..HEAD", "--", *paths)
        if not stat:
            mark(path, head)
            print(f"\n{name}: {commits} new commit(s), none touch its code → code_commit = {head}")
            continue

        print(f"\n{name}: changed since {base} ({commits} commit(s) in the repo):")
        for row in stat.splitlines():
            added, removed, file = row.split("\t")
            refs = ", ".join(f":{n}" for n in line_refs.get(file, []))
            print(f"  {file}  +{added} -{removed}" + (f"   referenced at {refs}" if refs else ""))
        log = git("log", "--format=%h %s", f"{base}..HEAD", "--", *paths)
        print("  commits:\n" + "\n".join("    " + line for line in log.splitlines()))


if __name__ == "__main__":
    main()
