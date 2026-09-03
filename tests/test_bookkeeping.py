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
    # Gittin, 2026-09-02. `accepted` here counts BORDERLINE, because that is what this
    # test's definition has always meant (anything not NOT_A_STORY) and silently
    # redefining it would move the other two tractates' numbers without touching them.
    # The split that actually matters is pinned separately, below.
    "gittin": {"pages": 178, "entries": 135, "accepted": 117},
}

# Gittin is the first golden built from two kinds of expert evidence, and the first to
# carry BORDERLINE. Both distinctions are load-bearing and neither is visible in a
# pages/entries/accepted triple, so they get their own assertion.
GITTIN_SHAPE = {
    "label_sources": {"expert_blind_list": 110, "expert_verdict": 25},
    "classification_distribution": {"YES": 113, "BORDERLINE": 4, "NOT_A_STORY": 18},
    "unlabelled_proposals": 23,
    "known_missing_stories": 3,
}


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).stdout


def tracked(*globs: str) -> list[Path]:
    """
    Every repo file matching the globs: tracked, PLUS untracked-but-not-ignored.

    Untracked files were added 2026-08-31. Enumerating only `git ls-files` made every
    guard here blind to a file until it was committed — so a brand-new finding with a
    broken link passed the suite and failed only after `git add`. A guard whose coverage
    depends on git state is weakest exactly when it matters most: just after you write a
    file (Lesson 38).

    `--exclude-standard` respects .gitignore, so scratch and generated artifacts stay out;
    the added set is precisely the files you are about to commit.
    """
    out: list[Path] = []
    for g in globs:
        listings = (git("ls-files", g),
                    git("ls-files", "--others", "--exclude-standard", g))
        for listing in listings:
            out += [ROOT / p for p in listing.split("\n")
                    if p and not p.startswith("archive/")]
    return [p for p in dict.fromkeys(out) if p.exists()]


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


def test_every_open_item_declares_what_it_writes():
    """`blocked_by` is ORDERING. `writes:` is CONTENTION. They are different graphs.

    Without `writes:`, two items with no dependency between them are presented by
    STATE.md, WORK.md and STATUS.md alike as concurrently runnable whether or not they
    write the same file. On 2026-08-31 six such pairs existed among the items runnable
    that day -- `golden-completeness` and `kiddushin-comments-harvest` both rewrite
    `results/canonical/kiddushin_canonical.json`, and both were recommended in the same
    breath as cheap next steps.

    An item that declares nothing is invisible to `board.py lanes`, which is worse than
    an item that declares too much: over-declaring costs a serialized lane,
    under-declaring costs a silent corruption.
    """
    missing = [str(f.relative_to(ROOT)) for f, fm, _ in items()
               if not f.parent.name == "done" and not listy(fm, "writes")]
    assert not missing, ("open items with no `writes:` -- their collisions cannot be "
                         f"seen by `board.py lanes`: {missing}")


def test_the_generated_board_is_never_merged_by_hand():
    """The guaranteed collision, and the one that has nothing to do with the work.

    Every item that is opened, finished or edited changes STATE.md and WORK.md, so every
    pair of concurrent branches conflicts on them. Measured on 2026-08-31: three sessions
    each opening ONE unrelated work item produced two conflicting merges, five conflict
    markers committed into WORK.md, and a trunk on which `board.py --check` failed.

    A hand-resolved generated file is worse than a conflict, because editing it breaks
    the checksum, and board.py then REFUSES to regenerate in whichever session next runs
    it -- a failure two steps removed from its cause.

    So the drivers must exist and .gitattributes must point at them. `board.py setup`
    registers them per clone; this asserts the committed half.
    """
    attrs = (ROOT / ".gitattributes").read_text()
    for name, driver in (("STATE.md", "board-state"), ("WORK.md", "board-work")):
        assert re.search(rf"^{re.escape(name)}\s+merge={driver}\s*$", attrs, re.M), \
            f".gitattributes does not route {name} to the {driver} merge driver"

    hook = ROOT / ".githooks" / "post-merge"
    assert hook.exists(), (
        "no .githooks/post-merge. The merge driver runs mid-merge, when work/ on disk "
        "does not yet hold the other side's items, so it resolves the conflict but "
        "cannot produce the correct board. The hook is what produces it (Lesson 32).")
    assert "board.py" in hook.read_text(), "post-merge hook no longer regenerates the board"


