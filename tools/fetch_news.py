#!/usr/bin/env python3
"""Collect public news feeds and write data/index.json plus one file per day."""

from __future__ import annotations

import hashlib
import html as htmlmod
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from zoneinfo import ZoneInfo

import feedparser
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sources import SOURCES, STYPES, TOPIC_FEEDS  # noqa: E402
from taxonomy import CASE_SENSITIVE, CAT_RULES, CATEGORIES, GEO, TOPICS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DAY_DIR = DATA / "day"
SHANGHAI = ZoneInfo("Asia/Shanghai")
UTC = timezone.utc
WINDOW_DAYS = int(os.environ.get("WINDOW_DAYS", "7"))
GN_WHEN = os.environ.get("GN_WHEN", "1d")
EXCERPT_LEN = 160
X_TITLE_LEN = 90
TIME_BUDGET = float(os.environ.get("TIME_BUDGET", "1500"))
MAX_DECODE = int(os.environ.get("MAX_DECODE", "500"))
MAX_TRANSLATE = int(os.environ.get("MAX_TRANSLATE", "1600"))
T0 = time.time()

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
ACCEPT = "application/rss+xml, application/atom+xml, application/xml, text/xml, text/html, */*"


def log(*a):
    print(*a, flush=True)


def elapsed() -> float:
    return time.time() - T0


# ---------------------------------------------------------------- http

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": UA,
    "Accept": ACCEPT,
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
})
GN_LOCK = Lock()
_gn_last = [0.0]


def http_get(url: str, timeout: int = 22, retries: int = 3, pause: float = 1.5):
    last = None
    for i in range(retries):
        if "news.google.com" in url:
            with GN_LOCK:
                wait = 0.9 - (time.time() - _gn_last[0])
                if wait > 0:
                    time.sleep(wait)
                _gn_last[0] = time.time()
        try:
            r = SESSION.get(url, timeout=timeout, allow_redirects=True)
            if r.status_code == 200 and r.content:
                return r
            last = r
            if r.status_code in (403, 429, 500, 502, 503, 504):
                time.sleep(pause * (i + 1) * (3 if r.status_code == 429 else 1))
                continue
            return r
        except requests.RequestException as e:
            last = e
            time.sleep(pause * (i + 1))
    return last if isinstance(last, requests.Response) else None


