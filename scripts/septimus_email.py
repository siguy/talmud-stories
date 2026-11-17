#!/usr/bin/env python3
"""Septimus sign-up: the emails (plan step e). Called by septimus_weekly.py; sends through Resend.

Three emails:
  weekly          one per person per campaign week: "Your stories this week", a card per story, one button
  still with us   one, to a person the script has just paused
  counts          to Simon after each hand-out: the numbers, and the alarm for a missed week

Never sent twice. Before a send the script creates sent/<key> in Firestore (create fails if it exists), and the
same key goes to Resend as its Idempotency-Key (Resend ignores a repeat of a key for 24 hours). After the send:
  - Resend accepted it           the sent/<key> record stays
  - Resend clearly refused it    the record is removed, so the next daily run tries again
  - no clear answer (timeout, server error)   the record stays: one missed email is better than two

Links that work without signing in. Each person has a private code (users/<uid>.mailToken, made here the first
time they are emailed). Every email carries it in two kinds of link: unsubscribe (the standard one-click header,
plus a link in the footer to a confirm page) and "Mark as learned" under each story. firestore.rules lets a
signed-out visitor holding that code switch emailOff or tick that person's story, and nothing else. A person
with emailOff set is not emailed.

Email is OFF unless RESEND_API_KEY is set, and a hand-out never depends on it: every failure here is counted,
logged without names, and left for the next run.

The repository is public, so Action logs are public: nothing here logs an address, a name or an id.

Environment (all read in Settings.from_env):
  RESEND_API_KEY          the Resend key. Not set = no email at all.
  SEPTIMUS_EMAIL_FROM     e.g. "Stories of the Talmud <talmud-stories@projects.simonbrief.com>"
  SEPTIMUS_SITE_URL       where the site lives, e.g. "https://talmud-stories-staging.vercel.app"
  SEPTIMUS_COUNTS_TO      Simon's address for the counts email (optional; without it no counts email)
  SEPTIMUS_EMAIL_ONLY_TO  optional, comma-separated. When set, ONLY these addresses are ever emailed. For
                          staging, where the test accounts have made-up addresses that must never be mailed.
"""
import html
import json
import logging
import math
import os
import secrets
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

LOG = logging.getLogger("septimus_email")
RESEND_URL = "https://api.resend.com/emails"
TITLE = "Stories of the Talmud"
DEDICATION = "In memory of Joe Septimus."      # Daniel's line goes after this when he supplies it
MAX_RATE_LIMIT_WAITS = 3                       # how many times one send waits out a "slow down" answer

# Colours and fonts from mockup 5 (docs/technical/signup-mockups/html/5-weekly-email.html).
NAVY, GOLD, PAPER, LINE, MUTED = "#18345d", "#ccb479", "#fbfbfa", "#e6e4df", "#666666"
SANS = "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Arial, sans-serif"
SERIF = "Georgia, 'Times New Roman', serif"


# ---------------------------------------------------------------- settings

@dataclass
class Settings:
    api_key: str
    sender: str
    site_url: str
    counts_to: str = ""
    only_to: frozenset = frozenset()

    @classmethod
    def from_env(cls, env=None):
        """Returns (settings, problem). (None, "") = email is simply off. (None, "…") = switched on but
        incomplete: the caller reports it and sends nothing."""
        env = os.environ if env is None else env
        key = (env.get("RESEND_API_KEY") or "").strip()
        if not key:
            return None, ""
        sender = (env.get("SEPTIMUS_EMAIL_FROM") or "").strip()
        site = (env.get("SEPTIMUS_SITE_URL") or "").strip().rstrip("/")
        missing = [name for name, value in (("SEPTIMUS_EMAIL_FROM", sender), ("SEPTIMUS_SITE_URL", site)) if not value]
        if missing:
            return None, "RESEND_API_KEY is set but " + " and ".join(missing) + " is not"
        only = frozenset(a.strip().lower() for a in (env.get("SEPTIMUS_EMAIL_ONLY_TO") or "").split(",") if a.strip())
        return cls(key, sender, site, (env.get("SEPTIMUS_COUNTS_TO") or "").strip(), only), ""

    def may_email(self, address):
        return not self.only_to or address.lower() in self.only_to


# ---------------------------------------------------------------- story details

