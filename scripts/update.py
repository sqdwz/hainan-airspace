from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

import feedparser
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
HISTORY_DIR = DATA_DIR / "history"
STORE_PATH = DATA_DIR / "notices.json"
LATEST_PATH = DATA_DIR / "latest.json"
TZ = ZoneInfo("Asia/Shanghai")
NOW = datetime.now(TZ)
TODAY = NOW.date()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    )
}

QUERY_GROUPS = [
    ("中国民航局（CAAC）", [
        "site:caac.gov.cn 海南 禁飞 无人机 空域管制",
        "site:caac.gov.cn 海南 临时空域 飞行限制",
    ]),
    ("海南省人民政府", [
        "site:hainan.gov.cn 海南 禁飞 无人机 空域管制",
        "site:hainan.gov.cn 低慢小 航空器 海南",
    ]),
    ("文昌市人民政府", [
        "site:wenchang.hainan.gov.cn 禁飞 无人机 空飘物",
        "site:wenchang.hainan.gov.cn 空域 管制 飞行活动",
    ]),
    ("海口市人民政府", [
        "site:haikou.gov.cn 无人机 禁飞 低慢小",
        "site:haikou.gov.cn 空域 管制 航空器",
    ]),
    ("三亚市人民政府", [
        "site:sanya.gov.cn 无人机 禁飞 低慢小",
        "site:sanya.gov.cn 空域 管制 航空器",
    ]),
    ("琼海市人民政府", [
        "site:qionghai.hainan.gov.cn 无人机 禁飞 空域",
        "site:qionghai.hainan.gov.cn 低慢小 航空器",
    ]),
    ("民航海南安全监督管理局", [
        "site:caac.gov.cn 海南安全监督管理局 无人机 空域",
        "民航海南安全监督管理局 禁飞 空域管制",
    ]),
    ("海口美兰 / 三亚凤凰 / 琼海博鳌机场公开信息", [
        "海南 美兰机场 无人机 禁飞 通告",
        "海南 凤凰机场 无人机 禁飞 通告",
        "海南 博鳌机场 无人机 禁飞 通告",
    ]),
    ("新闻媒体补充", [
        "海南 临时禁飞 公告",
        "海南 空域管制 通知",
        "海南 无人机 禁飞",
        "海南 航空 管制",
        "Hainan flight restriction NOTAM",
        "文昌 禁飞 无人机",
    ]),
]

OFFICIAL_DOMAINS = (
    "caac.gov.cn",
    "hainan.gov.cn",
    "haikou.gov.cn",
    "sanya.gov.cn",
)

MEDIA_DOMAINS = (
    "hinews.cn",
    "hnntv.cn",
    "people.com.cn",
    "xinhuanet.com",
    "cctv.com",
    "news.cn",
    "qq.com",
    "sina.cn",
    "sina.com.cn",
    "163.com",
)

GEO_WORDS = (
    "海南", "海口", "三亚", "文昌", "琼海", "儋州", "万宁", "陵水", "澄迈",
    "临高", "定安", "屯昌", "琼中", "保亭", "乐东", "东方", "昌江", "白沙",
    "五指山", "美兰", "凤凰", "博鳌", "龙楼", "东郊", "文教",
)

STRONG_CONTROL_WORDS = (
    "禁飞", "空域管制", "临时空域", "临时空中限制区", "低慢小", "小型航空器",
    "无人驾驶航空器", "无人机管制", "禁止飞行", "飞行活动的通告", "空飘物",
    "flight restriction", "NOTAM",
)

AIRCRAFT_WORDS = (
    "无人机", "无人驾驶航空器", "航空模型", "轻型航空器", "超轻型飞机", "滑翔伞",
    "动力伞", "热气球", "飞艇", "空飘物", "风筝", "孔明灯", "航空器",
)

PUBLISHER_BY_DOMAIN = {
    "wenchang.hainan.gov.cn": "文昌市人民政府",
    "haikou.gov.cn": "海口市人民政府",
    "sanya.gov.cn": "三亚市人民政府",
    "qionghai.hainan.gov.cn": "琼海市人民政府",
    "hainan.gov.cn": "海南省人民政府",
    "caac.gov.cn": "中国民航局 / 民航相关单位",
}

DATE_META_KEYS = {
    "article:published_time", "pubdate", "publishdate", "publish-date", "datepublished",
    "date", "sailthru.date", "weibo:article:create_at", "og:release_date",
}

