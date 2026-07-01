# 院校官方 RSS 探测结果

探测时间：2026-07-01（GitHub Actions / CI 环境批量请求）

探测方法：对每校尝试多个常见 RSS 路径（`/feed/`、`/rss`、`/rss.xml` 等），返回 HTTP 200 且含有效条目的视为可用。

**说明：** 许多名校官网 RSS 对自动化请求返回 403/404，或 feed 格式异常；此类院校在 `catalog.json` 中保留 **Google News** 作为保底，并标注 `feed_type: google_news`。已验证的官方 RSS 标注 `feed_type: official_rss`，抓取失败时自动回退到 Google News。

---

## 美国 Top 20 — 已验证官方 RSS（9/20）

| 院校 | 官方 RSS |
|------|----------|
| Princeton University | https://www.princeton.edu/news/feed/all |
| MIT | https://news.mit.edu/rss/topic/admissions |
| Harvard University | https://news.harvard.edu/gazette/feed/ |
| Caltech | https://www.caltech.edu/about/news/rss |
| Johns Hopkins University | https://hub.jhu.edu/feed/ |
| Dartmouth College | https://home.dartmouth.edu/rss.xml |
| UCLA | https://newsroom.ucla.edu/rss.xml |
| UC Berkeley | https://news.berkeley.edu/feed/ |
| Vanderbilt University | https://news.vanderbilt.edu/feed/ |

## 美国 Top 20 — 无可用官方 RSS，使用 Google News（11/20）

| 院校 | 域名 |
|------|------|
| Stanford University | stanford.edu |
| Yale University | yale.edu |
| Duke University | duke.edu |
| Northwestern University | northwestern.edu |
| University of Pennsylvania | upenn.edu |
| Cornell University | cornell.edu |
| University of Chicago | uchicago.edu |
| Brown University | brown.edu |
| Columbia University | columbia.edu |
| Rice University | rice.edu |
| University of Notre Dame | nd.edu |

---

## 英国 QS 世界 Top 200 院校 — 已验证官方 RSS（5/48）

| 院校 | 官方 RSS |
|------|----------|
| University of Cambridge | https://www.cam.ac.uk/news/feed |
| University of Manchester | https://www.manchester.ac.uk/discover/news/feed/ |
| University of St Andrews | https://news.st-andrews.ac.uk/feed/ |
| University of Liverpool | https://news.liverpool.ac.uk/feed/ |
| University of Exeter | https://news.exeter.ac.uk/feed/ |

## 英国 QS 世界 Top 200 — 无可用官方 RSS，使用 Google News（43/48）

含：Oxford、Imperial、UCL、Edinburgh、KCL、LSE、Bristol、Warwick、Glasgow、Birmingham、Southampton、Leeds、Sheffield、Durham、Nottingham、QMUL、Bath、York、Newcastle、Cardiff、Queen's Belfast、Loughborough、Reading、Sussex、Surrey、Leicester、Aberdeen、Lancaster、Heriot-Watt、Strathclyde、Kent、Royal Holloway、UEA、Dundee、Essex、Stirling、Swansea、City St George's、Brunel、Aston、SOAS、Goldsmiths、Birkbeck。

完整域名列表见 `data/rss_discovery.json` 中的 `fallback` 数组。

---

## 如何重新探测

```bash
python3 scripts/discover_rss.py    # 批量探测，输出 data/rss_discovery.json
python3 scripts/build_university_catalog.py  # 根据探测结果更新 catalog.json
```

## 手动补充官方 RSS

1. **管理后台**：添加自定义来源 → 填写「官方 RSS 地址」
2. **编辑 catalog**：在 `data/catalog.json` 中设置 `feed_type`、`url`（官方 RSS）、`fallback_url`（Google News）
