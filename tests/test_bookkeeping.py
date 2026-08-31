#!/usr/bin/env python3
"""
Bookkeeping invariants, enforced as ordinary tests.

This file exists because "the suite is green" is already this project's definition of
done, so a bookkeeping violation should look like a test failure rather than something
you notice three days later. It is committed, so it travels to every worktree and needs
no installation.

Each assertion below is a failure this repo has actually had. Nothing here is
hypothetical, and nothing here calls a model or the network.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CAPS = {"triage", "detection", "classification", "boundaries", "review", "publication"}
TRACTATES = {"ketubot", "kiddushin", "gittin", "yevamot", "eruvin"}

# scripts/evaluate_golden.py is called IMMUTABLE by CLAUDE.md. This makes that true
# rather than aspirational. If you genuinely need to change the harness, change this
# hash in the same commit and say why in the message.
EVALUATE_GOLDEN_SHA = "5b83879e731b361d312bc72b3faa2598eaae585b"

# scripts/evaluate_golden.py writes HERE when --output is omitted, silently overwriting a
# historical baseline that cannot be regenerated (the run that produced it is not
# reproducible -- Lesson 11). The harness is immutable, so the flag cannot be made
# required; pinning the file it would clobber is the next best thing, and turns "remember
# to pass --output" from advice into a test failure.
BASELINE_KETUBOT_SHA = "e5e46fd7ac174b2a52c4030ed71bb603c2f79067"

# The irreplaceable data. An unchanged composite beside a changed count is the signature
# of silent loss, so we assert the counts and never the score.
GOLDEN_COUNTS = {
    "ketubot": {"pages": 222, "entries": 187, "accepted": 164},
    "kiddushin": {"pages": 162, "entries": 96, "accepted": 85},
}


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).stdout


def tracked(*globs: str) -> list[Path]:
    out: list[Path] = []
    for g in globs:
        out += [ROOT / p for p in git("ls-files", g).split("\n") if p and not p.startswith("archive/")]
    return [p for p in out if p.exists()]


def items() -> list[tuple[Path, dict, str]]:
    out = []
    for d in (ROOT / "work", ROOT / "work" / "done"):
        for f in sorted(d.glob("*.md")):
            if f.name in ("_TEMPLATE.md", "README.md"):
                continue
            text = f.read_text()
            m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
            assert m, f"{f.relative_to(ROOT)} has no frontmatter"
            fm = dict(re.findall(r"^(\w+):[ \t]*(.*)$", m.group(1), re.M))
            out.append((f, fm, text))
    return out


def listy(fm: dict, key: str) -> list[str]:
    return [x.strip() for x in fm.get(key, "").strip("[]").split(",") if x.strip()]


# ---------------------------------------------------------------- lessons

def test_lesson_numbers_are_unique_across_every_local_ref():
    """Four sessions each wrote a 'Lesson 26' on 2026-08-30.

    One file per lesson makes that collision *merge cleanly*, which is worse than
    conflicting — so checking the current tree is not enough. Check every local ref.
    """
    seen: dict[int, set[str]] = {}
    refs = [r for r in git("for-each-ref", "--format=%(refname)", "refs/heads").split("\n") if r]
    for ref in refs:
        listing = git("ls-tree", "--name-only", f"{ref}:lessons")
        for name in listing.split("\n"):
            m = re.match(r"L-(\d+)-", name)
            if m:
                seen.setdefault(int(m.group(1)), set()).add(f"{ref}:{name}")
    collisions = {n: sorted(v) for n, v in seen.items()
                  if len({f.split(":")[1] for f in v}) > 1}
    assert not collisions, f"same lesson number, different files: {collisions}"


def test_every_lesson_citation_resolves():
    """218+ `Lesson N` citations across .md, .py and prompt files. All must exist."""
    have = {int(m.group(1)) for f in (ROOT / "lessons").glob("L-*.md")
            if (m := re.match(r"L-(\d+)-", f.name))}
    missing: dict[int, list[str]] = {}
    for p in tracked("*.md", "*.py", "*.json"):
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for n in {int(x) for x in re.findall(r"Lesson (\d+)", text)}:
            if n not in have:
                missing.setdefault(n, []).append(str(p.relative_to(ROOT)))
    assert not missing, f"cited lessons with no file: {missing}"


# ---------------------------------------------------------------- work items

def test_item_frontmatter_is_complete_and_uses_known_slugs():
    for f, fm, _ in items():
        rel = f.relative_to(ROOT)
        for key in ("title", "capability", "tractate", "blocked_by", "awaiting",
                    "finding", "superseded_by"):
            assert key in fm, f"{rel} missing frontmatter field {key!r}"
        assert fm["title"].strip(), f"{rel} has an empty title"
        bad_caps = set(listy(fm, "capability")) - CAPS
        assert not bad_caps, f"{rel} has unknown capability {bad_caps}"
        bad_tr = set(listy(fm, "tractate")) - TRACTATES
        assert not bad_tr, f"{rel} has unknown tractate {bad_tr}"


def test_blocked_by_and_awaiting_resolve():
    """A dependency pointing at nothing parks work silently. Both kinds must resolve:
    an item slug, or a `jeff:` question that comms/JEFF.md actually lists."""
    slugs = {f.stem for f, _, _ in items()}
    jeff = set(re.findall(r"`(jeff:[a-z0-9-]+)`", (ROOT / "comms/JEFF.md").read_text()))
    for f, fm, _ in items():
        for key in ("blocked_by", "awaiting"):
            for dep in listy(fm, key):
                ok = dep in slugs or (dep.startswith("jeff:") and dep in jeff)
                assert ok, (f"{f.relative_to(ROOT)}: {key} -> {dep!r} resolves to nothing "
                            f"(not a work item, not a question in comms/JEFF.md)")


def test_done_items_record_what_happened():
    """`## Outcome` is the whole point of never deleting an item: a revert we cannot
    explain gets re-tried. A `finding:` is not required — several closed items produced
    code or documentation rather than a finding — but if one is named it must exist."""
    for f, fm, text in items():
        rel, done = f.relative_to(ROOT), f.parent.name == "done"
        has_outcome = re.search(r"^## Outcome$", text, re.M) is not None
        if done:
            assert has_outcome, f"{rel} is in work/done/ with no `## Outcome` section"
        else:
            assert not has_outcome, f"{rel} is open but already has an `## Outcome`"
        finding = fm.get("finding", "").strip()
        if finding:
            assert (ROOT / finding).exists(), f"{rel}: finding -> {finding} does not exist"


# ---------------------------------------------------------------- irreplaceable data

def test_evaluate_golden_is_unchanged():
    sha = git("hash-object", "scripts/evaluate_golden.py").strip()
    assert sha == EVALUATE_GOLDEN_SHA, (
        "scripts/evaluate_golden.py changed. CLAUDE.md calls it IMMUTABLE and every "
        "score in this repo is comparable only because it has not moved. If the change "
        "is deliberate, update EVALUATE_GOLDEN_SHA in the same commit and justify it.")


def test_the_historical_baseline_was_not_clobbered():
    sha = git("hash-object", "docs/golden/v7/baseline_ketubot.json").strip()
    assert sha == BASELINE_KETUBOT_SHA, (
        "docs/golden/v7/baseline_ketubot.json changed. This is almost certainly an "
        "accident: scripts/evaluate_golden.py writes here when --output is omitted. The "
        "file records a score from a run that CANNOT be reproduced (Lesson 11), so an "
        "overwrite is unrecoverable. Restore it with `git checkout -- "
        "docs/golden/v7/baseline_ketubot.json` and re-run with --output.")


@pytest.mark.parametrize("tractate", sorted(GOLDEN_COUNTS))
def test_golden_still_measures_what_it_should(tractate):
    """Counts, never the composite. The composite is built from ratios over pages already
    in the golden, so deleting expert validations makes it go UP."""
    d = json.loads((ROOT / f"results/canonical/{tractate}_canonical.json").read_text())
    stories = [s for pg in d["pages"] for s in pg.get("stories", [])]
    got = {"pages": len(d["pages"]), "entries": len(stories),
           "accepted": len([s for s in stories if s.get("classification") != "NOT_A_STORY"])}
    assert got == GOLDEN_COUNTS[tractate], (
        f"{tractate} golden moved: {got} != {GOLDEN_COUNTS[tractate]}. The golden may only "
        f"GROW programmatically; if this is a deliberate addition, update the expected "
        f"counts in the same commit.")


# ---------------------------------------------------------------- paths

def test_no_reference_to_a_docs_golden_path_that_no_longer_exists():
    """docs/golden/ was emptied of prose on 2026-08-30. Its README carries a redirect
    table, and dated findings keep their old citations on purpose — but nothing may
    reference a docs/golden path that does not exist *and* is not listed as an old path
    in that redirect table."""
    redirect = (ROOT / "docs/golden/README.md").read_text()
    broken: list[str] = []
    for p in tracked("*.md", "*.py"):
        if p.name == "README.md" and p.parent.name == "golden":
            continue
        if p.parts[-2:][0] in ("findings", "history", "brainstorms") or "lessons" in p.parts:
            continue  # dated records keep what they said at the time; the redirect table
            # in docs/golden/README.md is how a reader resolves them
        for ref in re.findall(r"docs/golden/[A-Za-z0-9_/.-]*", p.read_text(errors="ignore")):
            ref = ref.rstrip(".")
            if not (ROOT / ref).exists() and f"`{ref}`" not in redirect:
                broken.append(f"{p.relative_to(ROOT)} -> {ref}")
    assert not broken, f"dangling docs/golden references: {broken}"


def test_generated_files_are_not_stale():
    """STATE.md and WORK.md are generated. If someone changed an item and did not
    regenerate, the board silently lies."""
    r = subprocess.run(["python3", "scripts/board.py", "--check"], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_generated_files_carry_their_banner():
    for name in ("STATE.md", "WORK.md"):
        head = (ROOT / name).read_text().split("\n")[0]
        assert "GENERATED" in head, f"{name} lost its do-not-edit banner"
