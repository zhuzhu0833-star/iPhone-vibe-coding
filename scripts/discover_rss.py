#!/usr/bin/env python3
"""Try multiple RSS URL patterns per university and report working feeds."""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

import feedparser
import requests

UA = {"User-Agent": "StudyAbroadDigestBot/1.0"}

# name, domain, [candidate urls]
UNIVERSITIES: list[tuple[str, str, list[str]]] = [
    # US Top 20
    ("Princeton", "princeton.edu", [
        "https://www.princeton.edu/news/feed/all",
        "https://www.princeton.edu/news/feed",
    ]),
    ("MIT", "mit.edu", [
        "https://news.mit.edu/rss/topic/admissions",
        "https://news.mit.edu/rss/topic/education",
        "https://news.mit.edu/rss",
        "https://news.mit.edu/feed",
    ]),
    ("Harvard", "harvard.edu", [
        "https://news.harvard.edu/gazette/feed/",
        "https://news.harvard.edu/gazette/feed/rss/",
    ]),
    ("Stanford", "stanford.edu", [
        "https://news.stanford.edu/feed/",
        "https://news.stanford.edu/feed",
        "https://news.stanford.edu/rss",
    ]),
    ("Yale", "yale.edu", [
        "https://news.yale.edu/rss.xml",
        "https://news.yale.edu/feed",
        "https://news.yale.edu/rss",
    ]),
    ("Caltech", "caltech.edu", [
        "https://www.caltech.edu/about/news/rss",
        "https://www.caltech.edu/about/news/feed",
    ]),
    ("Duke", "duke.edu", [
        "https://today.duke.edu/rss.xml",
        "https://today.duke.edu/feed",
        "https://today.duke.edu/rss",
    ]),
    ("Johns Hopkins", "jhu.edu", [
        "https://hub.jhu.edu/feed/",
        "https://hub.jhu.edu/feed",
    ]),
    ("Northwestern", "northwestern.edu", [
        "https://news.northwestern.edu/rss/",
        "https://news.northwestern.edu/feed/",
        "https://news.northwestern.edu/rss.xml",
    ]),
    ("UPenn", "upenn.edu", [
        "https://penntoday.upenn.edu/feed/",
        "https://penntoday.upenn.edu/feed",
        "https://penntoday.upenn.edu/rss",
    ]),
    ("Cornell", "cornell.edu", [
        "https://news.cornell.edu/rss/",
        "https://news.cornell.edu/feed/",
        "https://news.cornell.edu/rss.xml",
    ]),
    ("UChicago", "uchicago.edu", [
        "https://news.uchicago.edu/rss/",
        "https://news.uchicago.edu/feed/",
        "https://news.uchicago.edu/rss.xml",
    ]),
    ("Brown", "brown.edu", [
        "https://www.brown.edu/news/feed",
        "https://www.brown.edu/news/rss",
        "https://news.brown.edu/feed",
    ]),
    ("Columbia", "columbia.edu", [
        "https://news.columbia.edu/rss",
        "https://news.columbia.edu/feed",
        "https://news.columbia.edu/rss.xml",
    ]),
    ("Dartmouth", "dartmouth.edu", [
        "https://home.dartmouth.edu/rss.xml",
        "https://home.dartmouth.edu/news/rss.xml",
        "https://news.dartmouth.edu/feed",
    ]),
    ("UCLA", "ucla.edu", [
        "https://newsroom.ucla.edu/rss.xml",
        "https://newsroom.ucla.edu/rss",
        "https://newsroom.ucla.edu/feed",
    ]),
    ("UC Berkeley", "berkeley.edu", [
        "https://news.berkeley.edu/feed/",
        "https://news.berkeley.edu/feed",
    ]),
    ("Rice", "rice.edu", [
        "https://news.rice.edu/rss.xml",
        "https://news.rice.edu/feed/",
        "https://news.rice.edu/feed",
    ]),
    ("Notre Dame", "nd.edu", [
        "https://news.nd.edu/feed/",
        "https://news.nd.edu/feed",
        "https://news.nd.edu/rss",
    ]),
    ("Vanderbilt", "vanderbilt.edu", [
        "https://news.vanderbilt.edu/feed/",
        "https://news.vanderbilt.edu/feed",
    ]),
    # UK QS top 200
    ("Oxford", "ox.ac.uk", [
        "https://www.ox.ac.uk/news-and-events/rss",
        "https://www.ox.ac.uk/news/feed",
        "https://www.ox.ac.uk/news/rss",
    ]),
    ("Cambridge", "cam.ac.uk", [
        "https://www.cam.ac.uk/news/rss",
        "https://www.cam.ac.uk/news/feed",
        "https://www.cam.ac.uk/rss/news.xml",
    ]),
    ("Imperial", "imperial.ac.uk", [
        "https://www.imperial.ac.uk/news/rss.xml",
        "https://www.imperial.ac.uk/news/feed/",
        "https://www.imperial.ac.uk/news-events/news/rss/",
    ]),
    ("UCL", "ucl.ac.uk", [
        "https://www.ucl.ac.uk/news/rss.xml",
        "https://www.ucl.ac.uk/news/feed",
    ]),
    ("Edinburgh", "ed.ac.uk", [
        "https://www.ed.ac.uk/news/rss",
        "https://www.ed.ac.uk/news/feed",
        "https://www.ed.ac.uk/news/rss.xml",
    ]),
    ("Manchester", "manchester.ac.uk", [
        "https://www.manchester.ac.uk/discover/news/feed/",
        "https://www.manchester.ac.uk/discover/news/rss/",
        "https://www.manchester.ac.uk/discover/news/rss",
    ]),
    ("KCL", "kcl.ac.uk", [
        "https://www.kcl.ac.uk/news/rss",
        "https://www.kcl.ac.uk/news/feed",
        "https://www.kcl.ac.uk/news/rss.xml",
    ]),
    ("LSE", "lse.ac.uk", [
        "https://www.lse.ac.uk/News/Latest-news-from-LSE/RSS",
        "https://www.lse.ac.uk/news/rss",
        "https://www.lse.ac.uk/news/feed",
    ]),
    ("Bristol", "bristol.ac.uk", [
        "https://www.bristol.ac.uk/news/rss/",
        "https://www.bristol.ac.uk/news/feed/",
        "https://www.bristol.ac.uk/news/rss.xml",
    ]),
    ("Warwick", "warwick.ac.uk", [
        "https://warwick.ac.uk/news/rss/",
        "https://warwick.ac.uk/news/feed/",
        "https://news.warwick.ac.uk/feed/",
    ]),
    ("Glasgow", "gla.ac.uk", [
        "https://www.gla.ac.uk/news/headline/news_rss/",
        "https://www.gla.ac.uk/news/rss/",
        "https://www.gla.ac.uk/news/feed/",
    ]),
    ("Birmingham", "birmingham.ac.uk", [
        "https://www.birmingham.ac.uk/news/rss",
        "https://www.birmingham.ac.uk/news/feed",
        "https://www.birmingham.ac.uk/news/rss.xml",
    ]),
    ("Southampton", "southampton.ac.uk", [
        "https://www.southampton.ac.uk/news/rss.page",
        "https://www.southampton.ac.uk/news/rss",
        "https://www.southampton.ac.uk/news/feed",
    ]),
    ("Leeds", "leeds.ac.uk", [
        "https://www.leeds.ac.uk/news/rss/",
        "https://www.leeds.ac.uk/news/feed/",
        "https://www.leeds.ac.uk/news/article/feed",
    ]),
    ("Sheffield", "sheffield.ac.uk", [
        "https://www.sheffield.ac.uk/news/rss",
        "https://www.sheffield.ac.uk/news/feed",
        "https://www.sheffield.ac.uk/news/rss.xml",
    ]),
    ("Nottingham", "nottingham.ac.uk", [
        "https://www.nottingham.ac.uk/news/rss",
        "https://www.nottingham.ac.uk/news/feed",
        "https://www.nottingham.ac.uk/news/rss.xml",
    ]),
    ("QMUL", "qmul.ac.uk", [
        "https://www.qmul.ac.uk/media/news/rss/",
        "https://www.qmul.ac.uk/news/rss",
        "https://www.qmul.ac.uk/news/feed",
    ]),
    ("Durham", "durham.ac.uk", [
        "https://www.durham.ac.uk/news/rss/",
        "https://www.durham.ac.uk/news/feed/",
        "https://www.durham.ac.uk/news-events/news/rss/",
    ]),
    ("St Andrews", "st-andrews.ac.uk", [
        "https://news.st-andrews.ac.uk/feed/",
        "https://news.st-andrews.ac.uk/feed",
    ]),
    ("Bath", "bath.ac.uk", [
        "https://www.bath.ac.uk/announcements/rss/",
        "https://www.bath.ac.uk/news/rss/",
        "https://www.bath.ac.uk/news/feed/",
    ]),
    ("Liverpool", "liverpool.ac.uk", [
        "https://news.liverpool.ac.uk/feed/",
        "https://news.liverpool.ac.uk/feed",
    ]),
    ("Exeter", "exeter.ac.uk", [
        "https://news.exeter.ac.uk/feed/",
        "https://news.exeter.ac.uk/feed",
    ]),
    ("York", "york.ac.uk", [
        "https://www.york.ac.uk/news-and-events/news/rss/",
        "https://www.york.ac.uk/news/rss/",
        "https://www.york.ac.uk/news/feed/",
    ]),
    ("Cardiff", "cardiff.ac.uk", [
        "https://www.cardiff.ac.uk/news/rss",
        "https://www.cardiff.ac.uk/news/feed",
    ]),
    ("Newcastle", "ncl.ac.uk", [
        "https://www.ncl.ac.uk/press/rss",
        "https://www.ncl.ac.uk/press/office/pressreleases/rss",
        "https://www.ncl.ac.uk/news/rss",
    ]),
    ("Reading", "reading.ac.uk", [
        "https://www.reading.ac.uk/news-and-events/rss",
        "https://www.reading.ac.uk/news/rss",
        "https://www.reading.ac.uk/news/feed",
    ]),
    ("Queen's Belfast", "qub.ac.uk", [
        "https://www.qub.ac.uk/News/AllNews/RSS/",
        "https://www.qub.ac.uk/news/rss",
    ]),
    ("Loughborough", "lboro.ac.uk", [
        "https://www.lboro.ac.uk/media-centre/rss/",
        "https://www.lboro.ac.uk/news/rss",
    ]),
    ("Sussex", "sussex.ac.uk", [
        "https://www.sussex.ac.uk/news/rss",
        "https://www.sussex.ac.uk/news/feed",
    ]),
    ("Surrey", "surrey.ac.uk", [
        "https://www.surrey.ac.uk/news/rss",
        "https://www.surrey.ac.uk/news/feed",
    ]),
    ("Leicester", "le.ac.uk", [
        "https://le.ac.uk/news/rss",
        "https://le.ac.uk/news/feed",
    ]),
    ("Aberdeen", "abdn.ac.uk", [
        "https://www.abdn.ac.uk/news/rss/",
        "https://www.abdn.ac.uk/news/feed/",
    ]),
    ("Lancaster", "lancaster.ac.uk", [
        "https://www.lancaster.ac.uk/news/rss/",
        "https://www.lancaster.ac.uk/news/feed/",
    ]),
    ("Heriot-Watt", "hw.ac.uk", [
        "https://www.hw.ac.uk/news/rss",
        "https://www.hw.ac.uk/news/feed",
    ]),
    ("Strathclyde", "strath.ac.uk", [
        "https://www.strath.ac.uk/whystrathclyde/news/rss/",
        "https://www.strath.ac.uk/pressoffice/news/rss/",
    ]),
    ("Kent", "kent.ac.uk", [
        "https://www.kent.ac.uk/news/rss",
        "https://www.kent.ac.uk/news/feed",
    ]),
    ("Royal Holloway", "royalholloway.ac.uk", [
        "https://www.royalholloway.ac.uk/about-us/news/rss/",
        "https://www.royalholloway.ac.uk/news/rss",
    ]),
    ("UEA", "uea.ac.uk", [
        "https://www.uea.ac.uk/about/-/media/uea/about/news/rss.xml",
        "https://www.uea.ac.uk/news/rss",
    ]),
    ("Dundee", "dundee.ac.uk", [
        "https://www.dundee.ac.uk/press-office/rss",
        "https://www.dundee.ac.uk/news/rss",
    ]),
    ("Essex", "essex.ac.uk", [
        "https://www.essex.ac.uk/news/rss",
        "https://www.essex.ac.uk/news/feed",
    ]),
    ("Stirling", "stir.ac.uk", [
        "https://www.stir.ac.uk/news/rss/",
        "https://www.stir.ac.uk/news/feed/",
    ]),
    ("Swansea", "swansea.ac.uk", [
        "https://www.swansea.ac.uk/press-office/news-events/rss/",
        "https://www.swansea.ac.uk/news/rss",
    ]),
    ("City St George's", "city.ac.uk", [
        "https://www.city.ac.uk/news-and-events/news/rss",
        "https://www.city.ac.uk/news/rss",
    ]),
    ("Brunel", "brunel.ac.uk", [
        "https://www.brunel.ac.uk/news/rss",
        "https://www.brunel.ac.uk/news/feed",
    ]),
    ("Aston", "aston.ac.uk", [
        "https://www.aston.ac.uk/latest-news/rss",
        "https://www.aston.ac.uk/news/rss",
    ]),
    ("SOAS", "soas.ac.uk", [
        "https://www.soas.ac.uk/news/rss",
        "https://www.soas.ac.uk/news/feed",
    ]),
    ("Goldsmiths", "gold.ac.uk", [
        "https://www.gold.ac.uk/news/rss/",
        "https://www.gold.ac.uk/news/feed/",
    ]),
    ("Birkbeck", "bbk.ac.uk", [
        "https://www.bbk.ac.uk/news/rss",
        "https://www.bbk.ac.uk/news/feed",
    ]),
    # Australia top universities
    ("Melbourne", "unimelb.edu.au", [
        "https://about.unimelb.edu.au/news-and-events/rss",
        "https://newsroom.unimelb.edu.au/rss",
        "https://newsroom.unimelb.edu.au/feed",
        "https://about.unimelb.edu.au/news/rss",
    ]),
    ("Sydney", "sydney.edu.au", [
        "https://www.sydney.edu.au/news-opinion/news/rss.xml",
        "https://www.sydney.edu.au/news-opinion/news/feed",
        "https://sydney.edu.au/news/rss.xml",
    ]),
    ("ANU", "anu.edu.au", [
        "https://www.anu.edu.au/news/all-news/rss.xml",
        "https://www.anu.edu.au/news/rss",
        "https://services.anu.edu.au/news/rss",
    ]),
    ("UNSW", "unsw.edu.au", [
        "https://www.unsw.edu.au/news/rss",
        "https://newsroom.unsw.edu.au/rss",
        "https://newsroom.unsw.edu.au/feed",
    ]),
    ("Monash", "monash.edu", [
        "https://www.monash.edu/news/articles/rss",
        "https://www.monash.edu/news/rss",
        "https://www.monash.edu/news/feed",
    ]),
    ("UQ", "uq.edu.au", [
        "https://www.uq.edu.au/news/rss",
        "https://www.uq.edu.au/news/feed",
        "https://communication.uq.edu.au/article-feed/rss",
    ]),
    ("UWA", "uwa.edu.au", [
        "https://www.uwa.edu.au/news/rss",
        "https://www.uwa.edu.au/news/feed",
        "https://news.uwa.edu.au/rss",
    ]),
    ("Adelaide", "adelaide.edu.au", [
        "https://www.adelaide.edu.au/news/rss",
        "https://www.adelaide.edu.au/news/feed",
        "https://www.adelaide.edu.au/news/list/rss",
    ]),
    ("UTS", "uts.edu.au", [
        "https://www.uts.edu.au/about/faculty-staff/news/rss",
        "https://www.uts.edu.au/about/news-events/news/rss",
        "https://www.uts.edu.au/news/rss",
    ]),
    ("Macquarie", "mq.edu.au", [
        "https://www.mq.edu.au/news/rss",
        "https://www.mq.edu.au/news/feed",
        "https://lighthouse.mq.edu.au/rss",
    ]),
    ("RMIT", "rmit.edu.au", [
        "https://www.rmit.edu.au/news/rss",
        "https://www.rmit.edu.au/news/all-news/rss",
        "https://www.rmit.edu.au/news/feed",
    ]),
    ("QUT", "qut.edu.au", [
        "https://www.qut.edu.au/news/rss",
        "https://www.qut.edu.au/news/latest-news/rss",
        "https://www.qut.edu.au/news/feed",
    ]),
    # Canada top universities
    ("Toronto", "utoronto.ca", [
        "https://www.utoronto.ca/news/rss.xml",
        "https://www.utoronto.ca/news/feed",
        "https://news.utoronto.ca/rss",
        "https://news.utoronto.ca/feed",
    ]),
    ("UBC", "ubc.ca", [
        "https://news.ubc.ca/feed/",
        "https://news.ubc.ca/feed",
        "https://www.ubc.ca/news/rss.xml",
    ]),
    ("McGill", "mcgill.ca", [
        "https://www.mcgill.ca/newsroom/articles/rss",
        "https://www.mcgill.ca/newsroom/rss",
        "https://www.mcgill.ca/newsroom/feed",
        "https://www.mcgill.ca/news/rss",
    ]),
    ("Waterloo", "uwaterloo.ca", [
        "https://uwaterloo.ca/news/rss",
        "https://uwaterloo.ca/news/feed",
        "https://uwaterloo.ca/news/news/rss",
    ]),
    ("Alberta", "ualberta.ca", [
        "https://www.ualberta.ca/folio/rss.xml",
        "https://www.ualberta.ca/news/rss",
        "https://www.ualberta.ca/news/feed",
    ]),
    ("McMaster", "mcmaster.ca", [
        "https://news.mcmaster.ca/rss",
        "https://news.mcmaster.ca/feed",
        "https://dailynews.mcmaster.ca/rss",
    ]),
    ("Montreal", "umontreal.ca", [
        "https://nouvelles.umontreal.ca/rss",
        "https://www.umontreal.ca/english/news/rss",
        "https://www.umontreal.ca/en/news/rss",
    ]),
    ("Queen's", "queensu.ca", [
        "https://www.queensu.ca/gazette/rss",
        "https://www.queensu.ca/news/rss",
        "https://www.queensu.ca/news/feed",
    ]),
    ("Western", "uwo.ca", [
        "https://news.westernu.ca/feed/",
        "https://news.westernu.ca/feed",
        "https://www.uwo.ca/news/rss",
    ]),
    ("Ottawa", "uottawa.ca", [
        "https://www.uottawa.ca/about-us/news/rss",
        "https://www.uottawa.ca/about-us/administration-services/communications/news/rss",
        "https://www.uottawa.ca/news/rss",
    ]),
    ("Calgary", "ucalgary.ca", [
        "https://www.ucalgary.ca/news/rss",
        "https://news.ucalgary.ca/rss",
        "https://news.ucalgary.ca/feed",
    ]),
    ("SFU", "sfu.ca", [
        "https://www.sfu.ca/sfunews/rss",
        "https://www.sfu.ca/sfunews/feed",
        "https://www.sfu.ca/sfunews.html/rss",
    ]),
]