def load_story_details(data_dir):
    """{story id: {"ref", "refs", "summary", "words"}} for every story in the data folder. The hand-out only
    needs ids and word counts; the email also shows the page reference and the one-line summary."""
    data_dir = Path(data_dir)
    index = json.loads((data_dir / "index.json").read_text())
    out = {}
    for t in index.get("tractates", []):
        path = data_dir / f"{t['tractate']}.json"
        if not path.exists():
            continue
        for s in json.loads(path.read_text()).get("stories", []):
            refs = s.get("refs")
            out[s["id"]] = {"ref": s.get("ref", ""), "refs": refs if isinstance(refs, list) else [],
                            "summary": s.get("summary") or "", "words": int(s.get("words") or 0)}
    return out


def ref_label(story):
    """'Berakhot 5b', or 'Berakhot 5b – 6a' for a story that runs over two pages (same rule as site/app.js)."""
    refs = story.get("refs") or []
    return f"{refs[0]} – {refs[1].split(' ')[-1]}" if len(refs) > 1 else story.get("ref", "")


def about_minutes(words, wpm):
    return max(1, math.ceil(words / wpm))


def first_name(display_name):
    parts = (display_name or "").split()
    return parts[0] if parts else ""


# ---------------------------------------------------------------- links that work without signing in

def new_mail_token():
    """A person's private code: 32 characters nobody can guess (letters, digits, - and _)."""
    return secrets.token_urlsafe(24)


def email_links(site_url, uid, token, week=None, story_ids=()):
    """The no-sign-in links for one person's email.
      header       what goes in List-Unsubscribe: the address a mail program POSTs to (site/api/unsubscribe.js)
      unsubscribe  the confirm page a person opens from the footer (site/unsubscribe.html)
      learned      {story id: the confirm page that ticks that story} (site/learned.html)"""
    who = f"u={uid}&t={token}"
    return {"header": f"{site_url}/api/unsubscribe?{who}",
            "unsubscribe": f"{site_url}/unsubscribe.html?{who}",
            "learned": {sid: f"{site_url}/learned.html?{who}&w={week}&s={sid}" for sid in story_ids}}


def unsubscribe_headers(links):
    """The two standard headers (RFC 8058) that put an Unsubscribe button in the mail program itself."""
    return {"List-Unsubscribe": f"<{links['header']}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}


# ---------------------------------------------------------------- rendering

def _esc(text):
    return html.escape(str(text), quote=True)


def _page(body_rows):
    """The outer shell: tables and inline styles only, because mail programs ignore most other CSS."""
    return (
        f'<!doctype html><html><body style="margin:0;padding:0;background-color:{PAPER};">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{PAPER};">'
        '<tr><td align="center">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;'
        f'font-family:{SANS};color:#222222;">'
        f'<tr><td style="background-color:{NAVY};padding:16px 20px;font-family:{SERIF};font-weight:700;'
        f'font-size:20px;color:#ffffff;">{TITLE}</td></tr>'
        f'<tr><td style="padding:24px 20px 32px 20px;">{body_rows}</td></tr>'
        '</table></td></tr></table></body></html>')


def _greeting(name):
    text = f"Hi {name}," if name else "Hello,"
    return f'<p style="margin:0 0 10px 0;font-family:{SERIF};font-size:18px;font-weight:700;">{_esc(text)}</p>'


def _button(label, url):
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td align="center" style="background-color:{NAVY};border-radius:6px;">'
            f'<a href="{_esc(url)}" style="display:block;padding:14px 16px;font-family:{SANS};font-size:16px;'
            f'font-weight:700;color:#ffffff;text-decoration:none;"><span style="color:#ffffff;">{_esc(label)}</span></a>'
            '</td></tr></table>')


def _card(story, url, minutes, learned_url=None):
    summary = (f'<div style="font-size:15px;line-height:1.45;color:{MUTED};margin:6px 0 10px 0;">'
               f'{_esc(story["summary"])}</div>') if story.get("summary") else '<div style="height:8px;"></div>'
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 12px 0;'
        f'background-color:#ffffff;border:1px solid {LINE};border-left:6px solid {GOLD};border-radius:10px;">'
        '<tr><td style="padding:14px 16px;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
        f'<td style="font-family:{SERIF};font-weight:700;font-size:18px;color:#222222;">{_esc(ref_label(story))}</td>'
        f'<td align="right"><a href="{_esc(url)}" style="color:{NAVY};font-weight:600;font-size:15px;">Read</a></td>'
        f'</tr></table>{summary}'
        f'<div style="font-size:13px;color:#888888;">about {minutes} min'
        + (f' &nbsp;·&nbsp; <a href="{_esc(learned_url)}" style="color:{NAVY};">Mark as learned</a>'
           if learned_url else '') + '</div>'
        '</td></tr></table>')