def test_contention_is_computed_over_subtrees_not_just_exact_paths():
    """A trailing `/` in `writes:` means the subtree. Verified by simulating the failure
    it guards (Lesson 31): declaring `validation/generators/` must collide with a file
    inside it, or four review-UI items would be reported as safely concurrent."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("board", ROOT / "scripts" / "board.py")
    board = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(board)

    assert board.overlap(["validation/generators/"], ["validation/generators/gen_ui.py"])
    assert board.overlap(["results/canonical/kiddushin_canonical.json"],
                         ["results/canonical/kiddushin_canonical.json"])
    assert not board.overlap(["results/triage/gittin.json"], ["results/triage/eruvin.json"])
    # A prefix that is not a path boundary is not an overlap.
    assert not board.overlap(["results/v10/"], ["results/v10_other/x.json"])


def test_an_undeclared_write_is_caught_when_an_item_is_closed():
    """`writes:` is filled in when an item is OPENED -- before the work is done.

    Lesson 34 is exactly about such a field: a person who does not know a value leaves it
    blank, and an LLM session produces a confident, plausible, wrong one. A blank gets
    investigated; a confident wrong value does not. So the field cannot be trusted on its
    own -- it has to be grounded against something that knows.

    This is not a hypothetical risk. The FIRST item ever to carry the field under-declared
    four contended paths, one of which (tests/test_review_ui_symmetry.py) collides with
    `review-verdict-axes` -- an item the lane map was printing as safe to run concurrently
    at that exact moment. An unchecked declaration is worse than none: it licenses the
    confidence that two sessions cannot hurt each other.

    Verified by simulating the failure it guards (Lesson 31).
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("board", ROOT / "scripts" / "board.py")
    board = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(board)

    # An undeclared path that another open item writes must surface as a collision...
    victim = next((i for i in board.items() if not i["done"] and i["writes"]), None)
    assert victim, "no open item declares writes -- nothing to test against"
    stolen = victim["writes"][0]
    hidden = [(i["slug"], board.overlap([stolen], i["writes"]))
              for i in board.items() if not i["done"]]
    assert any(sl == victim["slug"] and sh for sl, sh in hidden), (
        f"overlap() no longer matches {stolen} against the item that declares it")

    # ...and the bookkeeping every item touches by construction must NOT, or the report
    # would cry wolf on every single close and stop being read.
    for p in ("STATE.md", "WORK.md", "docs/findings/x.md", "lessons/L-999-x.md"):
        assert p.startswith(board.UNCONTENDED), f"{p} should be exempt from drift reporting"