# ---------------------------------------------------------------- text helpers

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
TRACKING = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "utm_id",
    "fbclid", "gclid", "ref", "rss", "from", "fromrss", "cmpid", "ns_mchannel", "ns_source",
    "ns_campaign", "ns_linkname", "ocid", "at_medium", "at_campaign", "dicbo", "smid", "partner",
}
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def strip_html(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</p>", "\n", s)
    s = TAG_RE.sub(" ", s)
    s = htmlmod.unescape(htmlmod.unescape(s))
    return WS_RE.sub(" ", s).strip()


def fix_mojibake(s: str) -> str:
    if s and any(ch in s for ch in ("â€", "Ã", "ð", "Â")):
        try:
            return s.encode("latin-1").decode("utf-8")
        except Exception:
            return s
    return s


EXCERPT_JUNK = re.compile(
    r"^(点击查看原文>?|阅读全文|Read more|Continue reading|查看原文|Comments|The post .+ appeared first on .+)\.?$", re.I
)


def excerpt_of(s: str, title: str = "", n: int = EXCERPT_LEN) -> str:
    s = fix_mojibake(strip_html(s))
    s = re.sub(r"\s*(Continue reading\.*|Read more\.*|阅读全文|\[…\]|\[\.\.\.\])\s*$", "", s, flags=re.I)
    s = re.sub(r"The post .+? appeared first on .+?\.\s*$", "", s)
    if not s or EXCERPT_JUNK.match(s):
        return ""
    if title:
        t = WS_RE.sub("", title)
        if WS_RE.sub("", s).startswith(t) and len(s) < len(title) + 24:
            return ""
        if s.startswith(title):
            s = s[len(title):].lstrip(" ：:-—|")
    if len(s) <= n:
        return s
    cut = s[:n]
    for sep in ("。", "！", "？", ". ", "; ", "；", "，", ", ", " "):
        i = cut.rfind(sep)
        if i >= n * 0.55:
            return cut[: i + (1 if sep in "。！？" else 0)].strip() + ("" if sep in "。！？" else "…")
    return cut.rstrip() + "…"


TITLE_PREFIX = re.compile(r"^(?:\[流言板\]|\[[^\]]{1,6}\]|【[^】]{1,8}】(?=\S{6}))")


SITE_SUFFIX = re.compile(
    r"\s*[-_|｜—]+\s*(中国日报网|中国新闻网|中新网|新华网|人民网|央视网|光明网|环球网|澎湃新闻|凤凰网|新浪网|"
    r"网易|搜狐|腾讯网|中国经济网|央广网|中青在线|中国军网|科技日报|界面新闻|新京报|第一财经|财新网|"
    r"[^\s-]{1,8}频道|[^\s-]{1,6}网)\s*$"
)


COLUMN_PREFIX = re.compile(r"^[^丨｜|：:]{1,9}[丨｜|]\s*")


def clean_title(title: str) -> str:
    title = fix_mojibake(strip_html(title))
    title = TITLE_PREFIX.sub("", title).strip()
    if CJK_RE.search(title):
        for _ in range(2):
            title = SITE_SUFFIX.sub("", title).strip()
        m = COLUMN_PREFIX.match(title)
        if m and len(title) - m.end() >= 10:
            title = title[m.end():].strip()
    return WS_RE.sub(" ", title).strip(" -_—|")


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    try:
        p = urlparse(url)
    except Exception:
        return url
    host = (p.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = p.path or ""
    if path.endswith("/") and len(path) > 1:
        path = path[:-1]
    q = [(k, v) for k, v in parse_qsl(p.query) if k.lower() not in TRACKING and not k.lower().startswith("utm_")]
    return urlunparse(((p.scheme or "https").lower(), host, path, "", urlencode(q, doseq=True), ""))


def clean_url(url: str) -> str:
    url = (url or "").strip()
    if not url.startswith("http"):
        return url
    try:
        p = urlparse(url)
    except Exception:
        return url
    q = [(k, v) for k, v in parse_qsl(p.query) if k.lower() not in TRACKING and not k.lower().startswith("utm_")]
    return urlunparse((p.scheme, p.netloc, p.path, p.params, urlencode(q, doseq=True), ""))


def make_id(url: str) -> str:
    return hashlib.sha1(normalize_url(url).encode("utf-8")).hexdigest()[:14]


def title_key(src: str, title: str) -> str:
    t = re.sub(r"[\W_]+", "", (title or "").lower())
    return "%s|%s" % (src, t[:60])


def to_sh(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(SHANGHAI)


def parse_date(v):
    if not v:
        return None
    if isinstance(v, time.struct_time):
        try:
            return to_sh(datetime(*v[:6], tzinfo=UTC))
        except Exception:
            return None
    s = str(v).strip()
    try:
        return to_sh(datetime.fromisoformat(s.replace("Z", "+00:00")))
    except Exception:
        pass
    try:
        return to_sh(parsedate_to_datetime(s))
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%b %d, %Y %I:%M%p", "%Y-%m-%d %H:%M:%S %z"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=SHANGHAI if "-" in s[:5] else UTC)
            return to_sh(dt)
        except Exception:
            continue
    return None


def iso(dt: datetime) -> str:
    return to_sh(dt).isoformat(timespec="seconds")


def is_zh(text: str) -> bool:
    cjk = len(CJK_RE.findall(text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return cjk >= 4 or (cjk >= 1 and cjk * 3 >= max(1, latin))


try:
    import opencc
    _T2S = opencc.OpenCC("t2s")
except Exception:  # pragma: no cover
    _T2S = None


def to_simplified(s: str) -> str:
    if not s or _T2S is None:
        return s
    out = _T2S.convert(s)
    diff = sum(1 for a, b in zip(s, out) if a != b)
    return out if diff >= 2 else s


# ---------------------------------------------------------------- feed parsing

def entry_link(e) -> str:
    link = (e.get("link") or "").strip()
    if link:
        return link
    for l in e.get("links") or []:
        if l.get("href") and l.get("rel") in (None, "", "alternate"):
            return l["href"]
    ident = e.get("id") or ""
    return ident if isinstance(ident, str) and ident.startswith("http") else ""


def entry_date(e):
    for k in ("published_parsed", "updated_parsed"):
        dt = parse_date(e.get(k))
        if dt:
            return dt
    for k in ("published", "updated", "dc_date", "date"):
        dt = parse_date(e.get(k))
        if dt:
            return dt
    return None


def entry_summary(e) -> str:
    for k in ("summary", "description"):
        if e.get(k):
            return e[k]
    c = e.get("content")
    if c and isinstance(c, list) and c[0].get("value"):
        return c[0]["value"]
    return ""


IMG_BLOCKED_HOSTS = ("japantimes.co.jp",)  # images refuse to load on other sites
IMG_RE = re.compile(r"""<img[^>]+src=["']([^"']+)["']""", re.I)


def entry_image(e) -> str:
    cands = []
    for k in ("media_content", "media_thumbnail"):
        for m in e.get(k) or []:
            u = m.get("url") or ""
            if u:
                try:
                    w = int(m.get("width") or 0)
                except ValueError:
                    w = 0
                cands.append((w, u))
    if cands:
        cands.sort(key=lambda x: -x[0])
        url = cands[0][1]
    else:
        url = ""
        for enc in e.get("enclosures") or []:
            if (enc.get("type") or "").startswith("image") and enc.get("href"):
                url = enc["href"]
                break
        if not url:
            for k in ("summary", "description"):
                m = IMG_RE.search(e.get(k) or "")
                if m:
                    url = m.group(1)
                    break
        if not url:
            c = e.get("content")
            if c and isinstance(c, list):
                m = IMG_RE.search(c[0].get("value") or "")
                if m:
                    url = m.group(1)
    url = htmlmod.unescape(url or "").strip()
    if url.startswith("//"):
        url = "https:" + url
    if not url.startswith("http"):
        return ""
    if re.search(r"(feedburner|pixel|tracking|1x1|spacer|blank\.gif|emoji|gravatar|avatar)", url, re.I):
        return ""
    if any(h in url for h in IMG_BLOCKED_HOSTS):
        return ""
    url = re.sub(r"(ichef\.bbci\.co\.uk/(?:ace/(?:standard|ws)|news))/\d+/", r"\1/480/", url)
    return url


GENERIC_JUNK = re.compile(
    r"^(首页|新闻中心|滚动新闻|专题|视频|图片|直播|节目单|体育节目单)$|_[^_]{1,12}_[^_]{1,12}$|"
    r"数据库|节目单|频道$|首页$|数字报|电子版|招聘|日常公告|公告系列|官方网站|门户网站"
)


def is_junk_title(title: str, src: dict) -> bool:
    if len(title) < (6 if is_zh(title) else 14):
        return True
    if GENERIC_JUNK.search(title):
        return True
    j = src.get("junk")
    if j and re.search(j, title):
        return True
    return False


def build_item(src: dict, title: str, url: str, dt: datetime, excerpt_raw: str, cats, img: str = "", via: str = ""):
    title = clean_title(title)
    if not title or not url or not dt:
        return None
    if url.startswith("/"):
        url = urljoin(src["home"], url)
    if "news.google.com" not in url:
        url = clean_url(url)
    if is_junk_title(title, src):
        return None
    excerpt = excerpt_of(excerpt_raw or "", title)
    zh = is_zh(title + " " + excerpt)
    if zh:
        title = to_simplified(title)
        excerpt = to_simplified(excerpt)
    now = datetime.now(SHANGHAI)
    if dt - now > timedelta(minutes=40):
        if src["region"] == "cn":
            dt = dt - timedelta(hours=8)
        if dt - now > timedelta(minutes=40):
            dt = now
    it = {
        "id": make_id(url),
        "title": title,
        "url": url,
        "src": src["id"],
        "time": iso(dt),
        "lang": "zh" if zh else "en",
    }
    if excerpt:
        it["excerpt"] = excerpt
    if img:
        it["img"] = img
    if via:
        it["via"] = via
    it["_feedcats"] = list(cats or [])
    return it


def parse_rss(raw: bytes, src: dict, cats) -> list:
    parsed = feedparser.parse(raw)
    out = []
    for e in parsed.entries:
        it = build_item(src, e.get("title") or "", entry_link(e), entry_date(e),
                        entry_summary(e), cats, entry_image(e))
        if it:
            out.append(it)
    return out


def split_gn_title(e) -> tuple[str, str]:
    title = strip_html(e.get("title") or "")
    s = e.get("source") or {}
    name = s.get("title", "") if isinstance(s, dict) else ""
    if name and title.endswith(name):
        title = title[: -len(name)].rstrip(" -–—|")
    elif " - " in title:
        left, right = title.rsplit(" - ", 1)
        if len(right) <= 24:
            title, name = left, name or right
    return title.strip(), name.strip()


def parse_gn(raw: bytes, src: dict, cats) -> list:
    parsed = feedparser.parse(raw)
    out = []
    for e in parsed.entries:
        title, _ = split_gn_title(e)
        it = build_item(src, title, entry_link(e), entry_date(e), "", cats)
        if it:
            out.append(it)
    return out


# ---- X / Twitter via FxTwitter

STATUS_RE = re.compile(r"(?:https?://)?(?:www\.)?(?:twitter|x|fxtwitter)\.com/([^/?#]+)/status/(\d+)", re.I)
MEDIA_ONLY_RE = re.compile(r"^(?:Media|https?://(?:pbs|video)\.twimg\.com\S*)$", re.I)


def tweet_text(e) -> str:
    raw = entry_summary(e) or e.get("title") or ""
    raw = re.sub(r"(?is)<img[^>]*>", " ", raw)
    raw = re.sub(r'(?is)<a[^>]+href="[^"]*(?:pbs|video)\.twimg\.com[^"]*"[^>]*>.*?</a>', " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>", "\n", raw)
    raw = htmlmod.unescape(TAG_RE.sub(" ", raw))
    lines = [WS_RE.sub(" ", l).strip() for l in raw.splitlines()]
    return "\n".join(l for l in lines if l and not MEDIA_ONLY_RE.match(l)).strip()


def tweet_split(text: str) -> tuple[str, str]:
    compact = WS_RE.sub(" ", text).strip()
    compact = re.sub(r"\s*https?://\S+$", "", compact)
    if len(compact) <= X_TITLE_LEN:
        return compact, ""
    m = re.search(r"(.+?[。！？.!?])(\s+|$)", compact)
    if m and 18 <= len(m.group(1)) <= X_TITLE_LEN + 30:
        return m.group(1).strip(), compact[m.end():].strip()
    cut = compact[:X_TITLE_LEN].rsplit(" ", 1)[0].rstrip("，,;:、")
    return cut + "…", compact[len(cut):].lstrip(" ….,;:，、")


def parse_x(src: dict, cats) -> list:
    handle = src["handle"]
    raw = None
    for url in ("https://fxtwitter.com/%s/feed.xml" % handle, "https://fxtwitter.com/%s/feed.atom.xml" % handle):
        r = http_get(url, timeout=28, retries=3)
        if r is not None and r.status_code == 200 and (b"<item" in r.content or b"<entry" in r.content):
            raw = r.content
            break
    if not raw:
        raise RuntimeError("订阅暂不可用")
    out = []
    for e in feedparser.parse(raw).entries:
        m = STATUS_RE.search(entry_link(e))
        if not m or m.group(1).lower() != handle.lower():
            continue
        text = tweet_text(e)
        if not text or re.match(r"^(RT\s+@|@\w+)", text):
            continue
        url = "https://x.com/%s/status/%s" % (m.group(1), m.group(2))
        title, rest = tweet_split(text)
        it = build_item(src, title, url, entry_date(e), rest, cats, entry_image(e), via="x")
        if it:
            out.append(it)
        if len(out) >= 16:
            break
    return out


def fetch_source(src: dict) -> tuple[dict, list]:
    items, errors, ok_feeds = [], [], 0
    for url, cats in src["feeds"]:
        try:
            if src["kind"] == "x":
                got = parse_x(src, cats)
            else:
                real = url.replace("{when}", GN_WHEN)
                r = http_get(real)
                if r is None:
                    raise RuntimeError("连接失败")
                if r.status_code != 200:
                    raise RuntimeError("HTTP %d" % r.status_code)
                got = parse_gn(r.content, src, cats) if src["kind"] == "gn" else parse_rss(r.content, src, cats)
            ok_feeds += 1
            items.extend(got)
        except Exception as e:  # keep going with the other feeds
            errors.append("%s" % e)
    info = {
        "ok": ok_feeds > 0 and bool(items),
        "fetched": len(items),
        "error": "; ".join(sorted(set(errors)))[:160] if errors and not items else "",
    }
    return info, items


# ---- Google News front page (used to mark headline stories)

def fetch_headlines() -> dict:
    name_map = {}
    for s in SOURCES:
        for n in s.get("gn") or []:
            name_map[n.lower()] = s["id"]
    marks = {}
    for url, cat in TOPIC_FEEDS:
        r = http_get(url, retries=2)
        if r is None or r.status_code != 200:
            continue
        for rank, e in enumerate(feedparser.parse(r.content).entries):
            title, pub = split_gn_title(e)
            sid = name_map.get(pub.lower())
            if not sid or not title:
                continue
            key = title_key(sid, to_simplified(clean_title(title)))
            prev = marks.get(key)
            score = max(0.2, 1.0 - rank / 60)
            if not prev or prev < score:
                marks[key] = score
    log("头条标记 %d 条" % len(marks))
    return marks


# ---------------------------------------------------------------- tagging

def _compile(pat: str, flags=0):
    return re.compile(pat, flags)


CAT_ZH = {k: _compile(v[0]) for k, v in CAT_RULES.items()}
CAT_EN = {k: _compile(v[1], re.I) for k, v in CAT_RULES.items()}
GEO_ZH = {g[0]: _compile(g[2]) for g in GEO}
GEO_EN = {g[0]: _compile(g[3], re.I) for g in GEO}
TOP_ZH = {t[0]: _compile(t[2]) for t in TOPICS}
TOP_EN = {t[0]: _compile(t[3], re.I) for t in TOPICS}
CS = {k: re.compile(v) for k, v in CASE_SENSITIVE.items()}
TOPICAL = {"finance", "tech", "sports", "ent", "health", "science", "military", "auto", "edu", "culture"}


def _hits(zh_pat, en_pat, cs_key, zh_text, en_text) -> int:
    n = len(zh_pat.findall(zh_text)) if zh_text else 0
    if en_text:
        n += len(en_pat.findall(en_text))
        cs = CS.get(cs_key)
        if cs:
            n += len(cs.findall(en_text))
    return n


def tag(it: dict, src: dict) -> None:
    if it["lang"] == "zh":
        zh_text = "%s\n%s" % (it["title"], it.get("excerpt", ""))
        en_text = ""
        title_zh, title_en = it["title"], ""
    else:
        zh_text = "%s\n%s" % (it.get("title_zh", ""), it.get("excerpt_zh", ""))
        en_text = "%s\n%s" % (it["title"], it.get("excerpt", ""))
        title_zh, title_en = it.get("title_zh", ""), it["title"]

    def score(zp, ep, cskey):
        s = _hits(zp, ep, cskey, title_zh, title_en) * 2
        s += _hits(zp, ep, cskey, zh_text, en_text)
        return s

    feedcats = [c for c in it.get("feedcats", []) if c]
    cat_scores = {c: score(CAT_ZH[c], CAT_EN[c], "cat:" + c) for c in CAT_RULES}
    cats = list(dict.fromkeys(feedcats))
    ranked = sorted(((s, c) for c, s in cat_scores.items() if s > 0), reverse=True)
    if feedcats:
        for s, c in ranked:
            if c not in cats and s >= 4 and len(cats) < 3:
                cats.append(c)
    else:
        for s, c in ranked[:2]:
            if s >= 2 or (s >= 1 and not cats):
                cats.append(c)

    geo_scores = {g[0]: score(GEO_ZH[g[0]], GEO_EN[g[0]], "geo:" + g[0]) for g in GEO}
    geo = [g for g, s in sorted(geo_scores.items(), key=lambda x: -x[1]) if s >= 2][:3]
    if not geo:
        geo = [g for g, s in geo_scores.items() if s >= 1][:2]
    if src["region"] == "cn" and not geo and it["lang"] == "zh":
        geo = ["cn"]

    general = not feedcats or any(c in ("china", "world", "society") for c in feedcats)
    if general or not (set(cats) & TOPICAL):
        foreign = [g for g in geo if g not in ("cn", "hmt")]
        if "china" not in cats and ("cn" in geo or "hmt" in geo) and (not foreign or geo[0] in ("cn", "hmt")):
            cats.append("china")
        if "world" not in cats and foreign:
            cats.append("world")
    if not cats:
        cats = ["china"] if src["region"] == "cn" else ["world"]
    order = {c: i for i, (c, _) in enumerate(CATEGORIES)}
    head = cats[0]
    rest = sorted(set(cats[1:]) - {head}, key=lambda c: order.get(c, 99))
    it["cats"] = [head] + rest

    tops = []
    for t in TOPICS:
        s = score(TOP_ZH[t[0]], TOP_EN[t[0]], "topic:" + t[0])
        if s >= 2:
            tops.append((s, t[0]))
    tops.sort(reverse=True)
    it["geo"] = geo
    it["topics"] = [t for _, t in tops[:4]]


# ---------------------------------------------------------------- google news link decoding

def decode_links(items: list) -> None:
    try:
        from googlenewsdecoder import gnewsdecoder
    except Exception:
        log("未安装链接解析模块，跳过")
        return
    pending = [it for it in items if "news.google.com" in it["url"] and it.get("_dec", 0) < 3]
    pending.sort(key=lambda x: x["time"], reverse=True)
    pending = pending[:MAX_DECODE]
    if not pending:
        return
    log("解析转载链接 %d 条" % len(pending))
    ok = [0]

    def one(it):
        try:
            res = gnewsdecoder(it["url"], interval=0.4)
        except Exception:
            res = None
        return it, res

    with ThreadPoolExecutor(max_workers=4) as ex:
        for fut in as_completed([ex.submit(one, it) for it in pending]):
            it, res = fut.result()
            if res and res.get("status", res.get("success")) and res.get("decoded_url", "").startswith("http"):
                it["url"] = clean_url(res["decoded_url"])
                it.pop("_dec", None)
                ok[0] += 1
            else:
                it["_dec"] = it.get("_dec", 0) + 1
            if elapsed() > TIME_BUDGET * 0.45:
                break
    log("链接解析完成 %d / %d" % (ok[0], len(pending)))


# ---------------------------------------------------------------- translation

def _parse_mt(data, n):
    if not isinstance(data, list):
        return None
    out = []
    for row in data:
        if isinstance(row, str):
            out.append(row)
        elif isinstance(row, list) and row and isinstance(row[0], str):
            out.append(row[0])
        else:
            return None
    return [s.strip() for s in out[:n]] if len(out) >= n else None


def _mt_google(texts):
    try:
        r = requests.post(
            "https://clients5.google.com/translate_a/t",
            params={"client": "dict-chrome-ex", "sl": "auto", "tl": "zh-CN"},
            data=[("q", t) for t in texts],
            headers={"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"},
            timeout=25,
        )
    except requests.RequestException:
        return None
    if r.status_code != 200 or "json" not in (r.headers.get("content-type") or ""):
        return None
    try:
        return _parse_mt(r.json(), len(texts))
    except ValueError:
        return None


def _mt_gtx(texts):
    out = []
    for t in texts:
        try:
            r = requests.get(
                "https://translate.googleapis.com/translate_a/single",
                params={"client": "gtx", "sl": "auto", "tl": "zh-CN", "dt": "t", "q": t},
                headers={"User-Agent": UA}, timeout=20,
            )
            data = r.json()
            out.append("".join(seg[0] for seg in data[0] if seg and seg[0]).strip())
        except Exception:
            return None
    return out


FIXES = [
    (r"美联社新闻", "美联社"), (r"彭博社新闻", "彭博社"),
    (r"^突发：", "突发："), (r"^BREAKING:\s*", "突发："),
]


def polish_zh(s: str) -> str:
    s = (s or "").strip()
    for a, b in FIXES:
        s = re.sub(a, b, s)
    s = s.replace("“ ", "“").replace(" ”", "”")
    return s


def translate(items: list) -> None:
    pending = [it for it in items if it["lang"] != "zh" and not it.get("title_zh")]
    pending.sort(key=lambda x: x["time"], reverse=True)
    pending = pending[:MAX_TRANSLATE]
    if not pending:
        return
    log("待译外文 %d 条" % len(pending))
    done, fails, i, batch = 0, 0, 0, 5
    while i < len(pending) and fails < 10:
        if elapsed() > TIME_BUDGET * 0.85:
            log("时间预算用尽，余下留到下次")
            break
        chunk = pending[i:i + batch]
        texts, idx = [], []
        for it in chunk:
            texts.append(it["title"])
            if it.get("excerpt"):
                texts.append(it["excerpt"])
            idx.append(bool(it.get("excerpt")))
        got = _mt_google(texts) or _mt_gtx(texts)
        if not got:
            fails += 1
            batch = 1 if fails >= 3 else batch
            time.sleep(1.2 * fails)
            continue
        fails = 0
        k = 0
        for it, has_ex in zip(chunk, idx):
            tz = polish_zh(got[k]); k += 1
            ez = ""
            if has_ex:
                ez = polish_zh(got[k]); k += 1
            if tz and is_zh(tz):
                it["title_zh"] = tz
                if ez:
                    it["excerpt_zh"] = ez
                done += 1
        i += len(chunk)
        if done and done % 100 < batch:
            log("  已译 %d / %d" % (done, len(pending)))
        time.sleep(0.25)
    log("翻译完成 %d 条" % done)


# ---------------------------------------------------------------- engagement (tweets)

def fetch_engagement(items: list) -> None:
    now = datetime.now(SHANGHAI)
    pending = [it for it in items if it.get("via") == "x"
               and now - datetime.fromisoformat(it["time"]) < timedelta(hours=60)]
    if not pending:
        return

    def one(it):
        m = STATUS_RE.search(it["url"])
        if not m:
            return it, None
        r = http_get("https://api.fxtwitter.com/%s/status/%s" % (m.group(1), m.group(2)), timeout=18, retries=2)
        if r is None or r.status_code != 200:
            return it, None
        try:
            t = (r.json() or {}).get("tweet") or {}
        except ValueError:
            return it, None
        st = {k: int(t[k]) for k in ("likes", "retweets", "replies", "quotes", "views")
              if isinstance(t.get(k), int) and not isinstance(t.get(k), bool)}
        return it, st or None

    n = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for fut in as_completed([ex.submit(one, it) for it in pending]):
            it, st = fut.result()
            if st:
                it["eng"] = st
                n += 1
    log("推特互动 %d / %d" % (n, len(pending)))


# ---------------------------------------------------------------- images for big stories

OG_RE = re.compile(r"""<meta[^>]+(?:property|name)=["'](?:og:image|twitter:image)["'][^>]+content=["']([^"']+)["']""", re.I)
OG_RE2 = re.compile(r"""<meta[^>]+content=["']([^"']+)["'][^>]+(?:property|name)=["'](?:og:image|twitter:image)["']""", re.I)


def page_image(url: str) -> str:
    try:
        r = SESSION.get(url, timeout=10, allow_redirects=True, stream=True)
        if r.status_code != 200 or "html" not in (r.headers.get("content-type") or ""):
            return ""
        raw = r.raw.read(200000, decode_content=True)
        r.close()
    except Exception:
        return ""
    text = raw.decode("utf-8", "ignore")
    m = OG_RE.search(text) or OG_RE2.search(text)
    if not m:
        return ""
    img = htmlmod.unescape(m.group(1)).strip()
    if img.startswith("//"):
        img = "https:" + img
    if img.startswith("/"):
        img = urljoin(url, img)
    if not img.startswith("http") or re.search(r"(logo|default|share_icon|favicon|placeholder)", img, re.I):
        return ""
    return img


def enrich_images(items: list, limit: int = 70) -> None:
    now = datetime.now(SHANGHAI)
    groups = defaultdict(list)
    for it in items:
        if now - datetime.fromisoformat(it["time"]) > timedelta(hours=36):
            continue
        groups[it.get("cl") or it["id"]].append(it)
    todo = []
    for key, members in groups.items():
        if any(m.get("img") for m in members):
            continue
        size = max(m.get("cn", 1) for m in members)
        top = max(m.get("top", 0) for m in members)
        if size < 2 and top < 0.5:
            continue
        cands = [m for m in members if "news.google.com" not in m["url"] and not m.get("_og") and m.get("via") != "x"]
        if not cands:
            continue
        cands.sort(key=lambda m: (m["lang"] == "zh", m.get("top", 0)), reverse=True)
        todo.append((size + top, cands[0]))
    todo.sort(key=lambda x: -x[0])
    todo = [it for _, it in todo[:limit]]
    if not todo:
        return
    n = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for it, img in zip(todo, ex.map(lambda it: page_image(it["url"]), todo)):
            it["_og"] = 1
            if img:
                it["img"] = img
                n += 1
    log("补充配图 %d / %d" % (n, len(todo)))


# ---------------------------------------------------------------- clustering

STOP_BIGRAMS = set()
PUNCT_RE = re.compile(r"[^\w\u4e00-\u9fff]+")
EN_STOP = set("""a an the of to in on for and or with by at from as is are was were be been has have had it its this that
these those after over into about amid says said say new more than up out not no will can could would should may
how why what who when where which his her their our your you we they he she them us vs via first last""".split())


def sig_tokens(it: dict) -> list:
    zh = it["title"] if it["lang"] == "zh" else it.get("title_zh", "")
    toks = []
    if zh:
        s = PUNCT_RE.sub(" ", zh)
        for seg in s.split():
            if CJK_RE.search(seg):
                chars = [c for c in seg]
                toks += ["".join(chars[i:i + 2]) for i in range(len(chars) - 1)]
            elif len(seg) >= 2 and seg.lower() not in EN_STOP:
                toks.append("e:" + seg.lower())
    if it["lang"] != "zh":
        words = [w for w in PUNCT_RE.sub(" ", it["title"].lower()).split() if w not in EN_STOP and len(w) > 2]
        toks += ["e:" + w for w in words]
    return toks


MERGE_SIM = 0.34


def merge_groups(groups: list, toks: list, idf: dict, times: list) -> list:
    """Join groups whose combined wording is close, e.g. a Chinese and an English write-up."""
    big = [g for g in groups if len(g) >= 2]
    small = [g for g in groups if len(g) < 2]
    if len(big) < 2:
        return groups
    vecs, norms, spans = [], [], []
    for g in big:
        c = Counter()
        for i in g:
            c.update(toks[i])
        v = {t: idf[t] * (n / len(g)) for t, n in c.items() if n / len(g) >= 0.34}
        vecs.append(v)
        norms.append(math.sqrt(sum(x * x for x in v.values())) or 1.0)
        spans.append((min(times[i] for i in g), max(times[i] for i in g)))
    inv = defaultdict(list)
    for k, v in enumerate(vecs):
        for t in v:
            inv[t].append(k)
    parent = list(range(len(big)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, va in enumerate(vecs):
        cand = Counter()
        for t in va:
            if len(inv[t]) > 40:
                continue
            for b in inv[t]:
                if b > a:
                    cand[b] += 1
        for b, c in cand.items():
            if c < 3:
                continue
            if spans[b][0] - spans[a][1] > 36 * 3600 or spans[a][0] - spans[b][1] > 36 * 3600:
                continue
            vb = vecs[b]
            dot = sum(w * vb[t] for t, w in va.items() if t in vb)
            if dot / (norms[a] * norms[b]) >= MERGE_SIM:
                parent[find(a)] = find(b)
    joined = defaultdict(list)
    for k, g in enumerate(big):
        joined[find(k)].extend(g)
    return list(joined.values()) + small


def cluster(items: list) -> None:
    n = len(items)
    toks = [set(sig_tokens(it)) for it in items]
    df = Counter()
    for t in toks:
        df.update(t)
    idf = {t: math.log((n + 1) / (c + 0.5)) for t, c in df.items()}
    cap_df = max(30, n // 60)
    inv = defaultdict(list)
    for i, t in enumerate(toks):
        for tok in t:
            if df[tok] <= cap_df:
                inv[tok].append(i)
    times = [datetime.fromisoformat(it["time"]).timestamp() for it in items]
    weight = [sum(idf[t] for t in ts) or 1.0 for ts in toks]
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        if len(toks[i]) < 3:
            continue
        cand = Counter()
        for tok in toks[i]:
            lst = inv.get(tok)
            if lst:
                for j in lst:
                    if j > i:
                        cand[j] += 1
        for j, c in cand.items():
            if c < 3 or abs(times[i] - times[j]) > 40 * 3600:
                continue
            if items[i]["src"] == items[j]["src"] and abs(times[i] - times[j]) < 600:
                pass
            shared = toks[i] & toks[j]
            w = sum(idf[t] for t in shared)
            sim = w / min(weight[i], weight[j])
            dice = 2 * w / (weight[i] + weight[j])
            if dice >= 0.5 or (sim >= 0.72 and dice >= 0.38):
                parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)

    def dice(a, b):
        w = sum(idf[t] for t in toks[a] & toks[b])
        return 2 * w / (weight[a] + weight[b])

    final = []
    groups = merge_groups(list(groups.values()), toks, idf, times)
    for members in groups:
        while len(members) > 2:
            sample = members[:80]
            medoid = max(sample, key=lambda a: sum(dice(a, b) for b in sample if b != a))
            keep = [m for m in members if m == medoid or dice(m, medoid) >= 0.3]
            drop = [m for m in members if m not in keep]
            final.append(keep)
            if len(drop) <= 1:
                final.extend([[d] for d in drop])
                members = []
                break
            members = drop
        if members:
            final.append(members)
    for members in final:
        first = min(members, key=lambda k: (times[k], items[k]["id"]))
        cid = items[first]["id"]
        srcs = {items[k]["src"].replace("x-", "") for k in members}
        for k in members:
            if len(members) > 1:
                items[k]["cl"] = cid
                items[k]["cn"] = len(srcs)
            else:
                items[k].pop("cl", None)
                items[k].pop("cn", None)


# ---------------------------------------------------------------- hot words

HOT_STOP = set("""记者 表示 进行 工作 发展 我们 他们 今年 时间 问题 情况 日电 消息 报道 新闻 视频 图片 现场 直播 全国 中国 国家 中方 美国
今天 昨天 明天 目前 已经 相关 推进 加快 持续 举行 召开 发布 公布 宣布 回应 最新 首次 重要 全面 一起 怎么 什么 如何 为何 为什么
多少 可能 需要 开始 继续 部分 正在 这个 一个 没有 不是 还是 就是 以及 关于 通过 方面 期间 之后 之前 年度 人们 系列 活动 会议 全球
世界 国际 地区 城市 公司 企业 市场 行业 产业 项目 平台 数据 用户 服务 政策 提升 支持 推动 建设 合作 能力 质量 高质量 计划 方案 措施
新华社 新华网 央视网 人民网 中新网 澎湃 第一财经 财新 界面 观察 快讯 突发 一图 速览 盘点 解读 独家 专访 来源 作者 编辑 看点 早报 晚报
科技 时代 历史 影响 地面 美国联邦 学院 员工 范围 经济 指数 故障 中断 亚太 欧洲 苹果 美元 中心 主席 总统 总理 部长 官员 领导人 政府 机构 大会 论坛
产品 技术 模式 战略 价值 风险 机会 挑战 未来 今年以来 全年 季度 年度 记录 纪录 现象 背后 真相 原因 结果 方式 意义 体系 机制 时代 生活 健康 文化 社会 安全
亿元 万元 第一 第二 第三 百分 同比 环比 增长 下降 上涨 下跌 突破 达到 超过 其中 此前 近日 日前 当地 时间 小时 分钟 本周 上周 下周""".split())


def hot_words(items: list) -> list:
    try:
        import jieba
        import jieba.posseg as pseg
        jieba.setLogLevel(60)
    except Exception:
        return []
    now = datetime.now(SHANGHAI)
    recent, older = Counter(), Counter()
    seen_cl = set()
    for it in items:
        text = it["title"] if it["lang"] == "zh" else it.get("title_zh", "")
        if not text:
            continue
        key = it.get("cl") or it["id"]
        age = (now - datetime.fromisoformat(it["time"])).total_seconds() / 3600
        words = set()
        for w, flag in pseg.cut(text):
            w = w.strip()
            if len(w) < 2 or w in HOT_STOP or re.fullmatch(r"[\d.%]+", w):
                continue
            if flag[:1] in ("n",) or flag in ("vn", "eng", "nz", "nr", "ns", "nt"):
                if flag == "eng" and len(w) < 3:
                    continue
                words.add(w)
        if age <= 24:
            if (key, "r") in seen_cl:
                continue
            seen_cl.add((key, "r"))
            recent.update(words)
        else:
            older.update(words)
    days_old = max(1, WINDOW_DAYS - 1)
    scored = []
    for w, c in recent.items():
        if c < 4:
            continue
        base = older.get(w, 0) / days_old
        lift = (c + 1) / (base + 2)
        scored.append((c * math.log(1 + lift), w, c))
    scored.sort(reverse=True)
    out = []
    for s, w, c in scored:
        if any(w in o["w"] or o["w"] in w for o in out):
            continue
        out.append({"w": w, "n": c, "s": round(s, 2)})
        if len(out) >= 30:
            break
    return out


# ---------------------------------------------------------------- storage

def load_existing() -> list:
    out = []
    if DAY_DIR.exists():
        for f in sorted(DAY_DIR.glob("*.json")):
            try:
                out.extend(json.loads(f.read_text(encoding="utf-8")).get("items") or [])
            except Exception:
                continue
    return out


KEEP_KEYS = ("title_zh", "excerpt_zh", "img", "eng", "top", "feedcats")


def merge(old: list, fresh: list, cutoff: datetime, by_src: dict) -> list:
    by_id, by_title = {}, {}
    for it in old:
        if datetime.fromisoformat(it["time"]) < cutoff or it["src"] not in by_src:
            continue
        by_id[it["id"]] = it
        by_title[title_key(it["src"], it["title"])] = it["id"]
    added = 0
    for it in fresh:
        fc = it.pop("_feedcats", [])
        if datetime.fromisoformat(it["time"]) < cutoff:
            continue
        key = title_key(it["src"], it["title"])
        oid = it["id"] if it["id"] in by_id else by_title.get(key)
        if oid:
            cur = by_id[oid]
            cur["feedcats"] = list(dict.fromkeys((cur.get("feedcats") or []) + fc))
            if not cur.get("img") and it.get("img"):
                cur["img"] = it["img"]
            if not cur.get("excerpt") and it.get("excerpt"):
                cur["excerpt"] = it["excerpt"]
                cur.pop("excerpt_zh", None)
            if cur.get("title") != it["title"] and it["lang"] == cur.get("lang"):
                cur["title"] = it["title"]
                cur.pop("title_zh", None)
            continue
        it["feedcats"] = fc
        by_id[it["id"]] = it
        by_title[key] = it["id"]
        added += 1
    log("新增 %d 条" % added)
    return list(by_id.values())


def apply_caps(items: list, by_src: dict) -> list:
    buckets = defaultdict(list)
    for it in items:
        buckets[(it["src"], it["time"][:10])].append(it)
    out = []
    for (sid, _), lst in buckets.items():
        cap = by_src[sid].get("cap", 30)
        lst.sort(key=lambda x: (x.get("top", 0), x["time"]), reverse=True)
        out.extend(lst[:cap])
    return out


def compact(it: dict) -> dict:
    keys = ("id", "title", "title_zh", "url", "src", "time", "lang", "excerpt", "excerpt_zh", "img",
            "cats", "geo", "topics", "via", "eng", "top", "cl", "cn", "feedcats", "_dec", "_og")
    out = {}
    for k in keys:
        v = it.get(k)
        if v in (None, "", [], {}):
            continue
        out[k] = v
    return out


def write_json(path: Path, obj) -> bool:
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return True


# ---------------------------------------------------------------- bootstrap

def bootstrap(site: str) -> bool:
    """Pull the published data back when this machine has no local copy."""
    if (DATA / "index.json").exists() or not site:
        return (DATA / "index.json").exists()
    base = site.rstrip("/") + "/data/"
    r = http_get(base + "index.json?t=%d" % time.time(), retries=2)
    if r is None or r.status_code != 200:
        log("线上暂无数据，将从头抓取")
        return False
    try:
        idx = r.json()
    except ValueError:
        return False
    DAY_DIR.mkdir(parents=True, exist_ok=True)
    got = 0
    for d in idx.get("days") or []:
        rd = http_get(base + "day/%s.json?v=%s" % (d["date"], idx.get("generated", "")), retries=2)
        if rd is not None and rd.status_code == 200:
            (DAY_DIR / ("%s.json" % d["date"])).write_bytes(rd.content)
            got += 1
    (DATA / "index.json").write_bytes(r.content)
    log("已从线上取回 %d 天的数据" % got)
    return got > 0


# ---------------------------------------------------------------- main

def main() -> int:
    global GN_WHEN
    have = bootstrap(os.environ.get("SITE_URL", ""))
    if "--bootstrap-only" in sys.argv:
        return 0 if have else 1
    if not have and "GN_WHEN" not in os.environ:
        GN_WHEN = "7d"
    now = datetime.now(SHANGHAI)
    cutoff = (now - timedelta(days=WINDOW_DAYS)).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    by_src = {s["id"]: s for s in SOURCES}
    old = load_existing()
    log("已有 %d 条，抓取 %d 个来源…" % (len(old), len(SOURCES)))

    infos, fresh = {}, []

    def run(src):
        t = time.time()
        info, items = fetch_source(src)
        info["ms"] = int((time.time() - t) * 1000)
        return src, info, items

    for group, workers in (([s for s in SOURCES if s["kind"] != "x"], 12), ([s for s in SOURCES if s["kind"] == "x"], 2)):
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(run, s) for s in group]
            for fut in as_completed(futs):
                src, info, items = fut.result()
                infos[src["id"]] = info
                fresh.extend(items)
                log("  %s %-14s %4d %s" % ("OK " if info["ok"] else "ERR", src["name"][:14], info["fetched"], info["error"]))

    marks = {}
    try:
        marks = fetch_headlines()
    except Exception as e:
        log("头条标记失败：%s" % e)

    items = merge(old, fresh, cutoff, by_src)
    for it in items:
        m = marks.get(title_key(it["src"], it["title"]))
        if m:
            it["top"] = round(max(m, it.get("top", 0)), 2)
    items = apply_caps(items, by_src)

    try:
        decode_links(items)
    except Exception as e:
        log("链接解析出错：%s" % e)
    try:
        translate(items)
    except Exception as e:
        log("翻译出错：%s" % e)
    try:
        fetch_engagement(items)
    except Exception as e:
        log("互动数据出错：%s" % e)

    for it in items:
        tag(it, by_src[it["src"]])
    cluster(items)
    try:
        enrich_images(items)
    except Exception as e:
        log("补充配图出错：%s" % e)
    hot = hot_words(items)

    # write day files
    DAY_DIR.mkdir(parents=True, exist_ok=True)
    days = defaultdict(list)
    for it in items:
        days[it["time"][:10]].append(compact(it))
    keep = set(days)
    for f in DAY_DIR.glob("*.json"):
        if f.stem not in keep:
            f.unlink()
    day_meta = []
    for d in sorted(days, reverse=True):
        lst = sorted(days[d], key=lambda x: x["time"], reverse=True)
        write_json(DAY_DIR / ("%s.json" % d), {"date": d, "items": lst})
        day_meta.append({"date": d, "count": len(lst)})

    counts = defaultdict(Counter)
    src_count = Counter()
    for it in items:
        src_count[it["src"]] += 1
        for k in ("cats", "geo", "topics"):
            counts[k].update(it.get(k) or [])
        counts["lang"][it["lang"]] += 1
        counts["stype"][by_src[it["src"]]["stype"]] += 1
    sources = []
    for s in SOURCES:
        info = infos.get(s["id"], {})
        sources.append({
            "id": s["id"], "name": s["name"], "home": s["home"], "stype": s["stype"],
            "lang": s["lang"], "region": s["region"], "w": s["w"],
            "ok": bool(info.get("ok")), "count": src_count.get(s["id"], 0),
            **({"err": info["error"]} if info.get("error") else {}),
        })
    clusters = len({it["cl"] for it in items if it.get("cl")})
    index = {
        "name": "朝闻",
        "generated": iso(now),
        "window_days": WINDOW_DAYS,
        "count": len(items),
        "clusters": clusters,
        "days": day_meta,
        "sources": sources,
        "taxonomy": {
            "cats": [{"id": c, "name": n, "count": counts["cats"].get(c, 0)} for c, n in CATEGORIES],
            "geo": [{"id": g[0], "name": g[1], "count": counts["geo"].get(g[0], 0)} for g in GEO],
            "topics": [{"id": t[0], "name": t[1], "count": counts["topics"].get(t[0], 0)} for t in TOPICS],
            "stypes": [{"id": k, "name": n, "count": counts["stype"].get(k, 0)} for k, n in STYPES],
            "langs": [{"id": "zh", "name": "中文", "count": counts["lang"].get("zh", 0)},
                      {"id": "en", "name": "外文", "count": counts["lang"].get("en", 0)}],
        },
        "hot": hot,
    }
    write_json(DATA / "index.json", index)
    status = {
        "generated": index["generated"], "count": index["count"], "clusters": clusters,
        "sources_ok": sum(1 for s in sources if s["ok"]), "sources": len(sources),
        "failed": [s["name"] for s in sources if not s["ok"]],
    }
    (ROOT / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ok = sum(1 for s in sources if s["ok"])
    log("完成：来源 %d/%d 可用，共 %d 条，%d 组多源报道，用时 %.0f 秒" % (ok, len(sources), len(items), clusters, elapsed()))
    log("热词：" + "、".join(h["w"] for h in hot[:15]))
    return 0 if items else 1


if __name__ == "__main__":
    sys.exit(main())
