"""Tests for scripts/septimus_email.py and the email step of septimus_weekly.py. No network, no Firebase:
Resend is a fake `post` function and the Store is the in-memory fake from test_septimus_weekly.py."""
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import septimus_assign as A  # noqa: E402
import septimus_email as E  # noqa: E402
import septimus_weekly as W  # noqa: E402
from test_septimus_weekly import FIX, SUNDAY, MONDAY, FakeStore, config, person  # noqa: E402

SITE = "https://stories.example"
SETTINGS = E.Settings("re_test", "Stories <talmud-stories@mail.example>", SITE, counts_to="simon@mail.example")


class MailStore(FakeStore):
    """The fake Store plus the email methods of the real one."""

    def __init__(self, users, rows=(), summary=None, addresses=None):
        super().__init__(users, rows, summary)
        self.sent = {}                                           # key -> {"uid", "week"}
        self.addresses = addresses if addresses is not None else {
            u["uid"]: (f"{u['uid']}@mail.example", f"{u['uid'].title()} Cohen") for u in users}

    def claim_sent(self, key, uid="", week=None):
        if key in self.sent:
            return False
        self.sent[key] = {"uid": uid, "week": week}
        return True

    def unclaim_sent(self, key):
        self.sent.pop(key, None)

    def sent_keys(self, week):
        return {k for k, v in self.sent.items() if v["week"] == week}

    def contacts(self, uids):
        return {uid: self.addresses[uid] for uid in uids if uid in self.addresses}

    def mark_emails_done(self, week):
        self.runs[week]["emailsDone"] = True


class FakeResend:
    """Stands in for Resend. `answers` maps an address to a list of (status, body, headers) or an exception,
    used in order; anyone else gets 200. Like Resend, a repeated Idempotency-Key is not delivered again."""

    def __init__(self, answers=None):
        self.answers = {k: list(v) for k, v in (answers or {}).items()}
        self.delivered = []                                      # payloads that really "went out"
        self.calls = []
        self.keys = set()

    def __call__(self, payload, key):
        to = payload["to"][0]
        self.calls.append((to, key))
        queue = self.answers.get(to)
        if queue:
            answer = queue.pop(0)
            if isinstance(answer, Exception):
                raise answer
            if answer[0] != 200:
                return answer
        if key not in self.keys:
            self.keys.add(key)
            self.delivered.append(payload)
        return 200, {"id": "x"}, {}

    def to(self, address):
        return [p for p in self.delivered if p["to"] == [address]]


@pytest.fixture
def order():
    return A.load_story_order(FIX)


@pytest.fixture
def details():
    return E.load_story_details(FIX)


def go(store, today, order, details, resend, settings=SETTINGS, **kw):
    mailer = E.Mailer(settings, post=resend, sleep=lambda s: None)
    return W.run(store, today, config(), story_order=order, list_version="test-1", mailer=mailer,
                 story_details=details, **kw)


def two_people():
    return MailStore([person("alice", 10, 1), person("bob", 5, 2)])


# ---------------------------------------------------------------- the weekly email

def test_everyone_handed_stories_gets_one_email_with_their_own_stories(order, details):
    store, resend = two_people(), FakeResend()
    counts = go(store, SUNDAY, order, details, resend)
    assert counts["emailSent"] == 2 and counts["emailFailed"] == 0
    for uid in ("alice", "bob"):
        (mail,) = resend.to(f"{uid}@mail.example")
        mine = [r["storyId"] for r in store.rows.values() if r["uid"] == uid]
        assert mine and all(f"{SITE}/#/s/{sid}" in mail["html"] and f"{SITE}/#/s/{sid}" in mail["text"] for sid in mine)
        other = [r["storyId"] for r in store.rows.values() if r["uid"] != uid]
        assert not any(f"/#/s/{sid}\"" in mail["html"] for sid in other)
        assert mail["subject"] == "Your stories this week (week 1)"
        assert f"Hi {uid.title()}," in mail["html"] and f"{SITE}/#/my" in mail["html"]
        assert mail["from"] == SETTINGS.sender
    assert store.runs[1]["emailsDone"] is True


def test_a_second_run_sends_nothing_twice(order, details):
    store, resend = two_people(), FakeResend()
    go(store, SUNDAY, order, details, resend)
    again = go(store, SUNDAY, order, details, resend)
    go(store, MONDAY, order, details, resend)
    assert again["emailSent"] == 0
    assert len(resend.delivered) == 3                            # alice, bob, and one counts email
    assert len(resend.calls) == 3                                # the later runs did not even ask Resend