RANGE_RE = re.compile(
    r"(?:(?P<y1>20\d{2})年)?(?P<m1>\d{1,2})月(?P<d1>\d{1,2})日"
    r"(?:\s*(?P<h1>\d{1,2})(?:[:：时](?P<min1>\d{1,2})?)?(?:分)?)?"
    r"\s*(?:至|到|—|－|~|～|－|—)\s*"
    r"(?:(?P<y2>20\d{2})年)?(?P<m2>\d{1,2})月(?P<d2>\d{1,2})日"
    r"(?:\s*(?P<h2>\d{1,2})(?:[:：时](?P<min2>\d{1,2})?)?(?:分)?)?"
)

DATE_RE = re.compile(r"(20\d{2})[年./-](\d{1,2})[月./-](\d{1,2})日?")


def clean_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_url(url: str) -> str:
    try:
        parts = urlsplit(url)
        query = [
            (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if not k.lower().startswith("utm_") and k.lower() not in {"spm", "from", "source"}
        ]
        return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path, urlencode(query), ""))
    except Exception:
        return url


def domain_of(url: str) -> str:
    try:
        return urlsplit(url).netloc.lower().split(":")[0]
    except Exception:
        return ""


def is_allowed_domain(url: str) -> bool:
    d = domain_of(url)
    return any(d == x or d.endswith("." + x) for x in OFFICIAL_DOMAINS + MEDIA_DOMAINS)


def infer_publisher(url: str, soup: BeautifulSoup | None = None) -> str:
    d = domain_of(url)
    for key, publisher in PUBLISHER_BY_DOMAIN.items():
        if d == key or d.endswith("." + key):
            return publisher
    if soup:
        meta = soup.find("meta", attrs={"property": "og:site_name"}) or soup.find("meta", attrs={"name": "application-name"})
        if meta and meta.get("content"):
            return clean_space(meta.get("content"))[:60]
    return d or "未识别"


def parse_publish_date(soup: BeautifulSoup, text: str) -> str | None:
    for meta in soup.find_all("meta"):
        key = (meta.get("property") or meta.get("name") or meta.get("itemprop") or "").strip().lower()
        if key in DATE_META_KEYS:
            content = clean_space(meta.get("content") or "")
            m = DATE_RE.search(content)
            if m:
                try:
                    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
                except ValueError:
                    pass
            try:
                dt = datetime.fromisoformat(content.replace("Z", "+00:00"))
                return dt.date().isoformat()
            except Exception:
                pass

    head_text = text[:4000]
    for m in DATE_RE.finditer(head_text):
        try:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            continue
        if TODAY - timedelta(days=365) <= d <= TODAY + timedelta(days=30):
            return d.isoformat()
    return None


def parse_control_range(text: str) -> tuple[str | None, str | None, str | None]:
    best = None
    best_score = -1
    for m in RANGE_RE.finditer(text):
        ctx = text[max(0, m.start() - 180): min(len(text), m.end() + 180)]
        score = sum(2 for k in ("禁飞", "管制", "禁止", "限制区", "飞行") if k in ctx)
        score += sum(1 for k in AIRCRAFT_WORDS if k in ctx)
        if score > best_score:
            best, best_score = m, score
    if not best or best_score <= 0:
        return None, None, None

    g = best.groupdict()
    y1 = int(g["y1"] or TODAY.year)
    y2 = int(g["y2"] or y1)
    h1 = int(g["h1"] or 0)
    mi1 = int(g["min1"] or 0)
    h2 = int(g["h2"] or 23)
    mi2 = int(g["min2"] or (59 if not g["h2"] else 0))
    try:
        d1 = datetime(y1, int(g["m1"]), int(g["d1"]), h1, mi1, tzinfo=TZ)
        d2 = datetime(y2, int(g["m2"]), int(g["d2"]), h2, mi2, tzinfo=TZ)
        if d2 < d1 and not g["y2"]:
            d2 = d2.replace(year=d2.year + 1)
    except ValueError:
        return None, None, None

    label = f"{d1:%Y-%m-%d %H:%M} — {d2:%Y-%m-%d %H:%M}"
    return d1.isoformat(), d2.isoformat(), label


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[。！？；;])|[\r\n]+", text)
    return [clean_space(c) for c in chunks if clean_space(c)]


def extract_area(text: str) -> str:
    best = ""
    for s in split_sentences(text):
        if len(s) < 8 or len(s) > 320:
            continue
        has_geo = any(k in s for k in GEO_WORDS)
        has_area_signal = any(k in s for k in ("禁飞区域", "禁飞区", "管制区域", "限制区", "全域", "行政区域空域", "区域内"))
        if has_geo and has_area_signal:
            best = s
            if len(s) <= 180:
                break
    return best[:240]


