#!/usr/bin/env python3
"""Push the approved test cases of user stories to Qase.

A story's draft cases live in its `## Test cases` section (format: see
CLAUDE.md). Once the user sets `test_cases_approved: true` in the frontmatter,
this script pushes them: it creates the suite from `qase_suite` if it doesn't
exist (nested suites use a dot: "User & Auth.Logout"), creates the cases in one
bulk request, writes their keys into `qase_cases` (TF-2, TF-3, ...), sets
`status: analyzed` and removes the draft `## Test cases` section from the
story. From then on Qase is the source of truth for those cases.

Cases already in Qase (their IDs are in `qase_cases`, or a case with the same
title is in the target suite) are not created again but updated from the story:
fields, steps, and the suite, so changing `qase_suite` moves them. Re-running
is safe; pass --no-update to only create the missing cases.

Usage:
    python3 scripts/qase_sync.py --approved          # every approved story with draft cases
    python3 scripts/qase_sync.py "<story path>"      # one story (must be approved)
    python3 scripts/qase_sync.py "<story path>" --dry-run   # validate drafts, send nothing
    python3 scripts/qase_sync.py --sync              # match qase_cases to Qase (deleted/added)
    python3 scripts/qase_sync.py "<story path>" --show      # print the story's cases from Qase

Settings (read from `.env` in the vault root; real env vars take precedence):
    QASE_API_TOKEN   API token (Qase → Workspace settings → API tokens).
                     If it's missing, the script asks for it once and saves it to `.env`.
    QASE_PROJECT     project code (or pass --project), default TF. The project is
                     created in Qase if it doesn't exist yet.

Standard library only, no dependencies.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.qase.io/v1"
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
STORIES_DIR = ENV_FILE.parent / "user-stories"
DEFAULT_PROJECT = "TF"
PROJECT_TITLE = "Tutti Frutti"
# Allowed values of the Qase system fields, as written in the story. The numeric IDs are
# looked up in Qase at push time (GET /system_field), so nothing here depends on them.
FIELDS = {
    "severity": ["blocker", "critical", "major", "normal", "minor", "trivial"],
    "priority": ["high", "medium", "low"],
    "type": ["functional", "smoke", "regression", "security", "usability", "performance",
             "acceptance", "compatibility", "integration", "exploratory", "other"],
    "behavior": ["positive", "negative", "destructive"],
}
# Qase layer is derived from the case's Level; "both" means it ends up in an e2e (UI) test.
LAYER = {"api": "api", "ui": "e2e", "both": "e2e"}


# --- story parsing ---------------------------------------------------------

def split_frontmatter(text: str) -> tuple[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        sys.exit("error: story has no frontmatter")
    return m.group(1), text[m.end():]


def fm_value(frontmatter: str, key: str) -> str:
    m = re.search(rf"^{key}:[ \t]*(.*)$", frontmatter, re.M)
    return re.sub(r"\s+#.*$", "", m.group(1)).strip().strip("\"'") if m else ""


def parse_cases(body: str) -> list[dict]:
    m = re.search(r"^## Test cases[ \t]*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    if not m:
        sys.exit("error: story has no '## Test cases' section")

    cases = []
    for block in re.split(r"^### TC:[ \t]*", m.group(1), flags=re.M)[1:]:
        title, _, rest = block.partition("\n")
        case = {"title": title.strip(), "steps": []}
        field = None
        for line in rest.splitlines():
            fm = re.match(r"^- \*\*(.+?):\*\*[ \t]*(.*)$", line)
            sm = re.match(r"^\s+\d+\.\s+(.*)$", line)
            if fm:
                field = fm.group(1).strip().lower()
                if field != "steps":
                    case[field] = fm.group(2).strip()
            elif sm and field == "steps":
                case["steps"].append(sm.group(1).strip())
            elif line.strip() and field:
                # continuation line of a multi-line value
                if field == "steps" and case["steps"]:
                    case["steps"][-1] += " " + line.strip()
                else:
                    case[field] = (case.get(field, "") + "\n" + line.strip()).strip()
        cases.append(case)

    errors = []
    for c in cases:
        for key in ("description", "ac", "level", "severity", "priority", "type", "behavior", "expected result"):
            if not c.get(key):
                errors.append(f"'{c['title']}': missing **{key.capitalize()}**")
        if not c["steps"]:
            errors.append(f"'{c['title']}': no steps")
        for key, allowed in FIELDS.items():
            if c.get(key) and c[key].lower() not in allowed:
                errors.append(f"'{c['title']}': {key} '{c[key]}' is not one of {', '.join(allowed)}")
        if c.get("level") and c["level"].lower() not in LAYER:
            errors.append(f"'{c['title']}': level '{c['level']}' is not one of API, UI, both")
    titles = [c["title"] for c in cases]
    errors += [f"duplicate title '{t}'" for t in sorted({t for t in titles if titles.count(t) > 1})]
    if errors:
        sys.exit("error: invalid test cases:\n  " + "\n  ".join(errors))
    return cases


def to_qase(case: dict, story_id: str, suite_id: int | None, ids=None) -> dict:
    """`ids(field, value)` returns the Qase option ID; without it (dry run) values stay as text."""
    ids = ids or (lambda field, value: value)
    steps = [{"action": s, "position": i + 1} for i, s in enumerate(case["steps"])]
    steps[-1]["expected_result"] = case["expected result"]
    if case.get("test data"):
        steps[-1]["data"] = case["test data"]
    tags = [story_id, *re.findall(r"AC-\d+", case["ac"]), *case["level"].lower().replace("|", " ").split()]
    return {
        "title": case["title"],
        "description": case["description"],
        "preconditions": case.get("preconditions", ""),
        **{key: ids(key, case[key].lower()) for key in FIELDS},
        "layer": ids("layer", LAYER[case["level"].lower()]),
        "suite_id": suite_id,
        "tags": tags,
        "steps": steps,
    }


# --- Qase API --------------------------------------------------------------

def call(method: str, path: str, token: str, body: dict | None = None, query: dict | None = None,
         allow_404: bool = False) -> dict | None:
    url = f"{API}{path}" + (f"?{urllib.parse.urlencode(query)}" if query else "")
    req = urllib.request.Request(
        url,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Token": token, "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)["result"]
    except urllib.error.HTTPError as e:
        if allow_404 and e.code == 404:
            return None
        if e.code == 401:
            sys.exit(f"error: Qase rejected the API token (401). Fix QASE_API_TOKEN in {ENV_FILE}")
        sys.exit(f"error: {method} {path} → {e.code}: {e.read().decode(errors='replace')[:500]}")


def list_all(path: str, token: str, query: dict) -> list[dict]:
    items, offset = [], 0
    while True:
        page = call("GET", path, token, query={**query, "limit": 100, "offset": offset})
        items += page["entities"]
        offset += 100
        if offset >= page["total"]:
            return items


def field_ids(token: str):
    """Maps system field option names (severity: major, layer: api, ...) to their Qase IDs."""
    options = {}
    for field in call("GET", "/system_field", token):
        for opt in field.get("options") or []:
            for name in (opt.get("slug"), opt.get("title")):
                if name:
                    options[(field["slug"].lower(), str(name).lower().replace(" ", "-"))] = int(opt["id"])

    def lookup(field: str, value: str) -> int:
        try:
            return options[(field, value)]
        except KeyError:
            known = sorted(v for f, v in options if f == field)
            sys.exit(f"error: Qase has no {field} '{value}'. Available: {', '.join(known) or 'none'}")
    return lookup


def ensure_project(project: str, token: str) -> None:
    if call("GET", f"/project/{project}", token, allow_404=True) is None:
        call("POST", "/project", token, {"title": PROJECT_TITLE, "code": project})
        print(f"created project '{PROJECT_TITLE}' ({project})")


def ensure_suite(project: str, token: str, suite_path: str) -> int:
    suites = list_all(f"/suite/{project}", token, {})
    parent = None
    for title in [p.strip() for p in suite_path.split(".")]:
        found = next((s for s in suites if s["title"] == title and s.get("parent_id") == parent), None)
        if found:
            parent = found["id"]
        else:
            parent = call("POST", f"/suite/{project}", token, {"title": title, "parent_id": parent})["id"]
            print(f"created suite '{title}' (id {parent})")
    return parent


# --- main ------------------------------------------------------------------

def load_env(path: Path) -> None:
    """Minimal .env reader: KEY=value lines, # comments, optional quotes and `export`."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*(?:export\s+)?([A-Za-z_]\w*)\s*=\s*(.*?)\s*$", line)
        if m and not line.lstrip().startswith("#"):
            os.environ.setdefault(m.group(1), m.group(2).strip("\"'"))