def test_capture_refuses_to_commit_a_credential():
    """`board.py capture` runs `git add -A` and pushes. That sweeps in secrets.

    Verified by simulating the failure it guards (Lesson 31). This is not a theoretical
    risk: testing `capture` end to end on 2026-08-31, a worktree that had branched before
    .gitignore gained `.env` had the secret committed AND pushed. A pushed secret is in
    history forever, so the guard refuses the whole run rather than skipping one file.

    The list is deliberately high-precision. A false positive blocks a capture under time
    pressure with unpushed work at stake, which is the one moment a tool must not argue.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("board", ROOT / "scripts" / "board.py")
    board = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(board)

    caught = board.sensitive([
        ".env", "config/.env.production", "deploy/server.pem", "certs/tls.key",
        "secrets/id_rsa", "gcp/service-account.json",
    ])
    assert len(caught) == 6, f"a credential shape slipped through: {caught}"

    # And must not fire on ordinary repo content, or it blocks captures for nothing.
    assert board.sensitive([
        "src/story_detector_v11.py", "results/canonical/ketubot_canonical.json",
        "docs/findings/2026-08-31-x.md", "environment.md", "scripts/keyword_lookup.py",
    ]) == []


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


def test_the_gittin_golden_keeps_its_two_kinds_of_evidence_apart():
    """A golden entry labelled from a 2005 list is NOT the same fact as one he judged.

    `expert_verdict` means he saw our span and ruled on it. `expert_blind_list` means his
    list names a story our span overlaps -- it says a story is there, and says nothing
    about our extent. Collapsing them would let an unvalidated boundary be quoted as
    expert-confirmed, which is the shape of error Lesson 24 is about.

    Also pinned: every entry carries an expert label. A proposal with no expert evidence
    belongs in `unlabelled_proposals`, never in `pages[].stories[]` with a null
    classification -- a null in a file called "golden" is read as a label by the next
    reader and as a fact by the one after.
    """
    d = json.loads((ROOT / "results/canonical/gittin_canonical.json").read_text())
    stories = [s for pg in d["pages"] for s in pg.get("stories", [])]

    assert d["label_sources"] == GITTIN_SHAPE["label_sources"]
    assert d["classification_distribution"] == GITTIN_SHAPE["classification_distribution"]
    assert len(d["unlabelled_proposals"]) == GITTIN_SHAPE["unlabelled_proposals"]
    assert len(d["known_missing_stories"]) == GITTIN_SHAPE["known_missing_stories"]

    for s in stories:
        assert s.get("label_source") in ("expert_verdict", "expert_blind_list"), (
            f"{s} carries no label source. Every entry in this golden is labelled by the "
            f"expert, one way or the other.")
        assert s.get("classification") in ("YES", "BORDERLINE", "NOT_A_STORY")

    # BORDERLINE must stay its own answer. He asked for contested cases to be kept and
    # flagged (2026-07-06); rounding them into yes or no is the thing he declined.
    borderline = [s for s in stories if s["classification"] == "BORDERLINE"]
    assert len(borderline) == 4
    assert all(s["label_source"] == "expert_verdict" for s in borderline), (
        "a BORDERLINE can only come from a verdict -- a 2005 list has no such column")


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

def test_no_markdown_link_is_broken():
    """A broken link is how a reorganised repo quietly stops being navigable.

    This is not hypothetical bookkeeping: on 2026-08-31 the first item anyone finished
    broke its own link to FRAMEWORK.md, because `work/` items link with `../` and
    `work/done/` sits one level deeper. 60 such links were one `git mv` from breaking.
    `board.py finish` now re-roots them; this test is what notices if it stops.
    """
    import urllib.parse
    broken = []
    for p in tracked("*.md"):
        base = p.parent
        for m in re.finditer(r"\[([^\]]*)\]\(([^)\s]+)\)", p.read_text(errors="ignore")):
            link = m.group(2).split("#")[0]
            if link.startswith(("http", "mailto:", "#")) or not link:
                continue
            target = (base / urllib.parse.unquote(link)).resolve()
            if not target.exists():
                broken.append(f"{p.relative_to(ROOT)} -> {link}")
    assert not broken, f"{len(broken)} broken markdown link(s): {broken[:10]}"


def test_the_closing_step_re_roots_the_moved_item_s_own_links():
    """Verify the guard by simulating the failure it guards (Lesson 31).

    NOTE the name. This covers ONE direction: links *out of* the moved item. It was
    called `..._so_finishing_cannot_break_them` until 2026-08-31, which overclaimed —
    finishing went on breaking links *into* the item, and did so twice in one session
    while this test stayed green. The suite asserted a property the repo did not have.
    The other direction lives in `tests/test_finish_fixes_inbound_links.py`.

    Items live in `work/` and link out with `../`. Finishing one moves it into
    `work/done/`, one level deeper, where every such link breaks — at the exact moment
    the item becomes a permanent record. That happened: the first item anyone finished
    broke its own link to FRAMEWORK.md, with 60 more one `git mv` away.

    The fix is not to pre-break the 60 links (they are correct where they are); it is for
    the closing step to re-root them. This tests that it does.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("board", ROOT / "scripts" / "board.py")
    board = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(board)

    before = ("Read [`FRAMEWORK.md`](../FRAMEWORK.md) and [wf](../docs/technical/x.md), "
              "plus [deep](../../already/deep.md) and [ext](https://example.com).")
    after = board.reroot_links(before)
    assert "](../../FRAMEWORK.md)" in after
    assert "](../../docs/technical/x.md)" in after
    assert "](../../already/deep.md)" in after, "an already-deeper link must not move again"
    assert "https://example.com" in after, "external links must be untouched"
    assert board.reroot_links(after) == after, "re-rooting must be idempotent"


def test_every_open_item_would_survive_being_closed():
    """The 60 latent breakages, checked the right way round: not 'are the links already
    deep' but 'does the closing step leave them resolvable'.

    Outbound only — see the note on the test above. Inbound is covered by
    `tests/test_finish_fixes_inbound_links.py`."""
    import importlib.util, urllib.parse
    spec = importlib.util.spec_from_file_location("board", ROOT / "scripts" / "board.py")
    board = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(board)

    done_dir = ROOT / "work" / "done"
    broken = []
    for f in sorted((ROOT / "work").glob("*.md")):
        if f.name == "README.md":
            continue
        for m in re.finditer(r"\[([^\]]*)\]\(([^)\s]+)\)", board.reroot_links(f.read_text())):
            link = m.group(2).split("#")[0]
            if link.startswith(("http", "mailto:", "#")) or not link:
                continue
            if not (done_dir / urllib.parse.unquote(link)).resolve().exists():
                broken.append(f"{f.name} -> {link}")
    assert not broken, (
        f"{len(broken)} link(s) would still be broken after `board.py finish`: {broken[:5]}")