def try_url(url: str) -> tuple[bool, int, str]:
    try:
        r = requests.get(url, timeout=12, headers=UA, allow_redirects=True)
        if r.status_code != 200:
            return False, 0, f"HTTP {r.status_code}"
        feed = feedparser.parse(r.content)
        n = len(feed.entries)
        if n == 0:
            if feed.bozo:
                return False, 0, str(feed.bozo_exception)[:50]
            return False, 0, "empty feed"
        return True, n, "ok"
    except Exception as exc:
        return False, 0, str(exc)[:50]


def discover_one(name: str, domain: str, urls: list[str]) -> dict:
    for url in urls:
        ok, count, msg = try_url(url)
        if ok:
            return {"name": name, "domain": domain, "rss": url, "entries": count, "status": "ok"}
    return {"name": name, "domain": domain, "rss": None, "entries": 0, "status": "no_rss", "tried": urls}


def main() -> int:
    results = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(discover_one, name, domain, urls): name
            for name, domain, urls in UNIVERSITIES
        }
        for fut in as_completed(futures):
            results.append(fut.result())

    results.sort(key=lambda x: x["name"])
    ok = [r for r in results if r["status"] == "ok"]
    fail = [r for r in results if r["status"] != "ok"]

    print(f"=== VERIFIED OFFICIAL RSS ({len(ok)}/{len(results)}) ===\n")
    for r in ok:
        print(f"{r['name']:22} {r['entries']:3}  {r['rss']}")

    print(f"\n=== NO WORKING RSS ({len(fail)}) — use Google News fallback ===\n")
    for r in fail:
        print(f"{r['name']:22}  site:{r['domain']}")

    out = ROOT / "data" / "rss_discovery.json"
    out.write_text(json.dumps({"verified": ok, "fallback": fail}, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