def ask_token() -> str:
    """Asks for the API token once and appends it to .env, so later runs need nothing."""
    print("Qase API token not found.\n"
          "Create one in Qase → Workspace settings → API tokens and paste it here.")
    try:
        token = input("QASE_API_TOKEN: ").strip()
    except EOFError:
        token = ""
    if not token:
        sys.exit(f"error: no token given. Run the script again, or put QASE_API_TOKEN=... into {ENV_FILE}")
    existing = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.is_file() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    ENV_FILE.write_text(f"{existing}QASE_API_TOKEN={token}\n", encoding="utf-8")
    print(f"saved to {ENV_FILE} (gitignored)")
    return token


def has_cases(body: str) -> bool:
    return re.search(r"^## Test cases[ \t]*$", body, re.M) is not None


def is_approved(frontmatter: str) -> bool:
    return fm_value(frontmatter, "test_cases_approved").lower() in ("true", "yes")


# A key's whole entry: its line plus any indented continuation lines (a block list).
def _fm_entry(key: str) -> str:
    return rf"^{key}:[^\n]*(?:\n[ \t]+[^\n]*)*"


def set_fm(frontmatter: str, key: str, value: str) -> str:
    """Sets a key to `value` (already formatted YAML, may span lines), replacing the whole entry."""
    if re.search(rf"^{key}:", frontmatter, re.M):
        return re.sub(_fm_entry(key), lambda _: f"{key}:{value if value.startswith(chr(10)) else ' ' + value}",
                      frontmatter, count=1, flags=re.M)
    return f"{frontmatter}\n{key}: {value}"