def test_a_refused_email_is_sent_by_the_next_daily_run_and_only_that_one(order, details):
    store = two_people()
    resend = FakeResend({"bob@mail.example": [(422, {"name": "validation_error"}, {})]})
    first = go(store, SUNDAY, order, details, resend)
    assert (first["emailSent"], first["emailFailed"]) == (1, 1)
    assert "emailsDone" not in store.runs[1] and "1_bob" not in store.sent
    second = go(store, MONDAY, order, details, resend)
    assert (second["emailSent"], second["emailFailed"]) == (1, 0)
    assert len(resend.to("alice@mail.example")) == 1 and len(resend.to("bob@mail.example")) == 1
    assert store.runs[1]["emailsDone"] is True


def test_no_clear_answer_is_never_retried(order, details):
    """A timeout may mean the email went out. One missed email is better than two."""
    store = two_people()
    resend = FakeResend({"bob@mail.example": [TimeoutError("timed out")]})
    first = go(store, SUNDAY, order, details, resend)
    assert (first["emailSent"], first["emailUnknown"], first["emailFailed"]) == (1, 1, 0)
    go(store, MONDAY, order, details, resend)
    assert [to for to, _ in resend.calls].count("bob@mail.example") == 1
    assert "1_bob" in store.sent


def test_a_server_error_is_treated_as_no_clear_answer(order, details):
    store = two_people()
    resend = FakeResend({"bob@mail.example": [(500, {}, {})]})
    assert go(store, SUNDAY, order, details, resend)["emailUnknown"] == 1
    assert "1_bob" in store.sent


def test_slow_down_answers_are_waited_out(order, details):
    store, waits = two_people(), []
    resend = FakeResend({"alice@mail.example": [(429, {"name": "rate_limit_exceeded"}, {"retry-after": "2"})] * 2})
    mailer = E.Mailer(SETTINGS, post=resend, sleep=waits.append)
    counts = W.run(store, SUNDAY, config(), story_order=order, list_version="t", mailer=mailer, story_details=details)
    assert counts["emailSent"] == 2 and waits == [2.0, 2.0]


def test_when_the_quota_runs_out_the_rest_wait_for_the_next_run(order, details):
    store = MailStore([person("alice", 10, 1), person("bob", 5, 2), person("carol", 5, 3)])
    quota = (429, {"name": "daily_quota_exceeded"}, {})
    resend = FakeResend({"bob@mail.example": [quota]})
    first = go(store, SUNDAY, order, details, resend)
    assert (first["emailSent"], first["emailFailed"]) == (1, 2)          # alice sent; bob refused; carol not tried
    assert "carol@mail.example" not in [to for to, _ in resend.calls]
    second = go(store, MONDAY, order, details, resend)
    assert second["emailSent"] == 2 and store.runs[1]["emailsDone"] is True
    assert all(len(resend.to(f"{u}@mail.example")) == 1 for u in ("alice", "bob", "carol"))


def test_people_without_an_address_or_with_emails_off_are_skipped_not_failed(order, details):
    store = MailStore([person("alice", 10, 1), person("bob", 5, 2, emailOff=True), person("carol", 5, 3)],
                      addresses={"alice": ("alice@mail.example", "Alice"), "bob": ("bob@mail.example", "Bob")})
    resend = FakeResend()
    counts = go(store, SUNDAY, order, details, resend)
    assert (counts["emailSent"], counts["emailSkipped"], counts["emailFailed"]) == (1, 2, 0)
    assert not resend.to("bob@mail.example") and store.runs[1]["emailsDone"] is True


def test_the_test_list_keeps_made_up_addresses_from_ever_being_emailed(order, details):
    """Staging accounts have made-up addresses. With SEPTIMUS_EMAIL_ONLY_TO set, only that list is emailed."""
    settings = E.Settings("re_test", SETTINGS.sender, SITE, "simon@mail.example", frozenset({"alice@mail.example"}))
    store, resend = two_people(), FakeResend()
    counts = go(store, SUNDAY, order, details, resend, settings=settings)
    assert (counts["emailSent"], counts["emailSkipped"]) == (1, 1)
    assert {p["to"][0] for p in resend.delivered} == {"alice@mail.example", "simon@mail.example"}


def test_no_mailer_means_no_email_and_the_handout_still_happens(order, details):
    store = two_people()
    counts = W.run(store, SUNDAY, config(), story_order=order, list_version="t")
    assert counts["handedOut"] > 0 and counts["emailSent"] == 0 and not store.sent


def test_dry_run_and_pause_send_nothing(order, details):
    for kw in ({"dry_run": True}, {"pause": True}):
        store, resend = two_people(), FakeResend()
        go(store, SUNDAY, order, details, resend, **kw)
        assert not resend.calls and not store.sent


