#!/usr/bin/env python3
"""Add policy, education, and media sources to catalog.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catalog.json"

ADMISSIONS = (
    "admission+OR+admissions+OR+application+OR+enrollment+OR+enrolment+"
    "OR+international+student+OR+policy+OR+tuition+OR+scholarship"
)
POLICY = (
    "admission+OR+admissions+OR+application+OR+policy+OR+visa+OR+"
    "international+student+OR+enrollment+OR+enrolment"
)
MEDIA = (
    "international+student+OR+admission+OR+admissions+OR+visa+OR+"
    "policy+OR+enrollment+OR+enrolment+OR+tuition"
)


def gn(domain: str, query: str, *, hl: str, gl: str, ceid: str) -> str:
    return (
        f"https://news.google.com/rss/search?q=site:{domain}+{query}"
        f"&hl={hl}&gl={gl}&ceid={ceid}"
    )


def src(sid: str, name: str, stype: str, url: str, domain: str | None = None) -> dict:
    entry: dict = {"id": sid, "name": name, "type": stype, "url": url}
    if domain:
        entry["domain"] = domain
        entry["feed_type"] = "google_news"
    return entry


US = "en-US", "US", "US:en"
UK = "en-GB", "GB", "GB:en"
AU = "en-AU", "AU", "AU:en"
CA = "en-CA", "CA", "CA:en"
GL = "en", "US", "US:en"


NEW_BY_COUNTRY: dict[str, list[dict]] = {
    "us": [
        src("us-college-board", "College Board", "policy", gn("collegeboard.org", POLICY, hl=US[0], gl=US[1], ceid=US[2]), "collegeboard.org"),
        src("us-common-app", "Common App", "policy", gn("commonapp.org", POLICY, hl=US[0], gl=US[1], ceid=US[2]), "commonapp.org"),
        src("us-iie", "IIE / Open Doors", "policy", gn("iie.org", POLICY, hl=US[0], gl=US[1], ceid=US[2]), "iie.org"),
        src("us-nafsa", "NAFSA", "education", gn("nafsa.org", POLICY, hl=US[0], gl=US[1], ceid=US[2]), "nafsa.org"),
        src("us-nacac", "NACAC", "policy", gn("nacacnet.org", POLICY, hl=US[0], gl=US[1], ceid=US[2]), "nacacnet.org"),
        src("us-ed-gov", "US Dept. of Education", "policy", gn("ed.gov", POLICY, hl=US[0], gl=US[1], ceid=US[2]), "ed.gov"),
        src("us-ets", "ETS / TOEFL", "policy", gn("ets.org", POLICY, hl=US[0], gl=US[1], ceid=US[2]), "ets.org"),
        src("us-inside-higher-ed", "Inside Higher Ed", "media", gn("insidehighered.com", MEDIA, hl=US[0], gl=US[1], ceid=US[2]), "insidehighered.com"),
    ],
    "uk": [
        src("uk-ucas", "UCAS", "policy", gn("ucas.com", POLICY, hl=UK[0], gl=UK[1], ceid=UK[2]), "ucas.com"),
        src("uk-ofs", "Office for Students", "policy", gn("officeforstudents.org.uk", POLICY, hl=UK[0], gl=UK[1], ceid=UK[2]), "officeforstudents.org.uk"),
        src("uk-hesa", "HESA", "policy", gn("hesa.ac.uk", POLICY, hl=UK[0], gl=UK[1], ceid=UK[2]), "hesa.ac.uk"),
        src("uk-british-council", "British Council Education", "education", gn("britishcouncil.org", POLICY, hl=UK[0], gl=UK[1], ceid=UK[2]), "britishcouncil.org"),
        src("uk-russell-group", "Russell Group", "policy", gn("russellgroup.ac.uk", POLICY, hl=UK[0], gl=UK[1], ceid=UK[2]), "russellgroup.ac.uk"),
        src("uk-times-higher-education", "Times Higher Education", "media", gn("timeshighereducation.com", MEDIA, hl=UK[0], gl=UK[1], ceid=UK[2]), "timeshighereducation.com"),
    ],
    "au": [
        src("au-teqsa", "TEQSA", "policy", gn("teqsa.gov.au", POLICY, hl=AU[0], gl=AU[1], ceid=AU[2]), "teqsa.gov.au"),
        src("au-education-gov", "Australian Dept. of Education", "policy", gn("education.gov.au", POLICY, hl=AU[0], gl=AU[1], ceid=AU[2]), "education.gov.au"),
    ],
    "ca": [
        src("ca-cbie", "CBIE", "education", gn("cbie.ca", POLICY, hl=CA[0], gl=CA[1], ceid=CA[2]), "cbie.ca"),
        src("ca-universities-canada", "Universities Canada", "education", gn("universitiescanada.ca", POLICY, hl=CA[0], gl=CA[1], ceid=CA[2]), "universitiescanada.ca"),
    ],
}

GLOBAL_COUNTRY = {
    "id": "global",
    "name": "International",
    "flag": "🌍",
    "sources": [
        src("global-pie-news", "The PIE News", "media", gn("thepienews.com", MEDIA, hl=GL[0], gl=GL[1], ceid=GL[2]), "thepienews.com"),
        src("global-icef-monitor", "ICEF Monitor", "media", gn("monitor.icef.com", MEDIA, hl=GL[0], gl=GL[1], ceid=GL[2]), "monitor.icef.com"),
        src("global-university-world-news", "University World News", "media", gn("universityworldnews.com", MEDIA, hl=GL[0], gl=GL[1], ceid=GL[2]), "universityworldnews.com"),
        src("global-ielts", "IELTS", "policy", gn("ielts.org", POLICY, hl=GL[0], gl=GL[1], ceid=GL[2]), "ielts.org"),
        src("global-duolingo-english-test", "Duolingo English Test", "policy", gn("englishtest.duolingo.com", POLICY, hl=GL[0], gl=GL[1], ceid=GL[2]), "englishtest.duolingo.com"),
    ],
}

# Re-type key immigration sources as policy for admissions focus
RETYPE = {
    "ca-ircc-news": "policy",
    "ca-ircc-google-news": "policy",
    "uk-gov-uk-immigration": "policy",
}

NEW_IDS = [s["id"] for sources in NEW_BY_COUNTRY.values() for s in sources]
NEW_IDS += [s["id"] for s in GLOBAL_COUNTRY["sources"]]

DEFAULT_POLICY_IDS = [
    # US
    "us-study-in-the-states",
    "us-college-board",
    "us-common-app",
    "us-iie",
    "us-nafsa",
    "us-nacac",
    "us-inside-higher-ed",
    "us-ets",
    # UK
    "uk-ukcisa",
    "uk-ucas",
    "uk-ofs",
    "uk-hesa",
    "uk-british-council",
    "uk-russell-group",
    "uk-times-higher-education",
    "uk-gov-uk-immigration",
    # AU
    "au-study-australia",
    "au-department-of-home-affairs",
    "au-teqsa",
    "au-education-gov",
    # CA
    "ca-ircc-news",
    "ca-cbie",
    "ca-universities-canada",
    # Global
    "global-pie-news",
    "global-icef-monitor",
    "global-university-world-news",
    "global-ielts",
    "global-duolingo-english-test",
]


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    for country in catalog["countries"]:
        cid = country["id"]
        if cid in NEW_BY_COUNTRY:
            existing_ids = {s["id"] for s in country["sources"]}
            to_add = [s for s in NEW_BY_COUNTRY[cid] if s["id"] not in existing_ids]
            non_uni = [s for s in country["sources"] if s["type"] != "university"]
            unis = [s for s in country["sources"] if s["type"] == "university"]
            country["sources"] = non_uni + to_add + unis

        for source in country["sources"]:
            if source["id"] in RETYPE:
                source["type"] = RETYPE[source["id"]]

    if not any(c["id"] == "global" for c in catalog["countries"]):
        catalog["countries"].insert(0, GLOBAL_COUNTRY)

    CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    selections_path = ROOT / "data" / "selections.json"
    selections = json.loads(selections_path.read_text(encoding="utf-8"))
    enabled = list(selections.get("enabled_source_ids", []))
    for pid in DEFAULT_POLICY_IDS:
        if pid not in enabled:
            enabled.append(pid)
    selections["enabled_source_ids"] = enabled
    selections_path.write_text(json.dumps(selections, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Added {len(NEW_IDS)} new catalog sources")
    print(f"Default policy/media enabled: {len(DEFAULT_POLICY_IDS)}")


if __name__ == "__main__":
    main()