def fm_list(frontmatter: str, key: str) -> list[str]:
    """Reads a list in either YAML style: flow `[a, b]` or block (`- a` lines, as Obsidian saves it)."""
    m = re.search(_fm_entry(key), frontmatter, re.M)
    if not m:
        return []
    first, *rest = m.group(0).split("\n")
    items = re.findall(r"[^\[\],\s][^\[\],]*", first.split(":", 1)[1])
    items += [re.sub(r"^\s*-\s*", "", line) for line in rest if line.strip().startswith("-")]
    return [i.strip().strip("\"'") for i in items if i.strip()]


def set_fm_list(frontmatter: str, key: str, items: list[str]) -> str:
    """Writes a list in the block style Obsidian uses, so Obsidian doesn't rewrite it."""
    return set_fm(frontmatter, key, "".join(f"\n  - {i}" for i in items) if items else "[]")


def case_numbers(frontmatter: str, project: str) -> list[int]:
    """Case numbers from qase_cases: `[TF-2, TF-3]` (keys of this project) or plain `[2, 3]`."""
    numbers = []
    for item in fm_list(frontmatter, "qase_cases"):
        m = re.fullmatch(rf"(?:{re.escape(project)}-)?(\d+)", item)
        if m:
            numbers.append(int(m.group(1)))
    return list(dict.fromkeys(numbers))