def extract_summary(text: str) -> str:
    sentences = split_sentences(text)
    for s in sentences:
        if 15 <= len(s) <= 300 and any(k in s for k in ("禁止", "禁飞", "管制")) and any(k in s for k in AIRCRAFT_WORDS):
            return s[:220]
    for s in sentences:
        if 15 <= len(s) <= 300 and any(k in s for k in STRONG_CONTROL_WORDS):
            return s[:220]
    return "公开页面涉及海南禁飞、无人机或空域管制信息，请打开原文核验具体要求。"


def relevant(title: str, snippet: str, text: str) -> bool:
    blob = f"{title} {snippet} {text[:8000]}".lower()
    has_geo = any(k.lower() in blob for k in GEO_WORDS) or "hainan" in blob
    has_control = any(k.lower() in blob for k in STRONG_CONTROL_WORDS)
    return has_geo and has_control


def fetch_page(url: str, snippet: str = "") -> dict | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        r.raise_for_status()
        ctype = r.headers.get("content-type", "").lower()
        if "html" not in ctype and "text" not in ctype:
            return None
        r.encoding = r.apparent_encoding or r.encoding
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    title = clean_space(
        (soup.find("meta", attrs={"property": "og:title"}) or {}).get("content", "")
        if soup.find("meta", attrs={"property": "og:title"}) else ""
    )
    if not title and soup.title:
        title = clean_space(soup.title.get_text(" ", strip=True))
    text = clean_space(soup.get_text(" ", strip=True))
    final_url = normalize_url(r.url)
    if not relevant(title, snippet, text):
        return None
    if not is_allowed_domain(final_url):
        return None

    publish_date = parse_publish_date(soup, text)
    start_time, end_time, time_text = parse_control_range(text)
    publisher = infer_publisher(final_url, soup)
    area = extract_area(text)
    summary = extract_summary(text)
    source_type = "official" if any(domain_of(final_url).endswith(x) for x in OFFICIAL_DOMAINS) else "media"

    return {
        "title": title[:180] or clean_space(snippet)[:180] or "未识别标题",
        "publisher": publisher,
        "publish_date": publish_date,
        "area": area,
        "start_time": start_time,
        "end_time": end_time,
        "time_text": time_text,
        "summary": summary,
        "url": final_url,
        "source_type": source_type,
    }