def test_a_crash_in_the_email_step_does_not_undo_or_fail_the_handout(order, details):
    class Broken(MailStore):
        def contacts(self, uids):
            raise RuntimeError("auth is down for alice")
    store, resend = Broken([person("alice", 10, 1)]), FakeResend()
    counts = go(store, SUNDAY, order, details, resend)
    assert counts["handedOut"] > 0 and store.runs[1]["finishedAt"] and counts["emailFailed"] == 1
    assert "emailsDone" not in store.runs[1]                     # so the next run tries the emails again


def test_someone_who_stopped_after_the_handout_is_not_emailed_on_a_later_run(order, details):
    store = two_people()
    refuse = (422, {"name": "validation_error"}, {})
    resend = FakeResend({"bob@mail.example": [refuse]})
    go(store, SUNDAY, order, details, resend)
    store.user_docs["bob"]["minutesPerWeek"] = 0                 # bob presses "Stop my stories" on Sunday night
    go(store, MONDAY, order, details, resend)                    # his rows are handed back before the email step
    assert not resend.to("bob@mail.example")


# ---------------------------------------------------------------- still with us, counts

def test_a_person_paused_in_this_run_gets_one_still_with_us_email(order, details):
    store, resend = MailStore([person("zed", 5, 1)]), FakeResend()
    paused_week = None
    for week in range(1, 9):
        counts = go(store, SUNDAY + timedelta(weeks=week - 1), order, details, resend)
        if counts["paused"]:
            paused_week = week
            assert counts["pauseEmails"] == 1
            break
    assert paused_week, "the fixture person who never reads should be paused within 8 weeks"
    mails = [p for p in resend.delivered if p["subject"] == "Still with us?"]
    assert len(mails) == 1 and mails[0]["to"] == ["zed@mail.example"] and "Resume" in mails[0]["text"]
    go(store, SUNDAY + timedelta(weeks=paused_week), order, details, resend)
    assert len([p for p in resend.delivered if p["subject"] == "Still with us?"]) == 1


def test_counts_email_goes_to_simon_after_a_handout_with_numbers_only(order, details):
    store, resend = two_people(), FakeResend()
    counts = go(store, SUNDAY, order, details, resend)
    (mail,) = resend.to("simon@mail.example")
    assert mail["subject"] == f"Septimus week 1: {counts['handedOut']} stories to 2 people"
    assert "Weekly emails sent: 2" in mail["text"] and f"Stories handed out: {counts['handedOut']}" in mail["text"]
    assert not any(word in mail["text"] + mail["html"] for word in ("alice", "bob", "Cohen"))
    go(store, MONDAY, order, details, resend)                    # nothing happened on Monday: no second email
    assert len(resend.to("simon@mail.example")) == 1


def test_no_counts_address_means_no_counts_email(order, details):
    settings = E.Settings("re_test", SETTINGS.sender, SITE)
    store, resend = two_people(), FakeResend()
    go(store, SUNDAY, order, details, resend, settings=settings)
    assert len(resend.delivered) == 2


# ---------------------------------------------------------------- privacy, rendering, settings

def test_logs_and_printed_counts_never_carry_a_name_an_address_or_an_id(order, details, caplog, capsys):
    store = two_people()
    resend = FakeResend({"bob@mail.example": [(422, {"name": "validation_error", "message": "bob@mail.example"}, {})]})
    with caplog.at_level(logging.DEBUG):
        go(store, SUNDAY, order, details, resend)
    seen = caplog.text + capsys.readouterr().out
    assert "validation_error" in seen
    assert not any(word in seen for word in ("alice", "bob", "Cohen", "mail.example"))


def test_weekly_email_wording_and_escaping():
    stories = [{"id": "berakhot-5b-1-2", "ref": "Berakhot 5b", "refs": ["Berakhot 5b", "Berakhot 6a"],
                "summary": "Rav <Huna> & his son", "words": 300},
               {"id": "berakhot-7a-3-4", "ref": "Berakhot 7a", "refs": [], "summary": "", "words": 10}]
    subject, html_body, text = E.render_weekly("Dana<b>", 3, stories, 1, 412, 1800, SITE, 75)
    assert subject == "Your stories this week (week 3)"
    assert "Hi Dana&lt;b&gt;," in html_body and "<b>" not in html_body.replace("<body", "")
    assert "Rav &lt;Huna&gt; &amp; his son" in html_body
    assert "Berakhot 5b – 6a" in html_body and "about 4 min" in html_body and "about 1 min" in html_body
    assert "Here are your stories for this week, about 5 minutes of learning." in text
    assert "You also have 1 story still open from earlier weeks." in text
    assert "Together we have learned 412 of about 1,800 stories." in text
    assert "In memory of Joe Septimus." in html_body
    one = E.render_weekly("", 1, stories[:1], 0, 0, 0, SITE, 75)[2]
    assert one.startswith("Hello,") and "Here is your story for this week" in one and "still open" not in one