def story_files() -> list[Path]:
    return [p for p in sorted(STORIES_DIR.rglob("*.md"))
            if p.read_text(encoding="utf-8").startswith("---\n")]


def find_suite(suites: list[dict], suite_path: str) -> int | None:
    """ID of a nested suite ("User & Auth.Logout") among the listed suites, without creating it."""
    parent = None
    for title in [t.strip() for t in suite_path.split(".")]:
        found = next((x for x in suites if x["title"] == title and x.get("parent_id") == parent), None)
        if not found:
            return None
        parent = found["id"]
    return parent


def sync(project: str, token: str) -> None:
    """Brings every story's qase_cases in line with Qase: drops the cases deleted there and adds
    the ones created by hand in the story's suite."""
    all_cases = list_all(f"/case/{project}", token, {})
    in_qase = {c["id"] for c in all_cases}
    suites = list_all(f"/suite/{project}", token, {})
    changed = 0
    for path in story_files():
        frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
        numbers = case_numbers(frontmatter, project)
        suite_id = find_suite(suites, fm_value(frontmatter, "qase_suite") or "\0")
        gone = [n for n in numbers if n not in in_qase]
        added = sorted(c["id"] for c in all_cases if suite_id and c.get("suite_id") == suite_id
                       and c["id"] not in numbers)
        if not gone and not added:
            continue
        keys = [f"{project}-{n}" for n in numbers if n in in_qase] + [f"{project}-{n}" for n in added]
        frontmatter = set_fm_list(frontmatter, "qase_cases", keys)
        path.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
        changed += 1
        notes = []
        if gone:
            notes.append(f"removed {', '.join(f'{project}-{n}' for n in gone)} (deleted in Qase)")
        if added:
            notes.append(f"added {', '.join(f'{project}-{n}' for n in added)} (new in the suite)")
        print(f"{path.name}: {'; '.join(notes)}; {len(keys)} in total")
    if not changed:
        print("in sync: qase_cases of every story match Qase")


def show(path: Path, project: str, token: str) -> None:
    """Prints a story's cases as they are in Qase, compactly, for reviewing them against changes."""
    frontmatter, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    for n in case_numbers(frontmatter, project):
        case = call("GET", f"/case/{project}/{n}", token, allow_404=True)
        if not case:
            print(f"{project}-{n}: not in Qase (run --sync)")
            continue
        tags = ", ".join(t.get("title", "") for t in case.get("tags") or [])
        print(f"\n{project}-{n} {case['title']}  [{tags}]")
        for step in sorted(case.get("steps") or [], key=lambda s: s["position"]):
            print(f"  {step['position']}. {step.get('action') or ''}")
            for key in ("expected_result", "data"):
                if step.get(key):
                    print(f"     {key}: " + step[key].replace("\n", "\n     "))


def push_story(path: Path, project: str, token: str, ids, no_update: bool) -> None:
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    story_id, suite_path = fm_value(frontmatter, "id"), fm_value(frontmatter, "qase_suite")
    if not suite_path:
        sys.exit(f"error: {path.name}: qase_suite is empty in the frontmatter")
    cases = parse_cases(body)

    suite_id = ensure_suite(project, token, suite_path)
    # Cases already in Qase: the IDs recorded in qase_cases (wherever they live now, e.g. a
    # previous suite) plus any case with the same title in the target suite.
    existing = {c["title"]: c["id"] for c in list_all(f"/case/{project}", token, {"suite_id": suite_id})}
    alive = []  # keys from qase_cases that still exist in Qase
    for case_id in case_numbers(frontmatter, project):
        found = call("GET", f"/case/{project}/{case_id}", token, allow_404=True)
        if found:
            existing.setdefault(found["title"], found["id"])
            alive.append(f"{project}-{case_id}")

    new = [c for c in cases if c["title"] not in existing]
    old = [c for c in cases if c["title"] in existing]

    if new:
        result = call("POST", f"/case/{project}/bulk", token,
                      {"cases": [to_qase(c, story_id, suite_id, ids) for c in new]})
        existing.update(zip((c["title"] for c in new), result["ids"]))
    if old and not no_update:
        for c in old:
            call("PATCH", f"/case/{project}/{existing[c['title']]}", token,
                 to_qase(c, story_id, suite_id, ids))

    # Keep IDs pushed earlier (their drafts are already gone) and append the new ones.
    keys = list(dict.fromkeys(alive + [f"{project}-{existing[c['title']]}" for c in cases]))
    frontmatter = set_fm_list(frontmatter, "qase_cases", keys)
    frontmatter = set_fm(frontmatter, "status", "analyzed")
    # The drafts now live in Qase; drop the section up to the next "## " heading.
    body = re.sub(r"^## Test cases[ \t]*\n.*?(?=^## |\Z)", "", body, count=1, flags=re.M | re.S)
    path.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")

    print(f"{path.name}: suite '{suite_path}': created {len(new)}, "
          f"{'skipped' if no_update else 'updated'} {len(old)}; qase_cases = [{', '.join(keys)}]; "
          f"drafts removed, status: analyzed")