def bing_rss(query: str) -> list[dict]:
    cutoff = (TODAY - timedelta(days=14)).isoformat()
    params = {
        "q": f"{query} after:{cutoff}",
        "format": "rss",
        "setlang": "zh-Hans",
        "cc": "CN",
    }
    r = requests.get("https://www.bing.com/search", params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    feed = feedparser.parse(r.content)
    results = []
    for e in feed.entries[:12]:
        link = normalize_url(getattr(e, "link", ""))
        if not link:
            continue
        results.append({
            "title": clean_space(getattr(e, "title", "")),
            "link": link,
            "snippet": clean_space(getattr(e, "summary", "")),
        })
    return results


def normalized_title(title: str) -> str:
    t = re.sub(r"[\s\W_]+", "", title or "", flags=re.UNICODE).lower()
    for suffix in ("海南省人民政府网", "海口市人民政府", "三亚市人民政府", "文昌市人民政府"):
        t = t.replace(re.sub(r"[\s\W_]+", "", suffix), "")
    return t[:160]


def candidate_id(item: dict) -> str:
    raw = "|".join([
        item.get("publish_date") or "",
        normalized_title(item.get("title") or ""),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def parse_iso(v: str | None) -> datetime | None:
    if not v:
        return None
    try:
        dt = datetime.fromisoformat(v)
        return dt if dt.tzinfo else dt.replace(tzinfo=TZ)
    except Exception:
        return None


def calc_status(item: dict) -> str:
    start = parse_iso(item.get("start_time"))
    end = parse_iso(item.get("end_time"))
    if start and end:
        if NOW < start:
            return "upcoming"
        if NOW <= end:
            return "active"
        return "ended"
    if item.get("publish_date") == TODAY.isoformat():
        return "new"
    return "unknown"


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalized_title(a), normalized_title(b)).ratio()


def prefer_candidate(old: dict, new: dict) -> dict:
    # Prefer official source and keep richer fields. first_seen is immutable.
    if old.get("source_type") != "official" and new.get("source_type") == "official":
        base, other = dict(new), old
    else:
        base, other = dict(old), new
    for k in ("publisher", "publish_date", "area", "start_time", "end_time", "time_text", "summary", "url", "source_type"):
        if not base.get(k) and other.get(k):
            base[k] = other[k]
    base["first_seen"] = old.get("first_seen") or new.get("first_seen") or TODAY.isoformat()
    base["id"] = old.get("id") or new.get("id")
    return base


def load_store() -> list[dict]:
    if not STORE_PATH.exists():
        return []
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect_candidates() -> tuple[list[dict], list[dict]]:
    seen_urls: set[str] = set()
    candidates: list[dict] = []
    source_status: list[dict] = []

    for source_name, queries in QUERY_GROUPS:
        group_ok = False
        for q in queries:
            try:
                results = bing_rss(q)
                group_ok = True
            except Exception as exc:
                print(f"[WARN] search failed: {q}: {exc}", file=sys.stderr)
                continue

            for result in results:
                url = result["link"]
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                if not is_allowed_domain(url):
                    continue
                item = fetch_page(url, result.get("snippet", ""))
                if not item:
                    continue
                item["id"] = candidate_id(item)
                item["first_seen"] = TODAY.isoformat()
                candidates.append(item)
                time.sleep(0.15)
        source_status.append({"name": source_name, "ok": group_ok})

    return candidates, source_status


def merge_store(existing: list[dict], candidates: list[dict]) -> list[dict]:
    merged = [dict(x) for x in existing]
    for cand in candidates:
        match_idx = None
        for i, old in enumerate(merged):
            same_date = not cand.get("publish_date") or not old.get("publish_date") or cand.get("publish_date") == old.get("publish_date")
            if same_date and title_similarity(cand.get("title", ""), old.get("title", "")) >= 0.84:
                match_idx = i
                break
            if normalize_url(cand.get("url", "")) == normalize_url(old.get("url", "")) and cand.get("url"):
                match_idx = i
                break
        if match_idx is None:
            merged.append(cand)
        else:
            merged[match_idx] = prefer_candidate(merged[match_idx], cand)

    for item in merged:
        item["status"] = calc_status(item)
        item["is_new_today"] = item.get("publish_date") == TODAY.isoformat()
    return merged


def visible_notices(items: list[dict]) -> list[dict]:
    result = []
    for item in items:
        status = item.get("status")
        if status in {"active", "upcoming", "new"}:
            result.append(item)
            continue
        pub = item.get("publish_date")
        end = parse_iso(item.get("end_time"))
        first_seen = item.get("first_seen")
        keep = False
        try:
            if pub and TODAY - date.fromisoformat(pub) <= timedelta(days=35):
                keep = True
        except Exception:
            pass
        if end and NOW - end <= timedelta(days=35):
            keep = True
        try:
            if status == "unknown" and first_seen and TODAY - date.fromisoformat(first_seen) <= timedelta(days=7):
                keep = True
        except Exception:
            pass
        if keep:
            result.append(item)

    priority = {"active": 0, "upcoming": 1, "new": 2, "unknown": 3, "ended": 4}
    result.sort(key=lambda x: (
        priority.get(x.get("status"), 9),
        x.get("publish_date") or "0000-00-00",
        x.get("title") or "",
    ), reverse=False)
    # Within same status, newest publication first.
    grouped = []
    for p in range(5):
        block = [x for x in result if priority.get(x.get("status"), 9) == p]
        block.sort(key=lambda x: x.get("publish_date") or "0000-00-00", reverse=True)
        grouped.extend(block)
    return grouped


def main() -> None:
    existing = load_store()
    candidates, sources = collect_candidates()
    merged = merge_store(existing, candidates)
    visible = visible_notices(merged)

    summary = {
        "new": sum(1 for x in visible if x.get("is_new_today")),
        "active": sum(1 for x in visible if x.get("status") == "active"),
        "upcoming": sum(1 for x in visible if x.get("status") == "upcoming"),
        "ended": sum(1 for x in visible if x.get("status") == "ended"),
    }
    message = (
        f"今日发现{summary['new']}条海南省新的禁飞/空域管制公告"
        if summary["new"]
        else "今日未发现海南省新的禁飞/空域管制公告"
    )
    report = {
        "generated_at": NOW.strftime("%Y-%m-%d %H:%M"),
        "date": TODAY.isoformat(),
        "summary": summary,
        "message": message,
        "notices": visible,
        "sources": sources,
    }

    save_json(STORE_PATH, merged)
    save_json(LATEST_PATH, report)
    save_json(HISTORY_DIR / f"{TODAY.isoformat()}.json", report)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