def test_story_details_come_from_the_data_files(details, order):
    assert all(s.id in details for s in order)
    real = E.load_story_details(ROOT / "site" / "data")
    some = next(iter(real.values()))
    assert some["ref"] and some["words"] > 0 and isinstance(some["refs"], list)


def test_settings_from_env():
    assert E.Settings.from_env({}) == (None, "")
    off, problem = E.Settings.from_env({"RESEND_API_KEY": "re_x"})
    assert off is None and "SEPTIMUS_EMAIL_FROM" in problem and "SEPTIMUS_SITE_URL" in problem and "re_x" not in problem
    s, problem = E.Settings.from_env({"RESEND_API_KEY": "re_x", "SEPTIMUS_EMAIL_FROM": "A <a@b.example>",
                                      "SEPTIMUS_SITE_URL": "https://x.example/", "SEPTIMUS_COUNTS_TO": " s@b.example ",
                                      "SEPTIMUS_EMAIL_ONLY_TO": "S@b.example, t@b.example"})
    assert problem == "" and s.site_url == "https://x.example" and s.counts_to == "s@b.example"
    assert s.may_email("s@B.example") and not s.may_email("other@b.example")
    assert E.Settings("k", "f", "u").may_email("anyone@b.example")


def test_the_real_post_builds_the_request_resend_documents(monkeypatch):
    seen = {}

    class Response:
        status, headers = 200, {}

        def read(self):
            return b'{"id": "abc"}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(request, timeout):
        seen.update(url=request.full_url, method=request.get_method(), headers=dict(request.header_items()),
                    body=request.data)
        return Response()

    monkeypatch.setattr(E.urllib.request, "urlopen", fake_urlopen)
    E.Mailer(SETTINGS).send("a@mail.example", "Subject", "<p>x</p>", "x", key="septimus-1_a")
    assert seen["url"] == "https://api.resend.com/emails" and seen["method"] == "POST"
    assert seen["headers"]["Authorization"] == "Bearer re_test"
    assert seen["headers"]["Idempotency-key"] == "septimus-1_a" and seen["headers"]["User-agent"]
    assert b'"to": ["a@mail.example"]' in seen["body"] and b'"from"' in seen["body"]


def test_test_send_goes_only_to_the_counts_address_and_prints_no_address(monkeypatch, capsys):
    sent = []
    monkeypatch.setattr(E.Mailer, "send", lambda self, to, subject, html_body, text, key: sent.append((to, subject)))
    for name, value in (("RESEND_API_KEY", "re_x"), ("SEPTIMUS_EMAIL_FROM", "A <a@mail.example>"),
                        ("SEPTIMUS_SITE_URL", SITE), ("SEPTIMUS_COUNTS_TO", "simon@mail.example")):
        monkeypatch.setenv(name, value)
    assert E.main(["--test-send"]) == 0
    assert sent == [("simon@mail.example", "[TEST] Your stories this week (week 1)")]
    assert "mail.example" not in capsys.readouterr().out
    monkeypatch.delenv("SEPTIMUS_COUNTS_TO")
    assert E.main(["--test-send"]) == 1 and len(sent) == 1


def test_a_week_with_nothing_new_still_gets_a_short_email(order, details):
    """Someone still taking part who holds open stories but is handed nothing new hears from us anyway."""
    sid = order[0].id
    held = {"id": f"1_alice_{sid}", "uid": "alice", "storyId": sid, "round": 1, "week": 1,
            "doneAt": None, "releasedAt": None}
    store = MailStore([person("alice", 10, 1), person("bob", 0, 2), person("carol", 10, 3, pausedAt=5)],
                      rows=[held, {**held, "id": f"1_bob_{sid}", "uid": "bob"}, {**held, "id": f"1_carol_{sid}", "uid": "carol"}])
    store.runs[2] = {"startedAt": 1, "finishedAt": 102}          # week 2 is handed out; nobody got anything new
    mailer = E.Mailer(SETTINGS, post=(resend := FakeResend()), sleep=lambda s: None)
    result = E.send_weekly_emails(store, mailer, 2, list(store.rows.values()), store.users(), details,
                                  {"learned": 3}, 1800, 75)
    assert result["emailSent"] == 1                              # not bob (stopped), not carol (paused)
    (mail,) = resend.to("alice@mail.example")
    assert "Nothing new this week: you have 1 story still open from earlier weeks." in mail["text"]
    assert f"{SITE}/#/my" in mail["html"] and "minutes of learning" not in mail["html"]