def _footer(lines):
    out = f'<hr style="border:none;border-top:1px solid {LINE};margin:28px 0 24px 0;">'
    out += (f'<div style="background-color:#f1efe9;padding:12px 14px;margin:0 0 24px 0;font-family:{SERIF};'
            f'font-style:italic;font-size:17px;line-height:1.5;">{_esc(DEDICATION)}</div>')
    for line in lines:
        out += f'<p style="margin:0 0 6px 0;font-size:13px;line-height:1.5;color:{MUTED};">{line}</p>'
    return out


def _link(label, url):
    return f'<a href="{_esc(url)}" style="color:{MUTED};">{_esc(label)}</a>'


def _foot_links(my_url, links):
    """The footer's links, as (label, url) pairs: change or stop on the site, and unsubscribe when we can."""
    out = [("Change my minutes or stop my stories", my_url)]
    if links:
        out.append(("Unsubscribe from these emails", links["unsubscribe"]))
    return out


def render_weekly(name, week, stories, open_older, learned, total, site_url, wpm, links=None):
    """Returns (subject, html, text). `stories`: this week's story detail dicts, each with "id", in order.
    `open_older`: how many stories from earlier weeks the person still has open. `links`: email_links(...)
    for this person, or None for an email without the no-sign-in links."""
    my_url = f"{site_url}/#/my"
    learned_url = (links or {}).get("learned", {})
    foot = _foot_links(my_url, links)
    minutes = [about_minutes(s["words"], wpm) for s in stories]
    count = "1 story" if len(stories) == 1 else f"{len(stories)} stories"
    intro = (f"Here {'is' if len(stories) == 1 else 'are'} your {'story' if len(stories) == 1 else 'stories'} "
             f"for this week, about {sum(minutes)} minutes of learning.")
    older = ""
    if not stories:                      # a week with nothing new still gets a short email (plan review, D)
        intro = (f"Nothing new this week: you have {open_older} "
                 f"{'story' if open_older == 1 else 'stories'} still open from earlier weeks.")
    elif open_older:
        older = (f"You also have {open_older} {'story' if open_older == 1 else 'stories'} still open "
                 f"from earlier weeks.")
    together = f"Together we have learned {learned:,} of about {total:,} stories." if total else ""
    subject = f"Your stories this week (week {week})"

    body = _greeting(name) + f'<p style="margin:0 0 24px 0;font-size:16px;line-height:1.5;">{_esc(intro)}</p>'
    body += "".join(_card(s, f"{site_url}/#/s/{s['id']}", m, learned_url.get(s["id"]))
                    for s, m in zip(stories, minutes))
    body += f'<div style="margin:12px 0 14px 0;">{_button("Open my stories", my_url)}</div>'
    if older:
        body += f'<p style="margin:0;font-size:14px;color:{MUTED};text-align:center;">{_esc(older)}</p>'
    body += _footer([_esc(together)] * bool(together) + [" &nbsp;·&nbsp; ".join(_link(*pair) for pair in foot)])

    text = [f"Hi {name}," if name else "Hello,", "", intro, ""]
    for s, m in zip(stories, minutes):
        text += [f"{ref_label(s)} (about {m} min)", s.get("summary", ""), f"Read: {site_url}/#/s/{s['id']}"]
        if s["id"] in learned_url:
            text.append(f"Mark as learned: {learned_url[s['id']]}")
        text.append("")
    text += [f"Open my stories ({count}): {my_url}" if stories else f"Open my stories: {my_url}", ""]
    text += [older, ""] * bool(older)
    text += [DEDICATION, together] + [f"{label}: {url}" for label, url in foot]
    return subject, _page(body), "\n".join(line for line in text if line is not None)


