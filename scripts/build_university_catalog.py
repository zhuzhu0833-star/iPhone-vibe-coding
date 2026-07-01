#!/usr/bin/env python3
"""Generate university source entries for catalog.json from rss_discovery.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DISCOVERY = ROOT / "data" / "rss_discovery.json"

ADMISSION_QUERY = (
    "admission+OR+admissions+OR+tuition+OR+scholarship+"
    "OR+enrolment+OR+intake+OR+application+deadline"
)

US_TOP_20 = [
    ("us-princeton-university", "Princeton University", "princeton.edu"),
    ("us-mit", "MIT", "mit.edu"),
    ("us-harvard-university", "Harvard University", "harvard.edu"),
    ("us-stanford-university", "Stanford University", "stanford.edu"),
    ("us-yale-university", "Yale University", "yale.edu"),
    ("us-caltech", "Caltech", "caltech.edu"),
    ("us-duke-university", "Duke University", "duke.edu"),
    ("us-johns-hopkins-university", "Johns Hopkins University", "jhu.edu"),
    ("us-northwestern-university", "Northwestern University", "northwestern.edu"),
    ("us-upenn", "University of Pennsylvania", "upenn.edu"),
    ("us-cornell-university", "Cornell University", "cornell.edu"),
    ("us-uchicago", "University of Chicago", "uchicago.edu"),
    ("us-brown-university", "Brown University", "brown.edu"),
    ("us-columbia-university", "Columbia University", "columbia.edu"),
    ("us-dartmouth-college", "Dartmouth College", "dartmouth.edu"),
    ("us-ucla", "UCLA", "ucla.edu"),
    ("us-uc-berkeley", "UC Berkeley", "berkeley.edu"),
    ("us-rice-university", "Rice University", "rice.edu"),
    ("us-notre-dame", "University of Notre Dame", "nd.edu"),
    ("us-vanderbilt-university", "Vanderbilt University", "vanderbilt.edu"),
]

UK_QS_TOP_200 = [
    ("uk-imperial-college-london", "Imperial College London", "imperial.ac.uk"),
    ("uk-university-of-oxford", "University of Oxford", "ox.ac.uk"),
    ("uk-university-of-cambridge", "University of Cambridge", "cam.ac.uk"),
    ("uk-ucl", "UCL", "ucl.ac.uk"),
    ("uk-university-of-edinburgh", "University of Edinburgh", "ed.ac.uk"),
    ("uk-university-of-manchester", "University of Manchester", "manchester.ac.uk"),
    ("uk-kings-college-london", "King's College London", "kcl.ac.uk"),
    ("uk-lse", "London School of Economics", "lse.ac.uk"),
    ("uk-university-of-bristol", "University of Bristol", "bristol.ac.uk"),
    ("uk-university-of-warwick", "University of Warwick", "warwick.ac.uk"),
    ("uk-university-of-glasgow", "University of Glasgow", "gla.ac.uk"),
    ("uk-university-of-birmingham", "University of Birmingham", "birmingham.ac.uk"),
    ("uk-university-of-southampton", "University of Southampton", "southampton.ac.uk"),
    ("uk-university-of-leeds", "University of Leeds", "leeds.ac.uk"),
    ("uk-university-of-sheffield", "University of Sheffield", "sheffield.ac.uk"),
    ("uk-durham-university", "Durham University", "durham.ac.uk"),
    ("uk-university-of-nottingham", "University of Nottingham", "nottingham.ac.uk"),
    ("uk-qmul", "Queen Mary University of London", "qmul.ac.uk"),
    ("uk-university-of-st-andrews", "University of St Andrews", "st-andrews.ac.uk"),
    ("uk-university-of-bath", "University of Bath", "bath.ac.uk"),
    ("uk-university-of-liverpool", "University of Liverpool", "liverpool.ac.uk"),
    ("uk-university-of-exeter", "University of Exeter", "exeter.ac.uk"),
    ("uk-university-of-york", "University of York", "york.ac.uk"),
    ("uk-newcastle-university", "Newcastle University", "ncl.ac.uk"),
    ("uk-cardiff-university", "Cardiff University", "cardiff.ac.uk"),
    ("uk-queens-university-belfast", "Queen's University Belfast", "qub.ac.uk"),
    ("uk-loughborough-university", "Loughborough University", "lboro.ac.uk"),
    ("uk-university-of-reading", "University of Reading", "reading.ac.uk"),
    ("uk-university-of-sussex", "University of Sussex", "sussex.ac.uk"),
    ("uk-university-of-surrey", "University of Surrey", "surrey.ac.uk"),
    ("uk-university-of-leicester", "University of Leicester", "le.ac.uk"),
    ("uk-university-of-aberdeen", "University of Aberdeen", "abdn.ac.uk"),
    ("uk-lancaster-university", "Lancaster University", "lancaster.ac.uk"),
    ("uk-heriot-watt-university", "Heriot-Watt University", "hw.ac.uk"),
    ("uk-university-of-strathclyde", "University of Strathclyde", "strath.ac.uk"),
    ("uk-university-of-kent", "University of Kent", "kent.ac.uk"),
    ("uk-royal-holloway", "Royal Holloway, University of London", "royalholloway.ac.uk"),
    ("uk-uea", "University of East Anglia", "uea.ac.uk"),
    ("uk-university-of-dundee", "University of Dundee", "dundee.ac.uk"),
    ("uk-university-of-essex", "University of Essex", "essex.ac.uk"),
    ("uk-university-of-stirling", "University of Stirling", "stir.ac.uk"),
    ("uk-swansea-university", "Swansea University", "swansea.ac.uk"),
    ("uk-city-st-georges", "City St George's, University of London", "city.ac.uk"),
    ("uk-brunel-university", "Brunel University London", "brunel.ac.uk"),
    ("uk-aston-university", "Aston University", "aston.ac.uk"),
    ("uk-soas", "SOAS University of London", "soas.ac.uk"),
    ("uk-goldsmiths", "Goldsmiths, University of London", "gold.ac.uk"),
    ("uk-birkbeck", "Birkbeck, University of London", "bbk.ac.uk"),
]

# Map display names from discovery to domains
NAME_TO_DOMAIN: dict[str, str] = {}
for _id, name, domain in US_TOP_20 + UK_QS_TOP_200:
    short = re.sub(r"^University of ", "", name)
    NAME_TO_DOMAIN[name] = domain
    NAME_TO_DOMAIN[short] = domain


def google_news_url(domain: str, *, uk: bool = False) -> str:
    if uk:
        return (
            f"https://news.google.com/rss/search?q=site:{domain}+{ADMISSION_QUERY}"
            f"&hl=en-GB&gl=GB&ceid=GB:en"
        )
    return (
        f"https://news.google.com/rss/search?q=site:{domain}+{ADMISSION_QUERY}"
        f"&hl=en-US&gl=US&ceid=US:en"
    )


def load_verified() -> dict[str, str]:
    data = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    verified: dict[str, str] = {}
    for item in data.get("verified", []):
        domain = item.get("domain") or NAME_TO_DOMAIN.get(item["name"], "")
        if domain:
            verified[domain] = item["rss"]
    return verified


def make_entry(
    source_id: str, name: str, domain: str, verified: dict[str, str], *, uk: bool = False
) -> dict:
    fallback = google_news_url(domain, uk=uk)
    rss = verified.get(domain)
    if rss:
        return {
            "id": source_id,
            "name": name,
            "type": "university",
            "domain": domain,
            "feed_type": "official_rss",
            "url": rss,
            "fallback_url": fallback,
        }
    return {
        "id": source_id,
        "name": name,
        "type": "university",
        "domain": domain,
        "feed_type": "google_news",
        "url": fallback,
    }


def main() -> None:
    verified = load_verified()
    catalog = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))

    for country in catalog["countries"]:
        if country["id"] == "us":
            non_uni = [s for s in country["sources"] if s["type"] != "university"]
            country["sources"] = non_uni + [
                make_entry(sid, name, domain, verified) for sid, name, domain in US_TOP_20
            ]
        elif country["id"] == "uk":
            non_uni = [s for s in country["sources"] if s["type"] != "university"]
            country["sources"] = non_uni + [
                make_entry(sid, name, domain, verified, uk=True)
                for sid, name, domain in UK_QS_TOP_200
            ]

    out = ROOT / "data" / "catalog.json"
    out.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    us_rss = sum(1 for _, n, d in US_TOP_20 if d in verified)
    uk_rss = sum(1 for _, n, d in UK_QS_TOP_200 if d in verified)
    print(f"Updated {out}")
    print(f"US: {us_rss}/20 official RSS, UK: {uk_rss}/{len(UK_QS_TOP_200)} official RSS")


if __name__ == "__main__":
    main()
