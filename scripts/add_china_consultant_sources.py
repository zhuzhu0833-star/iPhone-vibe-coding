#!/usr/bin/env python3
"""Add China consultant-focused sources to catalog.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catalog.json"
SELECTIONS = ROOT / "data" / "selections.json"

POLICY_EN = (
    "admission+OR+admissions+OR+application+OR+policy+OR+visa+OR+"
    "international+student+OR+enrollment+OR+enrolment"
)
POLICY_CN = (
    "留学+OR+学历认证+OR+涉外+OR+留学预警+OR+院校+OR+签证+OR+招生"
)
SEVP = "SEVIS+OR+SEVP+OR+international+student+OR+F-1+OR+student+visa"
UK_VISA = "student+visa+OR+graduate+route+OR+CAS+OR+visa+requirement"


def gn(domain: str, query: str, *, hl: str, gl: str, ceid: str) -> str:
    return (
        f"https://news.google.com/rss/search?q=site:{domain}+{query}"
        f"&hl={hl}&gl={gl}&ceid={ceid}"
    )


def src(sid: str, name: str, stype: str, url: str, domain: str) -> dict:
    return {
        "id": sid,
        "name": name,
        "type": stype,
        "domain": domain,
        "feed_type": "google_news",
        "url": url,
    }


CN = "zh-CN", "CN", "CN:zh-Hans"
US = "en-US", "US", "US:en"
UK = "en-GB", "GB", "GB:en"
GL = "en", "US", "US:en"

NEW_CN_COUNTRY = {
    "id": "cn",
    "name": "China",
    "flag": "🇨🇳",
    "sources": [
        src(
            "cn-cscse",
            "教育部留学服务中心 CSCSE",
            "policy",
            gn("cscse.edu.cn", POLICY_CN, hl=CN[0], gl=CN[1], ceid=CN[2]),
            "cscse.edu.cn",
        ),
        src(
            "cn-cscse-service",
            "CSCSE 学历认证服务",
            "policy",
            gn("zwfw.cscse.edu.cn", POLICY_CN, hl=CN[0], gl=CN[1], ceid=CN[2]),
            "zwfw.cscse.edu.cn",
        ),
        src(
            "cn-moe-study-warning",
            "教育部留学预警",
            "policy",
            gn("jsj.moe.gov.cn", POLICY_CN, hl=CN[0], gl=CN[1], ceid=CN[2]),
            "jsj.moe.gov.cn",
        ),
    ],
}

ADDITIONAL = {
    "global": [
        src(
            "global-pte",
            "PTE Academic",
            "policy",
            gn("pearsonpte.com", POLICY_EN, hl=GL[0], gl=GL[1], ceid=GL[2]),
            "pearsonpte.com",
        ),
    ],
    "us": [
        src(
            "us-sevp-ice",
            "SEVP / ICE",
            "policy",
            gn("ice.gov", SEVP, hl=US[0], gl=US[1], ceid=US[2]),
            "ice.gov",
        ),
    ],
    "uk": [
        src(
            "uk-home-office-student-visa",
            "UK Home Office Student Visa",
            "policy",
            gn("gov.uk", UK_VISA, hl=UK[0], gl=UK[1], ceid=UK[2]),
            "gov.uk",
        ),
    ],
}

NEW_IDS = [s["id"] for s in NEW_CN_COUNTRY["sources"]]
for sources in ADDITIONAL.values():
    NEW_IDS.extend(s["id"] for s in sources)

DEFAULT_ENABLE = NEW_IDS.copy()


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    if not any(c["id"] == "cn" for c in catalog["countries"]):
        catalog["countries"].insert(0, NEW_CN_COUNTRY)
    else:
        for country in catalog["countries"]:
            if country["id"] == "cn":
                existing = {s["id"] for s in country["sources"]}
                country["sources"].extend(
                    s for s in NEW_CN_COUNTRY["sources"] if s["id"] not in existing
                )

    for country in catalog["countries"]:
        cid = country["id"]
        if cid not in ADDITIONAL:
            continue
        existing = {s["id"] for s in country["sources"]}
        to_add = [s for s in ADDITIONAL[cid] if s["id"] not in existing]
        non_uni = [s for s in country["sources"] if s["type"] != "university"]
        unis = [s for s in country["sources"] if s["type"] == "university"]
        country["sources"] = non_uni + to_add + unis

    CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    selections = json.loads(SELECTIONS.read_text(encoding="utf-8"))
    enabled = selections.get("enabled_source_ids", [])
    for sid in DEFAULT_ENABLE:
        if sid not in enabled:
            enabled.append(sid)
    selections["enabled_source_ids"] = enabled
    SELECTIONS.write_text(json.dumps(selections, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Added {len(NEW_IDS)} China consultant sources, all enabled by default")


if __name__ == "__main__":
    main()