def render_still_with_us(name, site_url, links=None):
    """The one email a person gets when the script pauses them (plan section 6)."""
    my_url = f"{site_url}/#/my"
    foot = _foot_links(my_url, links)[1:]            # only the unsubscribe link, when there is one
    lines = ["We have not seen you mark a story as learned for a while, so we have paused your weekly stories "
             "and passed them to others.",
             "If you would like to carry on, open your stories and choose Resume. You will get new stories "
             "the following Sunday. If not, there is nothing to do: you will not hear from us again."]
    body = _greeting(name) + "".join(f'<p style="margin:0 0 16px 0;font-size:16px;line-height:1.5;">{_esc(p)}</p>'
                                     for p in lines)
    body += (f'<div style="margin:8px 0 0 0;">{_button("Open my stories", my_url)}</div>'
             + _footer([_link(*pair) for pair in foot]))
    text = "\n\n".join([f"Hi {name}," if name else "Hello,"] + lines + [f"Open my stories: {my_url}", DEDICATION]
                       + [f"{label}: {url}" for label, url in foot])
    return "Still with us?", _page(body), text


COUNT_LABELS = [
    ("users", "People signed up"), ("newSignups", "New since the last hand-out"),
    ("eligible", "People given stories"), ("totalMinutes", "Minutes committed this week"),
    ("handedOut", "Stories handed out"), ("released", "Stories handed back"), ("paused", "People paused"),
    ("deleted", "Delete requests done"), ("deleteFailed", "Delete requests that failed"),
    ("emailSent", "Weekly emails sent"), ("emailFailed", "Emails refused (retried on the next run)"),
    ("emailUnknown", "Emails with no clear answer (not retried)"),
    ("emailSkipped", "People not emailed (no address, emails off, or not on the test list)"),
    ("reads", "Database reads"),
]


def render_counts(counts, today):
    """Plain numbers for Simon. No names, no addresses."""
    week = counts.get("week")
    lines = [f"{label}: {counts.get(key, 0)}" for key, label in COUNT_LABELS]
    text = f"Septimus weekly run, {today}, campaign week {week}.\n\n" + "\n".join(lines) + "\n"
    rows = "".join(f'<tr><td style="padding:4px 16px 4px 0;">{_esc(label)}</td>'
                   f'<td align="right" style="padding:4px 0;font-weight:700;">{_esc(counts.get(key, 0))}</td></tr>'
                   for key, label in COUNT_LABELS)
    body = (f'<p style="margin:0 0 16px 0;font-size:16px;">Run of {_esc(today)}, campaign week {_esc(week)}.</p>'
            f'<table role="presentation" cellpadding="0" cellspacing="0" style="font-size:15px;">{rows}</table>')
    return f"Septimus week {week}: {counts.get('handedOut', 0)} stories to {counts.get('eligible', 0)} people", \
        _page(body), text


# ---------------------------------------------------------------- sending

class SendError(Exception):
    """A send that did not go through. `kind` is safe to log (never an address).
      refused   Resend clearly said no: nothing was sent, try again on the next run
      quota     the plan's daily or monthly limit is used up: nothing was sent, stop sending for this run
      unknown   no clear answer: it may have been sent, so it is NOT tried again"""

    def __init__(self, kind, detail=""):
        super().__init__(f"{kind} {detail}".strip())
        self.kind, self.detail = kind, detail