def main() -> None:
    load_env(ENV_FILE)
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("story", type=Path, nargs="?")
    ap.add_argument("--approved", action="store_true",
                    help="push every story under user-stories/ that is approved and still has draft cases")
    ap.add_argument("--sync", action="store_true",
                    help="update qase_cases of every story: drop cases deleted in Qase, add new ones from its suite")
    ap.add_argument("--show", action="store_true",
                    help="print the story's cases from Qase (key, title, steps, expected result); read-only")
    ap.add_argument("--project", default=os.environ.get("QASE_PROJECT") or DEFAULT_PROJECT)
    ap.add_argument("--dry-run", action="store_true", help="parse and print the payload, call nothing")
    ap.add_argument("--no-update", action="store_true",
                    help="only create missing cases, leave the ones already in Qase untouched")
    args = ap.parse_args()
    if [bool(args.story), args.approved, args.sync].count(True) != 1:
        ap.error("pass exactly one of: a story path, --approved, --sync")

    if args.sync:
        if args.dry_run:
            ap.error("--sync has no dry run; it only changes qase_cases in the stories")
        sync(args.project, os.environ.get("QASE_API_TOKEN") or ask_token())
        return

    if args.show:
        if not args.story:
            ap.error("--show needs a story path")
        show(args.story, args.project, os.environ.get("QASE_API_TOKEN") or ask_token())
        return

    if args.approved:
        stories = []
        for path in story_files():
            frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
            if is_approved(frontmatter) and has_cases(body):
                stories.append(path)
        if not stories:
            print("nothing to push: no approved story has draft test cases")
            return
    else:
        frontmatter, body = split_frontmatter(args.story.read_text(encoding="utf-8"))
        if not has_cases(body):
            sys.exit(f"error: {args.story.name} has no '## Test cases' section")
        if not args.dry_run and not is_approved(frontmatter):
            sys.exit(f"error: {args.story.name} is not approved. Review the cases, then set "
                     "test_cases_approved: true in the frontmatter (--dry-run works without it)")
        stories = [args.story]

    if args.dry_run:
        for path in stories:
            frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
            cases = parse_cases(body)
            payload = [to_qase(c, fm_value(frontmatter, "id"), None) for c in cases]
            print(json.dumps({"story": path.name, "suite": fm_value(frontmatter, "qase_suite"),
                              "cases": payload}, indent=2, ensure_ascii=False))
            print(f"{path.name}: {len(cases)} cases parsed, nothing sent (dry run)", file=sys.stderr)
        return

    token = os.environ.get("QASE_API_TOKEN") or ask_token()
    ensure_project(args.project, token)
    ids = field_ids(token)
    for path in stories:
        push_story(path, args.project, token, ids, args.no_update)


if __name__ == "__main__":
    main()
