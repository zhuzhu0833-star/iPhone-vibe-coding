#!/usr/bin/env python3
"""Verify RSS feed URLs return valid feeds."""

from __future__ import annotations

import sys
from urllib.parse import urlparse

import feedparser
import requests

CANDIDATES: list[tuple[str, str]] = [
    # US Top 20
    ("Princeton", "https://www.princeton.edu/news/feed/all"),
    ("MIT", "https://news.mit.edu/rss"),
    ("Harvard", "https://news.harvard.edu/gazette/feed/"),
    ("Stanford", "https://news.stanford.edu/feed/"),
    ("Yale", "https://news.yale.edu/rss.xml"),
    ("Caltech", "https://www.caltech.edu/about/news/rss"),
    ("Duke", "https://today.duke.edu/rss.xml"),
    ("Johns Hopkins", "https://hub.jhu.edu/feed/"),
    ("Northwestern", "https://news.northwestern.edu/rss/"),
    ("UPenn", "https://penntoday.upenn.edu/feed/"),
    ("Cornell", "https://news.cornell.edu/rss/"),
    ("UChicago", "https://news.uchicago.edu/rss/"),
    ("Brown", "https://www.brown.edu/news/feed"),
    ("Columbia", "https://news.columbia.edu/rss"),
    ("Dartmouth", "https://home.dartmouth.edu/news/rss.xml"),
    ("UCLA", "https://newsroom.ucla.edu/rss"),
    ("UC Berkeley", "https://news.berkeley.edu/feed/"),
    ("Rice", "https://news.rice.edu/rss.xml"),
    ("Notre Dame", "https://news.nd.edu/feed/"),
    ("Vanderbilt", "https://news.vanderbilt.edu/feed/"),
    # UK QS top 200 (representative list)
    ("Oxford", "https://www.ox.ac.uk/news-and-events/rss"),
    ("Cambridge", "https://www.cam.ac.uk/news/rss"),
    ("Imperial", "https://www.imperial.ac.uk/news/rss.xml"),
    ("UCL", "https://www.ucl.ac.uk/news/rss.xml"),
    ("Edinburgh", "https://www.ed.ac.uk/news/rss"),
    ("Manchester", "https://www.manchester.ac.uk/discover/news/rss/"),
    ("KCL", "https://www.kcl.ac.uk/news/rss"),
    ("LSE", "https://www.lse.ac.uk/News/Latest-news-from-LSE/RSS"),
    ("Bristol", "https://www.bristol.ac.uk/news/rss/"),
    ("Warwick", "https://warwick.ac.uk/news/rss/"),
    ("Glasgow", "https://www.gla.ac.uk/news/headline/news_rss/"),
    ("Birmingham", "https://www.birmingham.ac.uk/news/rss"),
    ("Southampton", "https://www.southampton.ac.uk/news/rss.page"),
    ("Leeds", "https://www.leeds.ac.uk/news/rss/"),
    ("Sheffield", "https://www.sheffield.ac.uk/news/rss"),
    ("Nottingham", "https://www.nottingham.ac.uk/news/rss"),
    ("QMUL", "https://www.qmul.ac.uk/media/news/rss/"),
    ("Durham", "https://www.durham.ac.uk/news/rss/"),
    ("St Andrews", "https://news.st-andrews.ac.uk/feed/"),
    ("Exeter", "https://news.exeter.ac.uk/feed/"),
    ("Liverpool", "https://news.liverpool.ac.uk/feed/"),
    ("York", "https://www.york.ac.uk/news-and-events/news/rss/"),
    ("Cardiff", "https://www.cardiff.ac.uk/news/rss"),
    ("Newcastle", "https://www.ncl.ac.uk/press/rss"),
    ("Bath", "https://www.bath.ac.uk/announcements/rss/"),
    ("Reading", "https://www.reading.ac.uk/news-and-events/rss"),
    ("Queen's Belfast", "https://www.qub.ac.uk/News/AllNews/RSS/"),
    ("Loughborough", "https://www.lboro.ac.uk/media-centre/rss/"),
    ("Sussex", "https://www.sussex.ac.uk/news/rss"),
    ("Surrey", "https://www.surrey.ac.uk/news/rss"),
    ("Leicester", "https://le.ac.uk/news/rss"),
    ("Aberdeen", "https://www.abdn.ac.uk/news/rss/"),
]


def verify(name: str, url: str) -> tuple[bool, int, str]:
    try:
        r = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "StudyAbroadDigestBot/1.0"},
            allow_redirects=True,
        )
        if r.status_code != 200:
            return False, 0, f"HTTP {r.status_code}"
        feed = feedparser.parse(r.content)
        if feed.bozo and not feed.entries:
            return False, 0, str(feed.bozo_exception)[:60]
        return True, len(feed.entries), "ok"
    except Exception as exc:
        return False, 0, str(exc)[:60]


def main() -> None:
    ok_list = []
    fail_list = []
    for name, url in CANDIDATES:
        ok, count, msg = verify(name, url)
        if ok and count > 0:
            ok_list.append((name, url, count))
            print(f"OK  {name:20} {count:3} entries  {url}")
        else:
            fail_list.append((name, url, msg))
            print(f"FAIL {name:20} {msg:20} {url}")
    print(f"\n{len(ok_list)} ok, {len(fail_list)} failed")
    return 0 if ok_list else 1


if __name__ == "__main__":
    sys.exit(main())