def _http_post(api_key, payload, idempotency_key, timeout=30):
    """One POST to Resend. Returns (status, parsed body, headers). Raises OSError when there is no answer."""
    request = urllib.request.Request(RESEND_URL, data=json.dumps(payload).encode(), method="POST", headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key, "User-Agent": "septimus-weekly/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status, raw, headers = response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as err:                      # an answer, just not a 2xx
        status, raw, headers = err.code, err.read(), dict(err.headers)
    try:
        body = json.loads(raw or b"{}")
    except ValueError:
        body = {}
    return status, body if isinstance(body, dict) else {}, {k.lower(): v for k, v in headers.items()}


class Mailer:
    """Sends one email through Resend. `post` and `sleep` can be replaced in tests."""

    def __init__(self, settings, post=None, sleep=time.sleep):
        self.settings = settings
        self._post = post or (lambda payload, key: _http_post(settings.api_key, payload, key))
        self._sleep = sleep

    def send(self, to, subject, html_body, text, key, headers=None):
        """Send, or raise SendError. `key` is the Idempotency-Key: Resend ignores a repeat for 24 hours.
        `headers`: extra email headers (the unsubscribe pair)."""
        payload = {"from": self.settings.sender, "to": [to], "subject": subject, "html": html_body, "text": text}
        if headers:
            payload["headers"] = headers
        for _attempt in range(MAX_RATE_LIMIT_WAITS + 1):
            try:
                status, body, headers = self._post(payload, key)
            except OSError as exc:                             # timeout, connection dropped: it may have gone out
                raise SendError("unknown", type(exc).__name__) from None
            if 200 <= status < 300:
                return
            name = str(body.get("name") or "")
            if status == 429 and "quota" in name:
                raise SendError("quota", name)
            if status == 429:                                  # too many a second: wait as long as Resend says
                try:
                    wait = float(headers.get("retry-after", 1))
                except ValueError:
                    wait = 1.0
                self._sleep(min(max(wait, 0.5), 30))
                continue
            if status == 409 or status >= 500:                 # a clash on the key, or Resend's own trouble
                raise SendError("unknown", f"{status} {name}".strip())
            raise SendError("refused", f"{status} {name}".strip())
        raise SendError("refused", "429 still rate limited")


def send_once(store, mailer, key, to, subject, html_body, text, uid="", week=None, headers=None):
    """Send one email at most once ever. Returns "sent", "already", "refused", "quota" or "unknown".
    `uid` and `week` are stored on the sent/<key> record: uid so "delete my data" can find it, week so one
    small query lists who has had this week's email (None for emails that are not the weekly one)."""
    if not store.claim_sent(key, uid, week):
        return "already"
    try:
        mailer.send(to, subject, html_body, text, key=f"septimus-{key}", headers=headers)
    except SendError as err:
        LOG.warning("an email was not sent: %s", err)
        if err.kind in ("refused", "quota"):
            store.unclaim_sent(key)                            # certainly not sent: the next run may try again
        return err.kind
    return "sent"


def _is_open(row):
    return not row.get("doneAt") and not row.get("releasedAt")


def _mail_token(store, user):
    """The person's private code, made and saved the first time it is needed. It never changes afterwards,
    so the links in an old email keep working."""
    if not user.get("mailToken"):
        user["mailToken"] = new_mail_token()
        store.update_user(user["uid"], {"mailToken": user["mailToken"]})
    return user["mailToken"]


def send_weekly_emails(store, mailer, week, rows, users, details, summary, total, wpm):
    """Email everyone who holds stories handed out in `week` and has not had this week's email, and everyone
    still taking part who got nothing new but has stories open from earlier weeks (a short "nothing new" email).

    Works from the rows, not from "who was served in this run", so a later daily run finishes a send that
    stopped halfway. Returns {"emailSent", "emailFailed", "emailUnknown", "emailSkipped", "emailDone"}."""
    result = {"emailSent": 0, "emailFailed": 0, "emailUnknown": 0, "emailSkipped": 0, "emailDone": False}
    users_by_uid = {u["uid"]: u for u in users}
    mine, older = {}, {}
    for r in rows:
        uid = r.get("uid")
        if not uid or uid not in users_by_uid:
            continue
        if r.get("week") == week and not r.get("releasedAt"):
            mine.setdefault(uid, []).append(r)
        elif r.get("week", 0) < week and _is_open(r):
            older[uid] = older.get(uid, 0) + 1
    for uid, u in users_by_uid.items():          # nothing new, but still taking part and still holding stories
        active = int(u.get("minutesPerWeek") or 0) > 0 and not u.get("pausedAt") and not u.get("deleteRequested")
        if uid not in mine and uid in older and active:
            mine[uid] = []
    already = store.sent_keys(week)
    todo = sorted(uid for uid in mine if f"{week}_{uid}" not in already)
    wanted = [uid for uid in todo if not users_by_uid[uid].get("emailOff")]
    result["emailSkipped"] = len(todo) - len(wanted)
    contacts = store.contacts(wanted) if wanted else {}
    out_of_quota = False
    for uid in wanted:
        address, display = contacts.get(uid, ("", ""))
        if not address or not mailer.settings.may_email(address):
            result["emailSkipped"] += 1
            continue
        if out_of_quota:
            result["emailFailed"] += 1
            continue
        stories = [{**details[r["storyId"]], "id": r["storyId"]} for r in mine[uid] if r["storyId"] in details]
        if not stories and not older.get(uid):
            result["emailSkipped"] += 1
            continue
        site = mailer.settings.site_url
        links = email_links(site, uid, _mail_token(store, users_by_uid[uid]), week, [s["id"] for s in stories])
        subject, html_body, text = render_weekly(first_name(display), week, stories, older.get(uid, 0),
                                                 summary.get("learned", 0), total, site, wpm, links)
        outcome = send_once(store, mailer, f"{week}_{uid}", address, subject, html_body, text, uid, week,
                            unsubscribe_headers(links))
        if outcome == "sent":
            result["emailSent"] += 1
        elif outcome == "unknown":
            result["emailUnknown"] += 1
        elif outcome in ("refused", "quota"):
            result["emailFailed"] += 1
            out_of_quota = outcome == "quota"
    result["emailDone"] = result["emailFailed"] == 0
    LOG.info("weekly emails, week %d: %d sent, %d refused, %d unclear, %d people not emailed",
             week, result["emailSent"], result["emailFailed"], result["emailUnknown"], result["emailSkipped"])
    return result


def send_pause_emails(store, mailer, week, uids, users=()):
    """One "still with us?" email to each person paused in this run. Tried once: no later run knows who they
    were. Not sent to someone who has unsubscribed."""
    sent = 0
    users_by_uid = {u["uid"]: u for u in users}
    uids = [uid for uid in uids if not users_by_uid.get(uid, {}).get("emailOff")]
    contacts = store.contacts(list(uids)) if uids else {}
    for uid in uids:
        address, display = contacts.get(uid, ("", ""))
        if not address or not mailer.settings.may_email(address):
            continue
        user = users_by_uid.get(uid)
        links = email_links(mailer.settings.site_url, uid, _mail_token(store, user)) if user else None
        subject, html_body, text = render_still_with_us(first_name(display), mailer.settings.site_url, links)
        sent += send_once(store, mailer, f"pause-{week}_{uid}", address, subject, html_body, text, uid,
                          headers=unsubscribe_headers(links) if links else None) == "sent"
    LOG.info("still-with-us emails: %d sent of %d people paused", sent, len(uids))
    return sent


def send_counts_email(mailer, counts, today):
    """The numbers to Simon. Not recorded in sent/: a second copy would do no harm, and Resend's key stops
    a repeat on the same day anyway."""
    to = mailer.settings.counts_to
    if not to:
        LOG.warning("SEPTIMUS_COUNTS_TO is not set: no counts email")
        return False
    subject, html_body, text = render_counts(counts, today)
    try:
        mailer.send(to, subject, html_body, text, key=f"septimus-counts-{counts.get('week')}-{today}")
    except SendError as err:
        LOG.warning("the counts email was not sent: %s", err)
        return False
    return True


# ---------------------------------------------------------------- preview

def main(argv=None):
    """Look at the weekly email without running the job.
      --preview FILE   write it as an HTML file to open in a browser; sends nothing
      --test-send      send that same sample email, once, to SEPTIMUS_COUNTS_TO (needs the email settings)"""
    import argparse
    ap = argparse.ArgumentParser(description="Septimus emails: preview the weekly email, or send one sample.")
    ap.add_argument("--preview", help="file to write the HTML to; sends nothing")
    ap.add_argument("--test-send", action="store_true", help="send one sample email to SEPTIMUS_COUNTS_TO")
    ap.add_argument("--data-dir", default=str(Path(__file__).resolve().parent.parent / "site" / "data"))
    ap.add_argument("--site-url", default=os.environ.get("SEPTIMUS_SITE_URL", "https://example.invalid"))
    args = ap.parse_args(argv)
    details = load_story_details(args.data_dir)
    stories = [{**d, "id": sid} for sid, d in list(details.items())[:3]]
    total = round(len(details) / 100) * 100

    def sample_links(site):      # a made-up person: the links show where they sit, but change nothing if pressed
        return email_links(site, "sample-person", "sample-code-that-opens-nothing", 1, [s["id"] for s in stories])

    if args.test_send:
        settings, problem = Settings.from_env()
        if settings is None or not settings.counts_to:
            print("not sent: " + (problem or "RESEND_API_KEY and SEPTIMUS_COUNTS_TO must both be set"))
            return 1
        subject, html_body, text = render_weekly("Simon", 1, stories, 1, 412, total, settings.site_url, 75,
                                                 sample_links(settings.site_url))
        try:
            Mailer(settings).send(settings.counts_to, "[TEST] " + subject, html_body, text,
                                  key=f"septimus-test-{int(time.time())}")
        except SendError as err:
            print(f"not sent: {err}")                          # the kind of failure only, never an address
            return 1
        print("test email sent to the counts address")
        return 0
    if not args.preview:
        ap.error("give --preview FILE or --test-send")
    site = args.site_url.rstrip("/")
    _subject, html_body, _text = render_weekly("Dana", 3, stories, 1, 412, total, site, 75, sample_links(site))
    Path(args.preview).write_text(html_body)
    print(f"wrote {args.preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
