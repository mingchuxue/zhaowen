(function () {
  "use strict";

  // ------------------------------------------------------------ constants
  var NOIMG = /japantimes\.co\.jp/;
  var DATA = "data/";
  var CAT_ORDER = ["china", "world", "finance", "tech", "society", "sports", "ent", "health", "science", "military", "auto", "edu", "culture"];
  var HOME_SECTIONS = ["china", "world", "finance", "tech", "society", "sports", "ent", "health", "science", "military", "auto", "edu"];
  var PAGE = 30;
  var LS = {
    prefs: "zw.prefs", saved: "zw.saved", later: "zw.later", read: "zw.read", hist: "zw.hist",
    blockSrc: "zw.blockSrc", blockKw: "zw.blockKw", follow: "zw.follow", visit: "zw.visit"
  };
  var ICON = {
    star: '<svg viewBox="0 0 24 24"><path d="M12 4.2l2.3 4.8 5.2.7-3.8 3.6.9 5.2L12 16l-4.6 2.5.9-5.2-3.8-3.6 5.2-.7z"/></svg>',
    clock: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 7.5V12l3 2"/></svg>',
    link: '<svg viewBox="0 0 24 24"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/></svg>',
    share: '<svg viewBox="0 0 24 24"><path d="M12 15V4M8 8l4-4 4 4"/><path d="M5 13v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5"/></svg>',
    trans: '<svg viewBox="0 0 24 24"><path d="M4 6h9M8.5 4v2M6 6c.6 3 2.6 5.4 5.5 6.6M11 6c-.7 3.4-3 6-6.5 7.4"/><path d="M13 20l3.5-8 3.5 8M14.2 17.4h4.6"/></svg>',
    hide: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M6.5 6.5l11 11"/></svg>',
    check: '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.2 4.2L19 7"/></svg>'
  };

  // ------------------------------------------------------------ storage
  function load(key, def) {
    try { var v = localStorage.getItem(key); return v ? JSON.parse(v) : def; } catch (e) { return def; }
  }
  function save(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) { toast("浏览器存储空间已满，部分记录未能保存"); }
  }

  var prefs = Object.assign({ theme: "auto", size: "m", density: "cozy", lang: "zh", images: true, dimRead: true, group: true, sort: "hot" }, load(LS.prefs, {}));
  var saved = load(LS.saved, {});
  var later = load(LS.later, {});
  var readMap = load(LS.read, {});
  var hist = load(LS.hist, []);
  var blockSrc = load(LS.blockSrc, []);
  var blockKw = load(LS.blockKw, []);
  var follow = load(LS.follow, []);
  var lastVisit = load(LS.visit, null);

  // ------------------------------------------------------------ state
  var S = {
    index: null, items: [], byId: {}, src: {}, loaded: {}, loading: {},
    clusters: {}, view: "home", tab: "saved", day: null, tlCat: "",
    f: { cats: [], geo: [], topics: [], stypes: [], langs: [], srcs: [] },
    range: "all", date: "", q: "", onlyMulti: false, onlyImg: false, unread: false, followOnly: false,
    sort: prefs.sort || "hot", shown: 0, list: [], focus: -1, now: Date.now()
  };

  // ------------------------------------------------------------ helpers
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function attr(s) { return esc(s); }
  function ts(it) { return it._t || (it._t = Date.parse(it.time)); }
  function pad(n) { return n < 10 ? "0" + n : "" + n; }
  var WEEK = ["日", "一", "二", "三", "四", "五", "六"];
  function shDate(t) {
    var d = new Date(t + 8 * 3600 * 1000);
    return { y: d.getUTCFullYear(), m: d.getUTCMonth() + 1, d: d.getUTCDate(), h: d.getUTCHours(), mi: d.getUTCMinutes(), w: d.getUTCDay() };
  }
  function dayKey(t) { var p = shDate(t); return p.y + "-" + pad(p.m) + "-" + pad(p.d); }
  function rel(t) {
    var s = (S.now - t) / 1000;
    if (s < 60) return "刚刚";
    if (s < 3600) return Math.floor(s / 60) + " 分钟前";
    if (s < 86400 && dayKey(t) === dayKey(S.now)) return Math.floor(s / 3600) + " 小时前";
    var p = shDate(t);
    var yd = dayKey(S.now - 86400000) === dayKey(t);
    return (yd ? "昨天 " : p.m + "月" + p.d + "日 ") + pad(p.h) + ":" + pad(p.mi);
  }
  function absTime(t) { var p = shDate(t); return p.y + "年" + p.m + "月" + p.d + "日 " + pad(p.h) + ":" + pad(p.mi) + "（北京时间）"; }
  function hm(t) { var p = shDate(t); return pad(p.h) + ":" + pad(p.mi); }
  function fmtNum(n) { return n >= 10000 ? (n / 10000).toFixed(n >= 100000 ? 0 : 1) + "万" : String(n); }
  function debounce(fn, ms) { var t; return function () { var a = arguments; clearTimeout(t); t = setTimeout(function () { fn.apply(null, a); }, ms); }; }
  function srcName(id) { var s = S.src[id]; return s ? s.name : id; }
  function hostOf(u) { try { return new URL(u).hostname.replace(/^www\./, ""); } catch (e) { return ""; } }
  function nameOf(list, id) { for (var i = 0; i < list.length; i++) if (list[i].id === id) return list[i].name; return ""; }
  function uniq(a) { return a.filter(function (x, i) { return a.indexOf(x) === i; }); }

  var toastT;
  function toast(msg) {
    var el = $("#toast"); el.textContent = msg; el.hidden = false;
    clearTimeout(toastT); toastT = setTimeout(function () { el.hidden = true; }, 2200);
  }

  function savePrefs() { save(LS.prefs, prefs); }
  function applyPrefs() {
    var t = prefs.theme === "auto" ? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light") : prefs.theme;
    var r = document.documentElement;
    r.dataset.theme = t; r.dataset.size = prefs.size; r.dataset.density = prefs.density;
    r.dataset.dimread = prefs.dimRead ? "on" : "off";
    var m = document.querySelectorAll('meta[name="theme-color"]');
    for (var i = 0; i < m.length; i++) m[i].setAttribute("content", t === "dark" ? "#17161a" : "#f6f2ea");
  }

  // ------------------------------------------------------------ text by language
  function useZh(it) { return it.lang !== "zh" && it.title_zh && prefs.lang !== "orig" && !it._orig; }
  function titleOf(it) { return useZh(it) ? it.title_zh : it.title; }
  function excerptOf(it) {
    if (it.lang !== "zh" && it.excerpt_zh && prefs.lang !== "orig" && !it._orig) return it.excerpt_zh;
    return it.excerpt || "";
  }
  function speakTitle(it) { return it.lang === "zh" ? it.title : (it.title_zh || it.title); }

  // ------------------------------------------------------------ heat
  function heatOf(it) {
    var s = S.src[it.src] || { w: 1 };
    var h = Math.max(0, (S.now - ts(it)) / 3600000);
    var cov = it.cn || 1;
    var eng = 0;
    if (it.eng) eng = (it.eng.likes || 0) + 2 * (it.eng.retweets || 0) + 1.5 * (it.eng.quotes || 0) + 0.4 * (it.eng.replies || 0);
    var base = (s.w || 1) + 1.25 * Math.log2(cov) + 0.9 * (it.top || 0) + 0.3 * Math.log10(1 + eng);
    return Math.pow(2, -h / 20) * base;
  }

  // ------------------------------------------------------------ data loading
  function fetchJSON(url) {
    return fetch(url, { cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
  }
  function loadDay(d) {
    if (S.loaded[d]) return Promise.resolve();
    if (S.loading[d]) return S.loading[d];
    var v = S.index ? encodeURIComponent(S.index.generated) : Date.now();
    S.loading[d] = fetchJSON(DATA + "day/" + d + ".json?v=" + v).then(function (j) {
      (j.items || []).forEach(function (it) {
        if (S.byId[it.id]) return;
        if (it.img && NOIMG.test(it.img)) it.img = "";
        S.byId[it.id] = it; S.items.push(it);
      });
      S.loaded[d] = true;
      buildClusters();
    }).catch(function () { S.loaded[d] = true; });
    return S.loading[d];
  }
  function buildClusters() {
    var c = {};
    S.items.forEach(function (it) {
      if (!it.cl) return;
      (c[it.cl] || (c[it.cl] = [])).push(it);
    });
    S.clusters = c;
  }
  function allLoaded() { return S.index && S.index.days.every(function (d) { return S.loaded[d.date]; }); }
  function loadAll() {
    if (!S.index) return Promise.resolve();
    return Promise.all(S.index.days.map(function (d) { return loadDay(d.date); }));
  }

  // ------------------------------------------------------------ blocking / follow
  function fullText(it) {
    if (!it._ft) it._ft = (it.title + " " + (it.title_zh || "") + " " + (it.excerpt || "") + " " + (it.excerpt_zh || "")).toLowerCase();
    return it._ft;
  }
  function blocked(it) {
    if (blockSrc.indexOf(it.src) >= 0) return true;
    if (!blockKw.length) return false;
    var text = fullText(it);
    for (var i = 0; i < blockKw.length; i++) if (text.indexOf(blockKw[i].toLowerCase()) >= 0) return true;
    return false;
  }
  function followHit(it) {
    if (!follow.length) return false;
    var text = fullText(it);
    for (var i = 0; i < follow.length; i++) {
      var w = follow[i];
      if (w.indexOf("topic:") === 0) { if ((it.topics || []).indexOf(w.slice(6)) >= 0) return true; continue; }
      if (text.indexOf(w.toLowerCase()) >= 0) return true;
    }
    return false;
  }

  // ------------------------------------------------------------ search
  function parseQuery(q) {
    var inc = [], exc = [], src = [];
    (q || "").trim().split(/\s+/).forEach(function (w) {
      if (!w) return;
      if (w[0] === "-" && w.length > 1) exc.push(w.slice(1).toLowerCase());
      else if (/^(来源|source)[:：]/.test(w)) src.push(w.split(/[:：]/)[1]);
      else inc.push(w.toLowerCase());
    });
    return { inc: inc, exc: exc, src: src };
  }
  function hay(it) {
    if (!it._h) it._h = fullText(it) + "\n" + srcName(it.src).toLowerCase();
    return it._h;
  }
  function matchQuery(it, pq) {
    var h = hay(it);
    for (var i = 0; i < pq.inc.length; i++) if (h.indexOf(pq.inc[i]) < 0) return false;
    for (var j = 0; j < pq.exc.length; j++) if (h.indexOf(pq.exc[j]) >= 0) return false;
    if (pq.src.length && pq.src.every(function (s) { return srcName(it.src).indexOf(s) < 0 && it.src !== s; })) return false;
    return true;
  }
  function hl(text, pq) {
    var out = esc(text);
    if (!pq || !pq.inc.length) return out;
    pq.inc.forEach(function (w) {
      var re = new RegExp("(" + esc(w).replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }

  // ------------------------------------------------------------ filtering
  function rangeOk(it) {
    if (S.date) return dayKey(ts(it)) === S.date;
    if (S.range === "all") return true;
    var lim = { "6h": 6, "24h": 24, "3d": 72 }[S.range] || 1e9;
    return S.now - ts(it) <= lim * 3600000;
  }
  function filterItems() {
    var f = S.f, pq = parseQuery(S.q);
    var hasQ = pq.inc.length || pq.exc.length || pq.src.length;
    return S.items.filter(function (it) {
      if (blocked(it)) return false;
      if (!rangeOk(it)) return false;
      if (f.cats.length && !(it.cats || []).some(function (c) { return f.cats.indexOf(c) >= 0; })) return false;
      if (f.geo.length && !(it.geo || []).some(function (c) { return f.geo.indexOf(c) >= 0; })) return false;
      if (f.topics.length && !(it.topics || []).some(function (c) { return f.topics.indexOf(c) >= 0; })) return false;
      if (f.stypes.length && f.stypes.indexOf((S.src[it.src] || {}).stype) < 0) return false;
      if (f.langs.length && f.langs.indexOf(it.lang === "zh" ? "zh" : "en") < 0) return false;
      if (f.srcs.length && f.srcs.indexOf(it.src) < 0) return false;
      if (S.onlyMulti && (it.cn || 1) < 2) return false;
      if (S.onlyImg && !it.img) return false;
      if (S.unread && readMap[it.id]) return false;
      if (S.followOnly && !followHit(it)) return false;
      if (hasQ && !matchQuery(it, pq)) return false;
      return true;
    });
  }
  function repScore(it) {
    var s = S.src[it.src] || { w: 1 };
    return (s.w || 1) + (it.lang === "zh" ? 0.35 : 0) + (it.title_zh ? 0.1 : 0) + (it.img ? 0.25 : 0) + (it.excerpt ? 0.15 : 0) + (it.top || 0) * 0.3 + (it.via === "x" ? -0.6 : 0);
  }
  // Collapse items of the same story into one entry.
  function group(list, force) {
    var map = {}, out = [], on = force || prefs.group;
    list.forEach(function (it) {
      if (on && it.cl) {
        var g = map[it.cl];
        if (!g) { g = map[it.cl] = { key: it.cl, items: [] }; out.push(g); }
        g.items.push(it);
      } else out.push({ key: it.id, items: [it] });
    });
    out.forEach(function (g) {
      if (g.items.length > 1) g.items.sort(function (a, b) { return repScore(b) - repScore(a); });
      g.it = g.items[0];
      var all = g.it.cl && S.clusters[g.it.cl] ? S.clusters[g.it.cl] : g.items;
      g.all = all.filter(function (x) { return !blocked(x); });
      g.heat = Math.max.apply(null, g.items.map(heatOf));
      g.t = Math.max.apply(null, g.items.map(ts));
      g.cov = g.it.cn || 1;
    });
    return out;
  }
  function sortGroups(gs, how) {
    var cmp = {
      hot: function (a, b) { return b.heat - a.heat; },
      new: function (a, b) { return b.t - a.t; },
      cover: function (a, b) { return b.cov - a.cov || b.heat - a.heat; },
      source: function (a, b) { return srcName(a.it.src).localeCompare(srcName(b.it.src), "zh-CN") || b.t - a.t; }
    }[how] || function (a, b) { return b.heat - a.heat; };
    return gs.sort(cmp);
  }

  // ------------------------------------------------------------ rendering pieces
  function imgTag(it, cls) {
    if (!prefs.images || !it.img) return "";
    return '<a class="thumb ' + (cls || "") + '" href="' + attr(it.url) + '" target="_blank" rel="noopener" tabindex="-1" data-open="' + it.id + '">' +
      '<img src="' + attr(it.img) + '" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.parentNode.remove()"></a>';
  }
  function metaHtml(it, g, opts) {
    opts = opts || {};
    var s = S.src[it.src] || {};
    var parts = ['<a class="src" href="#" data-src="' + it.src + '">' + esc(s.name || it.src) + "</a>"];
    parts.push('<time class="dot" datetime="' + attr(it.time) + '" title="' + attr(absTime(ts(it))) + '">' + rel(ts(it)) + "</time>");
    if (it.via === "x") parts.push('<span class="pill x">推特</span>');
    if (it.lang !== "zh" && !opts.brief) parts.push('<span class="pill">' + (it.title_zh ? "译" : "外文") + "</span>");
    if (it.top && it.top >= 0.5 && !opts.brief) parts.push('<span class="pill top">头条</span>');
    if (it.eng && it.eng.likes) parts.push('<span class="dot">赞 ' + fmtNum(it.eng.likes) + "</span>");
    if (lastVisit && ts(it) > lastVisit && !readMap[it.id] && !opts.brief) parts.push('<span class="new-dot">新</span>');
    return '<div class="meta">' + parts.join("") + "</div>";
  }
  function coverageHtml(g, max) {
    if (!g || (g.cov || 1) < 2) return "";
    var seen = {}, chips = [];
    g.all.forEach(function (x) {
      var n = srcName(x.src).replace(/ · 推特$/, "");
      if (seen[n]) return; seen[n] = 1;
      if (chips.length < (max || 6)) chips.push('<a class="src-chip" href="' + attr(x.url) + '" target="_blank" rel="noopener" data-open="' + x.id + '">' + esc(n) + "</a>");
    });
    return '<div class="coverage"><span class="cov-n">' + g.cov + " 家来源报道</span>" + chips.join("") + (g.cov > chips.length ? "<span>等</span>" : "") + "</div>";
  }
  function tagsHtml(it) {
    var tx = S.index.taxonomy, out = [];
    (it.cats || []).slice(0, 2).forEach(function (c) { var n = nameOf(tx.cats, c); if (n) out.push('<button class="tag cat" data-f="cats" data-v="' + c + '">' + n + "</button>"); });
    (it.geo || []).slice(0, 2).forEach(function (c) { var n = nameOf(tx.geo, c); if (n) out.push('<button class="tag" data-f="geo" data-v="' + c + '">' + n + "</button>"); });
    (it.topics || []).slice(0, 3).forEach(function (c) { var n = nameOf(tx.topics, c); if (n) out.push('<button class="tag" data-f="topics" data-v="' + c + '">#' + n + "</button>"); });
    return out.length ? '<div class="tags">' + out.join("") + "</div>" : "";
  }
  function cardHtml(g, pq) {
    var it = g.it;
    var t = titleOf(it), ex = excerptOf(it);
    var showBoth = it.lang !== "zh" && it.title_zh && prefs.lang === "both" && !it._orig;
    var html = '<article class="card' + (readMap[it.id] ? " read" : "") + '" data-id="' + it.id + '">';
    html += "<div>" + metaHtml(it, g);
    html += '<h3><a href="' + attr(it.url) + '" target="_blank" rel="noopener" data-open="' + it.id + '">' + hl(t, pq) + "</a>";
    if (showBoth) html += '<span class="orig">' + hl(it.title, pq) + "</span>";
    html += "</h3>";
    if (ex) html += '<p class="ex">' + hl(ex, pq) + "</p>";
    html += tagsHtml(it);
    html += '<div class="actions">' +
      '<button class="act" data-act="save" aria-pressed="' + !!saved[it.id] + '" title="收藏 (s)">' + ICON.star + "收藏</button>" +
      '<button class="act" data-act="later" aria-pressed="' + !!later[it.id] + '" title="稍后读 (l)">' + ICON.clock + "稍后读</button>" +
      (it.lang !== "zh" && it.title_zh ? '<button class="act" data-act="lang" title="原文 / 译文 (t)">' + ICON.trans + (useZh(it) ? "看原文" : "看译文") + "</button>" : "") +
      '<button class="act" data-act="copy" title="复制标题与链接">' + ICON.link + "复制</button>" +
      (navigator.share ? '<button class="act" data-act="share">' + ICON.share + "分享</button>" : "") +
      '<button class="act" data-act="read" aria-pressed="' + !!readMap[it.id] + '" title="标记已读 (m)">' + ICON.check + "<span>" + (readMap[it.id] ? "已读" : "标为已读") + "</span></button>" +
      '<button class="act" data-act="block" title="不再显示此来源">' + ICON.hide + "屏蔽来源</button>" +
      "</div></div>";
    html += imgTag(it);
    if (g.all && g.all.length > 1) {
      var others = g.all.filter(function (x) { return x.id !== it.id; }).sort(function (a, b) { return ts(a) - ts(b); });
      html += '<div class="cluster"><button type="button" data-act="cluster">' + g.cov + " 家来源报道 · 查看另外 " + others.length + " 篇</button><ul>" +
        others.map(function (x) {
          return '<li><span class="s">' + esc(srcName(x.src)) + '</span><a href="' + attr(x.url) + '" target="_blank" rel="noopener" data-open="' + x.id + '">' + esc(titleOf(x)) + '</a><time title="' + attr(absTime(ts(x))) + '">' + rel(ts(x)) + "</time></li>";
        }).join("") + "</ul></div>";
    }
    return html + "</article>";
  }
  function skeleton() {
    var s = "";
    for (var i = 0; i < 6; i++) s += '<div class="skeleton sk-line" style="width:' + (90 - i * 9) + '%"></div>';
    return '<div style="padding:12px 0">' + s + "</div>";
  }

  // ------------------------------------------------------------ sections nav
  function currentSec() {
    if (S.view === "home") return "home";
    if (S.view !== "list") return S.view;
    if (S.followOnly) return "follow";
    var f = S.f, others = f.geo.length + f.topics.length + f.stypes.length + f.langs.length + f.srcs.length;
    if (f.cats.length === 1 && !others && !S.q) return f.cats[0];
    if (!f.cats.length && !others && !S.q) return "all";
    return "";
  }
  function renderSections() {
    var tx = S.index ? S.index.taxonomy.cats : [];
    var cur = currentSec();
    var btn = function (id, label, n) {
      return '<button type="button" class="sec" data-sec="' + id + '" aria-current="' + (cur === id) + '">' + label + (n ? '<span class="n">' + n + "</span>" : "") + "</button>";
    };
    var html = btn("home", "要闻") + btn("all", "全部");
    CAT_ORDER.forEach(function (c) { var n = nameOf(tx, c); if (n) html += btn(c, n); });
    html += '<span class="sec-sep"></span>' + btn("timeline", "时间轴") + btn("follow", "关注") + btn("mine", "我的", Object.keys(later).length || "");
    $("#sections").innerHTML = html;
    var on = $('.sec[aria-current="true"]');
    if (on && window.innerWidth < 860) {
      var box = $("#sections");
      box.scrollLeft = on.offsetLeft - box.clientWidth / 2 + on.clientWidth / 2;
    }
  }

  // ------------------------------------------------------------ home
  function homeGroups(hours) {
    var lim = S.now - hours * 3600000;
    var list = S.items.filter(function (it) { return ts(it) >= lim && !blocked(it); });
    return sortGroups(group(list, true), "hot");
  }
  function followLabel(w) {
    if (w.indexOf("topic:") === 0) return "#" + (nameOf(S.index ? S.index.taxonomy.topics : [], w.slice(6)) || w.slice(6));
    return w;
  }
  function newCount() {
    if (!lastVisit) return 0;
    return S.items.filter(function (it) { return ts(it) > lastVisit && !blocked(it); }).length;
  }
  // Prefer a member that carries a picture when showing a story prominently.
  function visual(g) {
    if (!prefs.images || g.it.img) return g;
    var best = null;
    g.items.forEach(function (x) { if (x.img && x.via !== "x" && (!best || repScore(x) > repScore(best))) best = x; });
    if (!best) return g;
    var c = Object.assign({}, g); c.it = best; return c;
  }
  function renderHome() {
    var el = $("#view-home");
    if (!S.items.length) { el.innerHTML = skeleton(); return; }
    var gs = homeGroups(36);
    var used = {};
    var take = function (g) { used[g.key] = 1; return g; };
    var hero = gs[0] ? visual(take(gs[0])) : null;
    var leads = gs.slice(1, 5).map(take).map(visual);
    var rank = gs.slice(5, 17).map(take);
    var tx = S.index.taxonomy;
    var html = '<div class="home-grid"><div class="home-main">';
    if (hero) {
      var it = hero.it, img = prefs.images && it.img;
      html += '<p class="kicker">今日要闻<button class="more" data-sec="all">全部新闻 →</button></p>';
      html += '<article class="hero' + (img ? "" : " noimg") + '" data-id="' + it.id + '">' +
        (img ? '<a class="hero-img" href="' + attr(it.url) + '" target="_blank" rel="noopener" tabindex="-1" data-open="' + it.id + '"><img src="' + attr(it.img) + '" alt="" referrerpolicy="no-referrer" onerror="this.parentNode.parentNode.classList.add(\'noimg\');this.parentNode.remove()"></a>' : "") +
        "<div>" + metaHtml(it, hero) +
        '<h2><a href="' + attr(it.url) + '" target="_blank" rel="noopener" data-open="' + it.id + '">' + esc(titleOf(it)) + "</a></h2>" +
        (excerptOf(it) ? '<p class="dek">' + esc(excerptOf(it)) + "</p>" : "") +
        coverageHtml(hero, 7) + "</div></article>";
    }
    if (leads.length) {
      html += '<div class="leads">' + leads.map(function (g) {
        var it = g.it;
        return '<article class="lead" data-id="' + it.id + '"><div>' + metaHtml(it, g) +
          '<h3><a href="' + attr(it.url) + '" target="_blank" rel="noopener" data-open="' + it.id + '">' + esc(titleOf(it)) + "</a></h3>" +
          (excerptOf(it) ? "<p>" + esc(excerptOf(it)) + "</p>" : "") +
          (g.cov > 1 ? '<div class="coverage" style="margin-top:6px"><span class="cov-n">' + g.cov + " 家来源报道</span></div>" : "") +
          "</div>" + imgTag(it) + "</article>";
      }).join("") + "</div>";
    }
    var hot = (S.index.hot || []).slice(0, 24);
    if (hot.length) {
      html += '<div class="hotwords" aria-label="今日热词"><span class="kicker" style="width:100%;margin:0 0 2px">今日热词</span>' + hot.map(function (h, i) {
        return '<button class="hw ' + (i < 4 ? "l1" : i < 10 ? "l2" : "") + '" data-q="' + attr(h.w) + '">' + esc(h.w) + "<b>" + h.n + "</b></button>";
      }).join("") + "</div>";
    }
    html += '<div class="sec-grid">';
    var secGroups = homeGroups(48);
    HOME_SECTIONS.forEach(function (c) {
      var name = nameOf(tx.cats, c);
      var list = secGroups.filter(function (g) { return !used[g.key] && (g.it.cats || [])[0] === c; }).slice(0, 5);
      if (list.length < 3) list = secGroups.filter(function (g) { return !used[g.key] && (g.it.cats || []).indexOf(c) >= 0; }).slice(0, 5);
      if (!list.length) return;
      list.forEach(take);
      list = list.map(visual);
      var withImg = prefs.images ? list.filter(function (g) { return g.it.img; })[0] : null;
      if (withImg && withImg !== list[0] && list.indexOf(withImg) < 3) { list.splice(list.indexOf(withImg), 1); list.unshift(withImg); }
      var top = list[0];
      html += '<section class="sec-block"><h4>' + name + '<button data-sec="' + c + '">更多 →</button></h4>' +
        '<div class="sec-top">' + imgTag(top.it) +
        '<h5><a href="' + attr(top.it.url) + '" target="_blank" rel="noopener" data-open="' + top.it.id + '">' + esc(titleOf(top.it)) + "</a></h5>" + metaHtml(top.it, top, { brief: true }) + "</div>" +
        '<ul class="sec-list">' + list.slice(1).map(function (g) {
          return '<li><a href="' + attr(g.it.url) + '" target="_blank" rel="noopener" data-open="' + g.it.id + '">' + esc(titleOf(g.it)) + "</a>" + metaHtml(g.it, g, { brief: true }) + "</li>";
        }).join("") + "</ul></section>";
    });
    html += "</div></div>";

    var maxHeat = Math.max(hero ? hero.heat : 0, rank.length ? rank[0].heat : 0) || 1;
    html += '<aside class="side">';
    html += '<div class="side-box"><h3>热度榜<button class="link-btn" data-sort-go="hot">完整榜单</button></h3><ol class="rank">' + rank.map(function (g) {
      return '<li><a href="' + attr(g.it.url) + '" target="_blank" rel="noopener" data-open="' + g.it.id + '">' + esc(titleOf(g.it)) + "</a>" +
        '<div class="meta"><span class="src">' + esc(srcName(g.it.src)) + "</span>" + (g.cov > 1 ? '<span class="dot">' + g.cov + " 家报道</span>" : "") + '<span class="dot">' + rel(g.t) + "</span></div>" +
        '<div class="heat-bar"><i style="width:' + Math.max(8, Math.round(g.heat / maxHeat * 100)) + '%"></i></div></li>';
    }).join("") + "</ol></div>";

    html += '<div class="side-box"><h3>我的关注<button class="link-btn" data-act="edit-follow">设置</button></h3>';
    if (follow.length) {
      var fl = S.items.filter(function (it) { return !blocked(it) && followHit(it); }).sort(function (a, b) { return ts(b) - ts(a); }).slice(0, 6);
      html += '<div class="follow-chips">' + follow.map(function (w) { return '<span class="chip">' + esc(followLabel(w)) + "</span>"; }).join("") + "</div>";
      html += fl.length ? '<ul class="mini-list">' + fl.map(function (it) {
        return '<li><a href="' + attr(it.url) + '" target="_blank" rel="noopener" data-open="' + it.id + '">' + esc(titleOf(it)) + '</a><div class="meta"><span class="src">' + esc(srcName(it.src)) + '</span><span class="dot">' + rel(ts(it)) + "</span></div></li>";
      }).join("") + '</ul><p style="margin:8px 0 0"><button class="link-btn" data-sec="follow">查看全部关注 →</button></p>' : '<p class="muted" style="font-size:13px">近几天没有相符的新闻。</p>';
    } else {
      html += '<p class="muted" style="font-size:13.5px;margin:0 0 10px">添加关键词或话题，例如“高考”“新能源”“航天”，相关新闻会集中出现在这里。</p><button class="btn" data-act="edit-follow">添加关注</button>';
    }
    html += "</div>";

    var lk = Object.keys(later);
    html += '<div class="side-box"><h3>稍后读<button class="link-btn" data-sec="mine">全部</button></h3>';
    html += lk.length ? '<ul class="mini-list">' + lk.slice(-5).reverse().map(function (id) {
      var x = later[id];
      return '<li><a href="' + attr(x.url) + '" target="_blank" rel="noopener" data-open="' + id + '">' + esc(x.title_zh && prefs.lang !== "orig" ? x.title_zh : x.title) + '</a><div class="meta"><span class="src">' + esc(srcName(x.src)) + "</span></div></li>";
    }).join("") + "</ul>" : '<p class="muted" style="font-size:13.5px;margin:0">在任意新闻下点“稍后读”，就会收进这里。</p>';
    html += "</div>";

    var st = S.index;
    var okSrc = st.sources.filter(function (s) { return s.ok; }).length;
    html += '<div class="side-box"><h3>本站概况</h3><div class="stat-row"><div><b>' + fmtNum(st.count) + "</b><span>条新闻</span></div><div><b>" + okSrc + "</b><span>个来源</span></div><div><b>" + fmtNum(st.clusters) + "</b><span>组多源报道</span></div></div>" +
      '<p class="muted" style="font-size:12.5px;margin:10px 0 0">收录最近 ' + st.window_days + " 天，约每两小时更新一次。<button class=\"link-btn\" data-sec=\"sources\">查看来源 →</button></p></div>";
    html += "</aside></div>";
    el.innerHTML = html;
  }

  // ------------------------------------------------------------ filters panel
  var FGROUPS = [["cats", "分类"], ["geo", "地区"], ["topics", "话题"], ["stypes", "来源类型"], ["langs", "语言"], ["srcs", "来源"]];
  var openGroups = load("zw.fopen", { cats: true, geo: true, topics: true, range: true, opts: true });
  var srcFilterQ = "";
  function filterItemsExcept(key) {
    var keep = S.f[key]; S.f[key] = [];
    var r = filterItems(); S.f[key] = keep; return r;
  }
  function counts(key) {
    var c = {};
    filterItemsExcept(key).forEach(function (it) {
      var vals = key === "stypes" ? [(S.src[it.src] || {}).stype] : key === "langs" ? [it.lang === "zh" ? "zh" : "en"] : key === "srcs" ? [it.src] : (it[key] || []);
      vals.forEach(function (v) { c[v] = (c[v] || 0) + 1; });
    });
    return c;
  }
  function toggleRow(id, label, on) {
    return '<label class="toggle-row">' + label + '<input type="checkbox" class="switch" data-toggle="' + id + '"' + (on ? " checked" : "") + "></label>";
  }
  function renderFilters() {
    var tx = S.index.taxonomy, html = "";
    html += '<details class="fgroup" data-g="range"' + (openGroups.range ? " open" : "") + "><summary>时间" + (S.range !== "all" || S.date ? '<span class="sel-n">1</span>' : "") + "</summary>" +
      '<div class="chips">' + [["all", "不限"], ["6h", "6 小时内"], ["24h", "24 小时内"], ["3d", "3 天内"]].map(function (r) {
        return '<button class="chip" data-range="' + r[0] + '" aria-pressed="' + (!S.date && S.range === r[0]) + '">' + r[1] + "</button>";
      }).join("") + '</div><div class="date-strip">' + S.index.days.map(function (d) {
        var p = d.date.split("-");
        var w = WEEK[new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])).getUTCDay()];
        return '<button class="chip" data-date="' + d.date + '" aria-pressed="' + (S.date === d.date) + '" title="' + d.count + ' 条">' + (+p[1]) + "/" + (+p[2]) + "<small>周" + w + "</small></button>";
      }).join("") + "</div></details>";
    FGROUPS.forEach(function (gp) {
      var key = gp[0], c = counts(key), sel = S.f[key], list;
      if (key === "cats") list = tx.cats;
      else if (key === "geo") list = tx.geo;
      else if (key === "topics") list = tx.topics.slice().sort(function (a, b) { return (c[b.id] || 0) - (c[a.id] || 0); });
      else if (key === "stypes") list = tx.stypes;
      else if (key === "langs") list = tx.langs;
      else list = S.index.sources.map(function (s) { return { id: s.id, name: s.name }; }).sort(function (a, b) { return (c[b.id] || 0) - (c[a.id] || 0); });
      var chips = list.filter(function (o) { return c[o.id] || sel.indexOf(o.id) >= 0; });
      if (key === "srcs" && srcFilterQ) chips = chips.filter(function (o) { return o.name.toLowerCase().indexOf(srcFilterQ.toLowerCase()) >= 0 || sel.indexOf(o.id) >= 0; });
      var limit = key === "srcs" && !openGroups.srcsAll ? 30 : key === "topics" && !openGroups.topicsAll ? 20 : 999;
      html += '<details class="fgroup" data-g="' + key + '"' + (openGroups[key] ? " open" : "") + "><summary>" + gp[1] + (sel.length ? '<span class="sel-n">' + sel.length + "</span>" : "") + "</summary>";
      if (key === "srcs") html += '<input class="src-search" id="src-search" type="search" placeholder="查找来源" value="' + attr(srcFilterQ) + '">';
      html += '<div class="chips">' + chips.slice(0, limit).map(function (o) {
        return '<button class="chip" data-f="' + key + '" data-v="' + o.id + '" aria-pressed="' + (sel.indexOf(o.id) >= 0) + '">' + esc(o.name) + '<span class="c">' + (c[o.id] || 0) + "</span></button>";
      }).join("") + (chips.length > limit ? '<button class="link-btn" data-more="' + key + '">展开全部 ' + chips.length + " 项</button>" : "") + "</div></details>";
    });
    html += '<details class="fgroup" data-g="opts"' + (openGroups.opts ? " open" : "") + '><summary>显示</summary><div style="margin-top:8px">' +
      toggleRow("onlyMulti", "只看多家来源报道", S.onlyMulti) +
      toggleRow("group", "合并同一事件的报道", prefs.group) +
      toggleRow("onlyImg", "只看带图片的", S.onlyImg) +
      toggleRow("unread", "只看未读", S.unread) +
      "</div></details>";
    $("#filter-body").innerHTML = html;
    var n = activeCount();
    var b = $("#filter-badge"); b.hidden = !n; b.textContent = n;
    var ss = $("#src-search");
    if (ss) ss.addEventListener("input", debounce(function () {
      srcFilterQ = ss.value; renderFilters();
      var s2 = $("#src-search"); s2.focus(); s2.setSelectionRange(s2.value.length, s2.value.length);
    }, 200));
  }
  function activeCount() {
    var n = 0;
    FGROUPS.forEach(function (g) { n += S.f[g[0]].length; });
    if (S.range !== "all" || S.date) n++;
    if (S.onlyMulti) n++; if (S.onlyImg) n++; if (S.unread) n++;
    return n;
  }
  function renderActiveBar() {
    var tx = S.index.taxonomy, chips = [];
    var lists = { cats: tx.cats, geo: tx.geo, topics: tx.topics, stypes: tx.stypes, langs: tx.langs, srcs: S.index.sources };
    FGROUPS.forEach(function (g) {
      S.f[g[0]].forEach(function (v) {
        chips.push('<button class="chip x" data-f="' + g[0] + '" data-v="' + v + '" aria-pressed="true">' + esc(nameOf(lists[g[0]], v) || v) + "</button>");
      });
    });
    if (S.date) chips.push('<button class="chip x" data-date="' + S.date + '" aria-pressed="true">' + (+S.date.slice(5, 7)) + "月" + (+S.date.slice(8)) + "日</button>");
    else if (S.range !== "all") chips.push('<button class="chip x" data-range="all" aria-pressed="true">' + { "6h": "6 小时内", "24h": "24 小时内", "3d": "3 天内" }[S.range] + "</button>");
    if (S.q) chips.push('<button class="chip x" data-clear-q="1" aria-pressed="true">搜索：' + esc(S.q) + "</button>");
    if (S.followOnly) chips.push('<button class="chip x" data-follow-off="1" aria-pressed="true">我的关注</button>');
    if (S.onlyMulti) chips.push('<button class="chip x" data-toggle-off="onlyMulti" aria-pressed="true">多家来源报道</button>');
    if (S.onlyImg) chips.push('<button class="chip x" data-toggle-off="onlyImg" aria-pressed="true">带图片</button>');
    if (S.unread) chips.push('<button class="chip x" data-toggle-off="unread" aria-pressed="true">未读</button>');
    var bar = $("#active-bar");
    bar.hidden = !chips.length;
    bar.innerHTML = chips.join("") + (chips.length > 1 ? '<button class="link-btn" id="clear-all">全部清除</button>' : "");
  }

  // ------------------------------------------------------------ list view
  function listTitle() {
    var f = S.f, tx = S.index.taxonomy;
    if (S.followOnly) return "我的关注";
    if (f.cats.length === 1) return nameOf(tx.cats, f.cats[0]);
    if (f.topics.length === 1 && !f.cats.length) return "#" + nameOf(tx.topics, f.topics[0]);
    if (f.geo.length === 1 && !f.cats.length) return nameOf(tx.geo, f.geo[0]);
    if (f.srcs.length === 1 && !f.cats.length) return srcName(f.srcs[0]);
    if (S.q) return "搜索结果";
    return "全部新闻";
  }
  function renderList(keepScroll) {
    if (!S.index) return;
    $("#list-title").textContent = listTitle();
    $$("#sort-seg button").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.sort === S.sort); });
    var items = filterItems();
    var gs = sortGroups(group(items), S.sort);
    S.list = gs; S.shown = 0; S.focus = -1;
    $("#list-count").textContent = (gs.length ? "共 " + items.length + " 条" + (prefs.group && gs.length !== items.length ? "，合并为 " + gs.length + " 组" : "") : "") + (allLoaded() ? "" : " · 正在载入更早的新闻…");
    $("#list").innerHTML = "";
    if (!gs.length) {
      $("#list").innerHTML = '<div class="empty"><h3>没有找到相符的新闻</h3><p>' + (S.followOnly && !follow.length ? '还没有添加关注，<button class="link-btn" data-act="edit-follow">现在添加</button>' : "试试减少筛选条件，或换个关键词。") + "</p></div>";
      $("#sentinel").textContent = "";
    } else more();
    renderFilters();
    renderActiveBar();
    renderSections();
    if (!keepScroll) window.scrollTo({ top: 0 });
  }
  function more() {
    var pq = parseQuery(S.q);
    var slice = S.list.slice(S.shown, S.shown + PAGE);
    if (!slice.length) return;
    var html = "", lastDay = S.shown ? dayKey(S.list[S.shown - 1].t) : null;
    slice.forEach(function (g) {
      if (S.sort === "new") {
        var dk = dayKey(g.t);
        if (dk !== lastDay) { html += daySep(dk); lastDay = dk; }
      }
      html += cardHtml(g, pq);
    });
    $("#list").insertAdjacentHTML("beforeend", html);
    S.shown += slice.length;
    $("#sentinel").textContent = S.shown >= S.list.length ? (S.list.length > 8 ? "已经到底了" : "") : "继续载入…";
  }
  function daySep(dk) {
    var p = dk.split("-"), w = WEEK[new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])).getUTCDay()];
    var label = dk === dayKey(S.now) ? "今天" : dk === dayKey(S.now - 86400000) ? "昨天" : "";
    return '<div class="day-sep"><b>' + (+p[1]) + "月" + (+p[2]) + "日</b>周" + w + (label ? " · " + label : "") + "</div>";
  }

  // ------------------------------------------------------------ timeline
  function renderTimeline() {
    var el = $("#view-timeline");
    if (!S.index) return;
    if (!S.day || !S.index.days.some(function (d) { return d.date === S.day; })) S.day = S.index.days[0] ? S.index.days[0].date : dayKey(S.now);
    var tx = S.index.taxonomy;
    var html = '<div class="tl-head"><div class="list-title"><h1>时间轴</h1><p class="muted">按发布时间逐时浏览，同一事件只列一次。</p></div>' +
      '<div class="toolbar"><label class="toggle-row" style="gap:8px">只看多家报道<input type="checkbox" class="switch" id="tl-multi"' + (S.tlMulti ? " checked" : "") + "></label></div></div>";
    html += '<div class="tl-days">' + S.index.days.map(function (d) {
      var p = d.date.split("-"), w = WEEK[new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])).getUTCDay()];
      return '<button class="tl-day" data-day="' + d.date + '" aria-pressed="' + (S.day === d.date) + '"><small>' + (+p[1]) + "月 · 周" + w + "</small><b>" + (+p[2]) + "</b><small>" + d.count + " 条</small></button>";
    }).join("") + "</div>";
    html += '<div class="tl-cats"><button class="chip" data-tlcat="" aria-pressed="' + !S.tlCat + '">全部</button>' + CAT_ORDER.map(function (c) {
      return '<button class="chip" data-tlcat="' + c + '" aria-pressed="' + (S.tlCat === c) + '">' + nameOf(tx.cats, c) + "</button>";
    }).join("") + "</div>";
    if (!S.loaded[S.day]) {
      el.innerHTML = html + skeleton();
      loadDay(S.day).then(function () { if (S.view === "timeline") renderTimeline(); });
      return;
    }
    var day = S.day;
    var list = S.items.filter(function (it) {
      return dayKey(ts(it)) === day && !blocked(it) && (!S.tlCat || (it.cats || []).indexOf(S.tlCat) >= 0) && (!S.tlMulti || (it.cn || 1) > 1);
    });
    var gs = group(list, true);
    gs.forEach(function (g) { g.t0 = Math.min.apply(null, g.items.map(ts)); });
    gs.sort(function (a, b) { return b.t0 - a.t0; });
    var hours = {};
    gs.forEach(function (g) { var h = shDate(g.t0).h; (hours[h] || (hours[h] = [])).push(g); });
    var maxN = 1, h;
    for (h = 0; h < 24; h++) maxN = Math.max(maxN, (hours[h] || []).length);
    html += '<div class="tl-bars" aria-label="每小时新闻数">';
    for (h = 0; h < 24; h++) {
      var n = (hours[h] || []).length;
      html += '<button style="height:' + Math.max(3, n / maxN * 100) + '%" data-hour="' + h + '" title="' + h + ":00 · " + n + ' 组" aria-label="' + h + "时 " + n + ' 组"></button>';
    }
    html += '</div><div class="tl-axis"><span>0 时</span><span>6 时</span><span>12 时</span><span>18 时</span><span>24 时</span></div>';
    html += '<div class="tl">';
    if (!gs.length) html += '<div class="empty"><h3>这一天没有相符的新闻</h3></div>';
    Object.keys(hours).map(Number).sort(function (a, b) { return b - a; }).forEach(function (hh) {
      var arr = hours[hh];
      html += '<div class="tl-hour" id="tl-h' + hh + '"><h4>' + pad(hh) + ":00<small>" + arr.length + ' 组</small></h4><div class="tl-items">' + arr.map(function (g) {
        var it = g.it;
        return '<div class="tl-item' + (g.cov >= 3 ? " hot" : "") + '" data-id="' + it.id + '"><div class="meta"><time>' + hm(g.t0) + '</time><a class="src" href="#" data-src="' + it.src + '">' + esc(srcName(it.src)) + "</a>" + (g.cov > 1 ? '<span class="dot cov-n" style="font-size:12px">' + g.cov + " 家来源</span>" : "") + "</div>" +
          '<h3><a href="' + attr(it.url) + '" target="_blank" rel="noopener" data-open="' + it.id + '">' + esc(titleOf(it)) + "</a></h3></div>";
      }).join("") + "</div></div>";
    });
    html += "</div>";
    el.innerHTML = html;
  }

  // ------------------------------------------------------------ mine
  function mineList() {
    var arr = S.tab === "saved" ? Object.keys(saved).map(function (k) { return saved[k]; }) :
      S.tab === "later" ? Object.keys(later).map(function (k) { return later[k]; }) : hist.slice();
    return arr.sort(function (a, b) { return (b._at || 0) - (a._at || 0); });
  }
  function renderMine() {
    var el = $("#view-mine");
    var tabs = [["saved", "收藏", Object.keys(saved).length], ["later", "稍后读", Object.keys(later).length], ["hist", "浏览记录", hist.length]];
    var html = '<div class="tabs">' + tabs.map(function (t) {
      return '<button data-tab="' + t[0] + '" aria-pressed="' + (S.tab === t[0]) + '">' + t[1] + '<span class="n">' + t[2] + "</span></button>";
    }).join("") + "</div>";
    var arr = mineList();
    html += '<div class="mine-tools">' + (arr.length ? '<button class="btn" data-act="export-list">复制为文本</button><button class="btn danger" data-act="clear-list">清空</button>' : "") + "</div>";
    if (!arr.length) {
      html += '<div class="empty"><h3>' + { saved: "还没有收藏", later: "稍后读是空的", hist: "还没有浏览记录" }[S.tab] + "</h3><p>" +
        { saved: "点新闻下方的“收藏”，就会长期保存在这台设备上。", later: "看到想读的新闻，点“稍后读”先放这里，打开后会自动移出。", hist: "在本站点开的新闻会记在这里，方便找回。" }[S.tab] + "</p></div>";
    } else {
      html += '<div class="cards">' + arr.map(function (snapIt) {
        var it = S.byId[snapIt.id] || snapIt;
        return cardHtml({ it: it, all: [it], cov: 1, items: [it] });
      }).join("") + "</div>";
    }
    el.innerHTML = html;
  }

  // ------------------------------------------------------------ sources
  function renderSources() {
    var el = $("#view-sources");
    var st = S.index, tx = st.taxonomy;
    var ok = st.sources.filter(function (s) { return s.ok; }).length;
    var zh = st.sources.filter(function (s) { return s.lang === "zh"; }).length;
    var html = '<div class="list-head"><div class="list-title"><h1>来源一览</h1><p class="muted">每条新闻都标明出处，点来源名可只看它的报道。</p></div></div>';
    html += '<div class="src-sum"><div><b>' + st.sources.length + "</b><span>收录来源</span></div><div><b>" + ok + "</b><span>本次更新正常</span></div><div><b>" + zh + "</b><span>中文来源</span></div><div><b>" + (st.sources.length - zh) + "</b><span>外文来源（附译文）</span></div></div>";
    html += '<div class="src-groups">' + [{ id: "", name: "全部" }].concat(tx.stypes).map(function (t) {
      return '<button class="chip" data-stype="' + t.id + '" aria-pressed="' + ((S.stypeView || "") === t.id) + '">' + t.name + "</button>";
    }).join("") + "</div>";
    var list = st.sources.filter(function (s) { return !S.stypeView || s.stype === S.stypeView; });
    list.sort(function (a, b) { return b.count - a.count; });
    html += '<table class="src-table"><thead><tr><th>来源</th><th class="hide-m">类型</th><th class="hide-m">语言</th><th>状态</th><th style="text-align:right">收录</th><th></th></tr></thead><tbody>' + list.map(function (s) {
      var isBlocked = blockSrc.indexOf(s.id) >= 0;
      return '<tr><td><a href="#" data-src="' + s.id + '"><b>' + esc(s.name) + '</b></a><br><a class="muted" style="font-size:12px" href="' + attr(s.home) + '" target="_blank" rel="noopener">' + esc(hostOf(s.home)) + "</a></td>" +
        '<td class="hide-m">' + esc(nameOf(tx.stypes, s.stype)) + '</td><td class="hide-m">' + (s.lang === "zh" ? "中文" : "英文") + "</td>" +
        '<td><span class="st' + (s.ok ? "" : " bad") + '">' + (s.ok ? "正常" : "本次未更新") + "</span></td>" +
        '<td class="num">' + s.count + "</td>" +
        '<td><button class="link-btn" data-block-src="' + s.id + '">' + (isBlocked ? "取消屏蔽" : "屏蔽") + "</button></td></tr>";
    }).join("") + "</tbody></table>";
    el.innerHTML = html;
  }

  // ------------------------------------------------------------ dialogs
  function openDlg(title, body, after) {
    $("#dlg-title").textContent = title;
    $("#dlg-body").innerHTML = body;
    var d = $("#dlg");
    if (!d.open) { if (d.showModal) d.showModal(); else d.setAttribute("open", ""); }
    if (after) after($("#dlg-body"));
  }
  function closeDlg() { var d = $("#dlg"); if (d.open) { if (d.close) d.close(); else d.removeAttribute("open"); } stopSpeak(); }

  function settingsBody() {
    var seg = function (key, opts) {
      return '<div class="seg">' + opts.map(function (o) { return '<button data-pref="' + key + '" data-val="' + o[0] + '" aria-pressed="' + (String(prefs[key]) === String(o[0])) + '">' + o[1] + "</button>"; }).join("") + "</div>";
    };
    var topics = S.index ? S.index.taxonomy.topics : [];
    return "<h3>阅读</h3>" +
      '<div class="set-row"><span>外观</span>' + seg("theme", [["auto", "跟随系统"], ["light", "浅色"], ["dark", "深色"]]) + "</div>" +
      '<div class="set-row"><span>字号</span>' + seg("size", [["s", "小"], ["m", "中"], ["l", "大"], ["xl", "特大"]]) + "</div>" +
      '<div class="set-row"><span>列表密度</span>' + seg("density", [["cozy", "舒适"], ["compact", "紧凑"]]) + "</div>" +
      '<div class="set-row"><span>外文标题<small>外文新闻已附中文译文</small></span>' + seg("lang", [["zh", "译文"], ["both", "双语"], ["orig", "原文"]]) + "</div>" +
      '<div class="set-row"><span>显示配图</span><input type="checkbox" class="switch" data-pref-bool="images"' + (prefs.images ? " checked" : "") + "></div>" +
      '<div class="set-row"><span>已读新闻变淡</span><input type="checkbox" class="switch" data-pref-bool="dimRead"' + (prefs.dimRead ? " checked" : "") + "></div>" +
      '<div class="set-row"><span>合并同一事件<small>多家来源报道同一件事时只显示一条</small></span><input type="checkbox" class="switch" data-pref-bool="group"' + (prefs.group ? " checked" : "") + "></div>" +
      "<h3>关注</h3><p>含有这些词或属于这些话题的新闻，会出现在“关注”栏目和首页右侧。</p>" + wordEditor("follow", follow, "输入关键词，如：高考、航天") +
      '<div class="chips" style="margin-top:4px">' + topics.map(function (t) {
        var on = follow.indexOf("topic:" + t.id) >= 0;
        return '<button class="chip" data-follow-topic="' + t.id + '" aria-pressed="' + on + '">#' + esc(t.name) + "</button>";
      }).join("") + "</div>" +
      "<h3>屏蔽</h3><p>含有这些词的新闻不再显示。</p>" + wordEditor("blockKw", blockKw, "输入要屏蔽的词") +
      '<p style="margin-top:10px">已屏蔽的来源：</p><div class="word-list">' + (blockSrc.length ? blockSrc.map(function (id) { return '<button class="chip x" data-unblock="' + id + '">' + esc(srcName(id)) + "</button>"; }).join("") : '<span class="muted">无</span>') + "</div>" +
      "<h3>数据</h3><p>收藏、稍后读、已读记录和设置只保存在这台设备的浏览器里，换设备前可以先导出备份。</p>" +
      '<div class="brief-tools"><button class="btn" data-act="export-data">导出备份</button><label class="btn" style="cursor:pointer">导入备份<input type="file" accept="application/json" id="import-file" hidden></label>' +
      '<button class="btn" data-act="clear-read">清除已读记录</button><button class="btn danger" data-act="reset-all">恢复初始状态</button></div>';
  }
  function wordEditor(key, arr, ph) {
    return '<div class="word-list">' + arr.filter(function (w) { return w.indexOf("topic:") !== 0; }).map(function (w) {
      return '<button class="chip x" data-del-word="' + key + '" data-w="' + attr(w) + '">' + esc(w) + "</button>";
    }).join("") + '</div><form class="add-row" data-add-word="' + key + '"><input type="text" placeholder="' + attr(ph) + '" maxlength="30" aria-label="' + attr(ph) + '"><button class="btn" type="submit">添加</button></form>';
  }
  function bindSettings(b) { var imp = $("#import-file", b); if (imp) imp.addEventListener("change", importData); }
  function openSettings(scrollTo) {
    openDlg("阅读设置", settingsBody(), function (b) {
      bindSettings(b);
      if (scrollTo) { var f = $('[data-add-word="' + scrollTo + '"] input', b); if (f) { f.scrollIntoView({ block: "center" }); f.focus(); } }
    });
  }
  function refreshSettings() {
    var body = $("#dlg-body"), top = body.scrollTop;
    if ($("#dlg-title").textContent !== "阅读设置") return;
    body.innerHTML = settingsBody();
    body.scrollTop = top;
    bindSettings(body);
  }
  function kbdTable() {
    var rows = [["/", "搜索"], ["j / k", "下一条 / 上一条"], ["o 或 Enter", "打开当前新闻"], ["s", "收藏"], ["l", "稍后读"], ["m", "标为已读"], ["t", "原文 / 译文"], ["g 然后 h", "回到要闻"], ["?", "显示快捷键"]];
    return '<table class="kbd-table">' + rows.map(function (r) { return "<tr><td><kbd>" + r[0] + "</kbd></td><td>" + r[1] + "</td></tr>"; }).join("") + "</table>";
  }
  function aboutBody() {
    var st = S.index;
    return "<p>朝闻把国内外各家媒体、通讯社和机构公开发布的新闻汇到一处。每条新闻都注明来源和发布时间，点标题即前往原网站阅读全文。</p>" +
      "<h3>多源归并</h3><p>不同来源报道同一件事时，会合并成一条并标出“几家来源报道”，展开可以对照各家的标题和角度。报道的来源越多、越新，热度越高。</p>" +
      "<h3>外文新闻</h3><p>英文报道附有中文译文，可在设置里改为显示原文或中英对照，也可以在单条新闻上切换。译文为机器翻译，仅供参考。</p>" +
      "<h3>更新</h3><p>大约每两小时自动更新一次，保留最近 " + (st ? st.window_days : 7) + " 天的新闻。" + (st ? "本次更新于 " + absTime(Date.parse(st.generated)) + "。" : "") + "</p>" +
      "<h3>搜索技巧</h3><p>空格分隔多个词表示同时包含；词前加减号表示排除，如 <code>芯片 -手机</code>；<code>来源:新华网</code> 只搜该来源。</p>" +
      "<h3>快捷键</h3>" + kbdTable() +
      "<h3>离线使用</h3><p>可以把本站添加到手机桌面或电脑应用列表，看过的内容在没有网络时也能打开。</p>";
  }

  // daily brief
  function briefData() {
    var gs = homeGroups(24);
    var out = [{ name: "要闻", list: gs.slice(0, 5) }];
    var used = {}; gs.slice(0, 5).forEach(function (g) { used[g.key] = 1; });
    HOME_SECTIONS.forEach(function (c) {
      var list = gs.filter(function (g) { return !used[g.key] && (g.it.cats || [])[0] === c; }).slice(0, 3);
      list.forEach(function (g) { used[g.key] = 1; });
      if (list.length) out.push({ name: nameOf(S.index.taxonomy.cats, c), list: list });
    });
    return out;
  }
  function briefText() {
    var p = shDate(S.now);
    var lines = ["朝闻 · " + p.m + "月" + p.d + "日简报", ""];
    briefData().forEach(function (sec) {
      lines.push("【" + sec.name + "】");
      sec.list.forEach(function (g, i) { lines.push((i + 1) + ". " + speakTitle(g.it) + "（" + srcName(g.it.src) + "）"); });
      lines.push("");
    });
    lines.push(location.origin + location.pathname);
    return lines.join("\n");
  }
  function openBrief() {
    if (!S.index) return;
    var p = shDate(S.now);
    var body = '<div class="brief"><p class="muted" style="margin:0 0 10px">' + p.m + "月" + p.d + "日 · 过去 24 小时各栏目最受关注的新闻</p>" +
      '<div class="brief-tools"><button class="btn" data-act="copy-brief">复制全文</button>' + ("speechSynthesis" in window ? '<button class="btn" data-act="speak-brief">朗读要闻</button>' : "") + '<button class="btn" data-act="print-brief">打印</button></div>' +
      briefData().map(function (sec) {
        return "<h4>" + sec.name + "</h4><ol>" + sec.list.map(function (g) {
          return '<li><a href="' + attr(g.it.url) + '" target="_blank" rel="noopener" data-open="' + g.it.id + '">' + esc(speakTitle(g.it)) + "</a><small>" + esc(srcName(g.it.src)) + (g.cov > 1 ? " 等 " + g.cov + " 家" : "") + "</small></li>";
        }).join("") + "</ol>";
      }).join("") + "</div>";
    openDlg("今日简报", body);
  }
  var speaking = false;
  function speakBrief(btn) {
    if (!("speechSynthesis" in window)) return;
    if (speaking) { stopSpeak(); return; }
    var lines = [];
    briefData().slice(0, 6).forEach(function (sec) {
      lines.push(sec.name);
      sec.list.forEach(function (g) { lines.push(speakTitle(g.it)); });
    });
    speaking = true; if (btn) btn.textContent = "停止朗读";
    var voices = speechSynthesis.getVoices().filter(function (v) { return /zh/i.test(v.lang); });
    lines.forEach(function (l, i) {
      var u = new SpeechSynthesisUtterance(l);
      u.lang = "zh-CN"; u.rate = 1.02;
      if (voices[0]) u.voice = voices[0];
      if (i === lines.length - 1) u.onend = function () { speaking = false; if (btn) btn.textContent = "朗读要闻"; };
      speechSynthesis.speak(u);
    });
  }
  function stopSpeak() {
    if ("speechSynthesis" in window && speaking) speechSynthesis.cancel();
    speaking = false;
    var b = $('[data-act="speak-brief"]'); if (b) b.textContent = "朗读要闻";
  }
  function printBrief() {
    var w = window.open("", "_blank");
    if (!w) { toast("浏览器阻止了弹出窗口"); return; }
    var p = shDate(S.now);
    var html = "<!doctype html><meta charset=utf-8><title>朝闻简报</title><style>body{font:15px/1.7 'Songti SC','Noto Serif SC',serif;max-width:680px;margin:32px auto;padding:0 20px;color:#111}h1{letter-spacing:.2em;border-bottom:3px double #111;padding-bottom:8px}h2{font-size:16px;color:#b2362b;margin:18px 0 4px}li{margin:3px 0}small{color:#777}</style>";
    html += "<h1>朝闻 · " + p.m + "月" + p.d + "日简报</h1>";
    briefData().forEach(function (sec) {
      html += "<h2>" + esc(sec.name) + "</h2><ol>" + sec.list.map(function (g) { return "<li>" + esc(speakTitle(g.it)) + " <small>" + esc(srcName(g.it.src)) + "</small></li>"; }).join("") + "</ol>";
    });
    w.document.write(html); w.document.close(); w.focus(); setTimeout(function () { w.print(); }, 300);
  }

  // ------------------------------------------------------------ actions
  function snap(it) {
    return { id: it.id, title: it.title, title_zh: it.title_zh, url: it.url, src: it.src, time: it.time, lang: it.lang, excerpt: it.excerpt, excerpt_zh: it.excerpt_zh, img: it.img, cats: it.cats, geo: it.geo, topics: it.topics, _at: Date.now() };
  }
  function itemFromEl(el) {
    var card = el.closest("[data-id]");
    if (!card) return null;
    var id = card.dataset.id;
    return S.byId[id] || saved[id] || later[id] || hist.filter(function (h) { return h.id === id; })[0] || null;
  }
  function markRead(it, on) {
    if (on === false) delete readMap[it.id];
    else readMap[it.id] = Math.floor(Date.now() / 1000);
    var keys = Object.keys(readMap);
    if (keys.length > 6000) {
      keys.sort(function (a, b) { return readMap[a] - readMap[b]; }).slice(0, keys.length - 5000).forEach(function (k) { delete readMap[k]; });
    }
    save(LS.read, readMap);
  }
  function onOpen(id) {
    var it = S.byId[id] || saved[id] || later[id] || hist.filter(function (h) { return h.id === id; })[0];
    if (!it) return;
    markRead(it);
    hist = hist.filter(function (h) { return h.id !== id; });
    hist.unshift(snap(it)); hist = hist.slice(0, 200);
    save(LS.hist, hist);
    if (later[id]) { delete later[id]; save(LS.later, later); renderSections(); }
    $$('.card[data-id="' + id + '"]').forEach(function (c) {
      c.classList.add("read");
      var b = $('[data-act="read"]', c); if (b) { b.setAttribute("aria-pressed", "true"); $("span", b).textContent = "已读"; }
      var lb = $('[data-act="later"]', c); if (lb) lb.setAttribute("aria-pressed", "false");
    });
  }
  function copyText(t, msg) {
    var done = function () { toast(msg || "已复制"); };
    var fallback = function () {
      var ta = document.createElement("textarea"); ta.value = t; ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); done(); } catch (e) { toast("复制失败，请手动复制"); }
      ta.remove();
    };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(t).then(done, fallback);
    else fallback();
  }
  function doAct(act, btn) {
    var it = itemFromEl(btn);
    switch (act) {
      case "save":
        if (!it) return;
        if (saved[it.id]) { delete saved[it.id]; toast("已取消收藏"); } else { saved[it.id] = snap(it); toast("已收藏"); }
        save(LS.saved, saved); btn.setAttribute("aria-pressed", !!saved[it.id]);
        if (S.view === "mine") renderMine();
        break;
      case "later":
        if (!it) return;
        if (later[it.id]) { delete later[it.id]; toast("已移出稍后读"); } else { later[it.id] = snap(it); toast("已加入稍后读"); }
        save(LS.later, later); btn.setAttribute("aria-pressed", !!later[it.id]);
        renderSections();
        if (S.view === "mine") renderMine();
        break;
      case "read":
        if (!it) return;
        var on = !readMap[it.id]; markRead(it, on);
        btn.closest(".card").classList.toggle("read", on);
        btn.setAttribute("aria-pressed", on); $("span", btn).textContent = on ? "已读" : "标为已读";
        break;
      case "lang":
        if (!it) return;
        it._orig = !it._orig;
        var g = S.list.filter(function (x) { return x.it.id === it.id; })[0] || { it: it, all: [it], cov: 1, items: [it] };
        btn.closest(".card").outerHTML = cardHtml(g, parseQuery(S.q));
        break;
      case "copy":
        if (!it) return;
        copyText((it.lang !== "zh" && it.title_zh ? it.title_zh + "\n" + it.title : it.title) + "\n" + srcName(it.src) + " · " + absTime(ts(it)) + "\n" + it.url, "已复制标题和链接");
        break;
      case "share":
        if (!it) return;
        navigator.share({ title: titleOf(it), text: titleOf(it) + "（" + srcName(it.src) + "）", url: it.url }).catch(function () {});
        break;
      case "block":
        if (!it) return;
        if (blockSrc.indexOf(it.src) < 0) blockSrc.push(it.src);
        save(LS.blockSrc, blockSrc);
        toast("已屏蔽“" + srcName(it.src) + "”，可在设置中恢复");
        rerender(true);
        break;
      case "cluster": btn.parentNode.classList.toggle("open"); break;
      case "edit-follow": openSettings("follow"); break;
      case "copy-brief": copyText(briefText(), "简报已复制，可直接粘贴分享"); break;
      case "speak-brief": speakBrief(btn); break;
      case "print-brief": printBrief(); break;
      case "export-data": exportData(); break;
      case "clear-read": readMap = {}; save(LS.read, readMap); toast("已清除已读记录"); rerender(true); break;
      case "reset-all":
        if (!confirm("清除这台设备上的收藏、稍后读、已读、屏蔽、关注和设置？")) return;
        Object.keys(LS).forEach(function (k) { localStorage.removeItem(LS[k]); });
        localStorage.removeItem("zw.fopen");
        location.reload();
        break;
      case "export-list":
        var arr = mineList();
        copyText(arr.map(function (x) { return "· " + (x.title_zh || x.title) + "\n  " + srcName(x.src) + "  " + x.url; }).join("\n"), "已复制 " + arr.length + " 条");
        break;
      case "clear-list":
        if (!confirm("确定清空？")) return;
        if (S.tab === "saved") { saved = {}; save(LS.saved, saved); }
        else if (S.tab === "later") { later = {}; save(LS.later, later); }
        else { hist = []; save(LS.hist, hist); }
        renderMine(); renderSections();
        break;
    }
  }
  function exportData() {
    var data = { app: "zhaowen", v: 1, at: new Date().toISOString(), prefs: prefs, saved: saved, later: later, read: readMap, hist: hist, blockSrc: blockSrc, blockKw: blockKw, follow: follow };
    var blob = new Blob([JSON.stringify(data)], { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "朝闻备份-" + dayKey(Date.now()) + ".json";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
  }
  function importData(e) {
    var f = e.target.files && e.target.files[0];
    if (!f) return;
    var r = new FileReader();
    r.onload = function () {
      try {
        var d = JSON.parse(r.result);
        if (d.app !== "zhaowen") throw new Error("bad");
        prefs = Object.assign(prefs, d.prefs || {}); saved = Object.assign(saved, d.saved || {}); later = Object.assign(later, d.later || {});
        readMap = Object.assign(readMap, d.read || {}); hist = (d.hist || []).concat(hist).slice(0, 200);
        blockSrc = uniq(blockSrc.concat(d.blockSrc || [])); blockKw = uniq(blockKw.concat(d.blockKw || [])); follow = uniq(follow.concat(d.follow || []));
        save(LS.prefs, prefs); save(LS.saved, saved); save(LS.later, later); save(LS.read, readMap); save(LS.hist, hist);
        save(LS.blockSrc, blockSrc); save(LS.blockKw, blockKw); save(LS.follow, follow);
        applyPrefs(); toast("已导入"); closeDlg(); rerender();
      } catch (err) { toast("文件格式不正确"); }
    };
    r.readAsText(f);
  }

  // ------------------------------------------------------------ routing
  var VIEWS = ["home", "list", "timeline", "mine", "sources"];
  function setView(v, opts) {
    opts = opts || {};
    if (VIEWS.indexOf(v) < 0) v = "home";
    S.view = v;
    VIEWS.forEach(function (x) { $("#view-" + x).hidden = x !== v; });
    if (v === "home") renderHome();
    else if (v === "list") renderList(opts.keepScroll);
    else if (v === "timeline") renderTimeline();
    else if (v === "mine") renderMine();
    else if (v === "sources") renderSources();
    if (v !== "list") renderSections();
    if (!opts.keepScroll && v !== "list") window.scrollTo({ top: 0 });
    if (!opts.noHash) writeHash();
  }
  function rerender(keep) { setView(S.view, { keepScroll: keep, noHash: true }); }
  function resetFilters() {
    S.f = { cats: [], geo: [], topics: [], stypes: [], langs: [], srcs: [] };
    S.range = "all"; S.date = ""; S.onlyMulti = false; S.onlyImg = false; S.unread = false; S.followOnly = false;
  }
  function goSection(id) {
    if (id === "home" || id === "timeline" || id === "mine" || id === "sources") { setView(id); return; }
    resetFilters(); S.q = ""; $("#q").value = "";
    if (id === "follow") S.followOnly = true;
    else if (id !== "all") S.f.cats = [id];
    setView("list");
  }
  function writeHash() {
    var p = new URLSearchParams();
    if (S.view !== "home") p.set("v", S.view);
    if (S.view === "list") {
      FGROUPS.forEach(function (g) { if (S.f[g[0]].length) p.set(g[0], S.f[g[0]].join(",")); });
      if (S.q) p.set("q", S.q);
      if (S.sort !== "hot") p.set("sort", S.sort);
      if (S.date) p.set("date", S.date); else if (S.range !== "all") p.set("range", S.range);
      if (S.onlyMulti) p.set("multi", "1");
      if (S.onlyImg) p.set("img", "1");
      if (S.followOnly) p.set("follow", "1");
    }
    if (S.view === "timeline" && S.day) p.set("day", S.day);
    var h = p.toString();
    var url = location.pathname + location.search + (h ? "#" + h : "");
    if (url !== location.pathname + location.search + location.hash) history.replaceState(null, "", url);
  }
  function readHash() {
    var p = new URLSearchParams(location.hash.slice(1));
    resetFilters();
    FGROUPS.forEach(function (g) { var v = p.get(g[0]); if (v) S.f[g[0]] = v.split(",").filter(Boolean); });
    S.q = p.get("q") || ""; $("#q").value = S.q;
    S.sort = p.get("sort") || prefs.sort || "hot";
    S.date = p.get("date") || ""; S.range = p.get("range") || "all";
    S.onlyMulti = p.get("multi") === "1"; S.onlyImg = p.get("img") === "1"; S.followOnly = p.get("follow") === "1";
    S.day = p.get("day") || S.day;
    return p.get("v") || (S.q ? "list" : "home");
  }
  function shareView() {
    writeHash();
    copyText(location.href, "已复制当前页面链接");
  }

  // ------------------------------------------------------------ events
  function bind() {
    document.addEventListener("click", function (e) {
      var t = e.target, a;
      if ((a = t.closest("[data-open]"))) { onOpen(a.dataset.open); return; }
      if ((a = t.closest("[data-sec]"))) { e.preventDefault(); closeFilters(); closeDlg(); goSection(a.dataset.sec); return; }
      if ((a = t.closest("[data-src]"))) {
        e.preventDefault(); closeDlg();
        resetFilters(); S.q = ""; $("#q").value = ""; S.f.srcs = [a.dataset.src]; S.sort = "new"; setView("list"); return;
      }
      if ((a = t.closest("[data-act]"))) { e.preventDefault(); doAct(a.dataset.act, a); return; }
      if ((a = t.closest("[data-f]"))) {
        var k = a.dataset.f, v = a.dataset.v, arr = S.f[k];
        if (!a.closest("#filters, #active-bar")) { resetFilters(); S.f[k] = [v]; S.q = ""; $("#q").value = ""; setView("list"); return; }
        var i = arr.indexOf(v); if (i >= 0) arr.splice(i, 1); else arr.push(v);
        renderList(true); writeHash(); return;
      }
      if ((a = t.closest("[data-range]"))) { S.range = a.dataset.range; S.date = ""; renderList(true); writeHash(); return; }
      if ((a = t.closest("[data-date]"))) {
        var d = a.dataset.date; S.date = S.date === d ? "" : d; S.range = "all";
        loadDay(d).then(function () { renderList(true); writeHash(); });
        return;
      }
      if ((a = t.closest("[data-more]"))) { openGroups[a.dataset.more + "All"] = true; renderFilters(); return; }
      if ((a = t.closest("[data-clear-q]"))) { S.q = ""; $("#q").value = ""; renderList(true); writeHash(); return; }
      if ((a = t.closest("[data-follow-off]"))) { S.followOnly = false; renderList(true); writeHash(); return; }
      if ((a = t.closest("[data-toggle-off]"))) { S[a.dataset.toggleOff] = false; renderList(true); writeHash(); return; }
      if (t.id === "clear-all" || t.closest("#btn-reset")) { resetFilters(); S.q = ""; $("#q").value = ""; renderList(true); writeHash(); return; }
      if ((a = t.closest("[data-sort]"))) { S.sort = a.dataset.sort; prefs.sort = S.sort; savePrefs(); renderList(true); writeHash(); return; }
      if ((a = t.closest("[data-sort-go]"))) { resetFilters(); S.q = ""; $("#q").value = ""; S.sort = "hot"; S.range = "24h"; setView("list"); return; }
      if ((a = t.closest("[data-q]"))) { resetFilters(); S.q = a.dataset.q; $("#q").value = S.q; S.sort = "hot"; setView("list"); return; }
      if ((a = t.closest("[data-day]"))) { S.day = a.dataset.day; renderTimeline(); writeHash(); return; }
      if ((a = t.closest("[data-tlcat]"))) { S.tlCat = a.dataset.tlcat; renderTimeline(); return; }
      if ((a = t.closest("[data-hour]"))) { var h = $("#tl-h" + a.dataset.hour); if (h) h.scrollIntoView({ behavior: "smooth", block: "start" }); return; }
      if ((a = t.closest("[data-tab]"))) { S.tab = a.dataset.tab; renderMine(); return; }
      if ((a = t.closest("[data-stype]"))) { S.stypeView = a.dataset.stype; renderSources(); return; }
      if ((a = t.closest("[data-block-src]"))) {
        var id = a.dataset.blockSrc, ix = blockSrc.indexOf(id);
        if (ix >= 0) blockSrc.splice(ix, 1); else blockSrc.push(id);
        save(LS.blockSrc, blockSrc); renderSources(); return;
      }
      if ((a = t.closest("[data-pref]"))) { prefs[a.dataset.pref] = a.dataset.val; savePrefs(); applyPrefs(); refreshSettings(); rerender(true); return; }
      if ((a = t.closest("[data-follow-topic]"))) {
        var key = "topic:" + a.dataset.followTopic, fi = follow.indexOf(key);
        if (fi >= 0) follow.splice(fi, 1); else follow.push(key);
        save(LS.follow, follow); refreshSettings(); rerender(true); return;
      }
      if ((a = t.closest("[data-del-word]"))) {
        var list = a.dataset.delWord === "follow" ? follow : blockKw;
        var wi = list.indexOf(a.dataset.w); if (wi >= 0) list.splice(wi, 1);
        save(LS[a.dataset.delWord], list); refreshSettings(); rerender(true); return;
      }
      if ((a = t.closest("[data-unblock]"))) {
        blockSrc = blockSrc.filter(function (x) { return x !== a.dataset.unblock; });
        save(LS.blockSrc, blockSrc); refreshSettings(); rerender(true); return;
      }
    });
    document.addEventListener("change", function (e) {
      var t = e.target;
      if (t.dataset.toggle) {
        var k = t.dataset.toggle;
        if (k === "group") { prefs.group = t.checked; savePrefs(); } else S[k] = t.checked;
        renderList(true); writeHash(); return;
      }
      if (t.dataset.prefBool) { prefs[t.dataset.prefBool] = t.checked; savePrefs(); applyPrefs(); rerender(true); return; }
      if (t.id === "tl-multi") { S.tlMulti = t.checked; renderTimeline(); }
    });
    document.addEventListener("submit", function (e) {
      var f = e.target.closest("[data-add-word]");
      if (!f) return;
      e.preventDefault();
      var inp = $("input", f), w = inp.value.trim();
      if (!w) return;
      var key = f.dataset.addWord, list = key === "follow" ? follow : blockKw;
      if (list.indexOf(w) < 0) list.push(w);
      save(LS[key], list); refreshSettings(); rerender(true);
      var again = $('[data-add-word="' + key + '"] input'); if (again) again.focus();
    });
    document.addEventListener("toggle", function (e) {
      var d = e.target;
      if (d.classList && d.classList.contains("fgroup")) { openGroups[d.dataset.g] = d.open; save("zw.fopen", openGroups); }
    }, true);

    var q = $("#q");
    q.addEventListener("input", debounce(function () {
      S.q = q.value.trim();
      if (S.view !== "list") { if (!S.q) return; resetFilters(); setView("list"); }
      else { renderList(true); writeHash(); }
    }, 280));
    q.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { q.value = ""; S.q = ""; q.blur(); if (S.view === "list") { renderList(true); writeHash(); } }
      if (e.key === "Enter") q.blur();
    });

    $("#btn-theme").addEventListener("click", function () {
      prefs.theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark"; savePrefs(); applyPrefs();
    });
    $("#btn-settings").addEventListener("click", function () { openSettings(); });
    $("#btn-about").addEventListener("click", function () { openDlg("关于朝闻", aboutBody()); });
    $("#btn-brief").addEventListener("click", openBrief);
    $("#btn-sources").addEventListener("click", function () { setView("sources"); });
    $("#btn-share-view").addEventListener("click", shareView);
    $("#dlg-close").addEventListener("click", closeDlg);
    $("#dlg").addEventListener("click", function (e) { if (e.target.id === "dlg") closeDlg(); });
    $("#dlg").addEventListener("close", stopSpeak);
    $("#btn-filter").addEventListener("click", openFilters);
    $("#btn-close-filters").addEventListener("click", closeFilters);
    $("#btn-apply").addEventListener("click", closeFilters);
    $("#filters-mask").addEventListener("click", closeFilters);
    $("#to-top").addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
    window.addEventListener("scroll", debounce(function () { $("#to-top").hidden = window.scrollY < 900; }, 80), { passive: true });
    var mq = matchMedia("(prefers-color-scheme: dark)");
    var onScheme = function () { if (prefs.theme === "auto") applyPrefs(); };
    if (mq.addEventListener) mq.addEventListener("change", onScheme); else if (mq.addListener) mq.addListener(onScheme);

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) {
        if (es[0].isIntersecting && S.view === "list" && S.shown < S.list.length) more();
      }, { rootMargin: "700px 0px" }).observe($("#sentinel"));
    } else {
      window.addEventListener("scroll", function () { if (S.view === "list" && innerHeight + scrollY > document.body.offsetHeight - 800) more(); });
    }

    var gAt = 0;
    document.addEventListener("keydown", function (e) {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      var tag = (e.target.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea" || tag === "select" || e.target.isContentEditable) return;
      if ($("#dlg").open) return;
      var k = e.key;
      if (k === "/") { e.preventDefault(); setSearchOpen(true); return; }
      if (k === "?") { openDlg("快捷键", kbdTable()); return; }
      if (k === "g") { gAt = Date.now(); return; }
      if (k === "h" && Date.now() - gAt < 900) { goSection("home"); return; }
      var cards = $$("#view-" + S.view + " .card");
      if (!cards.length) return;
      if (k === "j" || k === "k") {
        e.preventDefault();
        S.focus = Math.max(0, Math.min(cards.length - 1, S.focus + (k === "j" ? 1 : -1)));
        cards.forEach(function (c) { c.classList.remove("focus"); });
        var c = cards[S.focus]; c.classList.add("focus");
        c.scrollIntoView({ block: "center", behavior: "smooth" });
        if (k === "j" && S.focus > cards.length - 4) more();
        return;
      }
      var cur = cards[S.focus];
      if (!cur) return;
      var map = { s: "save", l: "later", m: "read", t: "lang" };
      if (map[k]) { var b = $('[data-act="' + map[k] + '"]', cur); if (b) b.click(); return; }
      if (k === "o" || k === "Enter") { var a = $("h3 a", cur); if (a) { onOpen(cur.dataset.id); window.open(a.href, "_blank", "noopener"); } }
    });
    window.addEventListener("hashchange", function () { setView(readHash(), { noHash: true }); });
  }
  function openFilters() { $("#filters").classList.add("open"); $("#filters-mask").hidden = false; document.body.style.overflow = "hidden"; }
  function closeFilters() { $("#filters").classList.remove("open"); $("#filters-mask").hidden = true; document.body.style.overflow = ""; }

  // ------------------------------------------------------------ header bits
  var LUNAR_D = ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十", "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十", "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"];
  function dateline() {
    var p = shDate(Date.now());
    var s = p.y + "年" + p.m + "月" + p.d + "日 星期" + WEEK[p.w], lunar = "";
    try {
      var parts = new Intl.DateTimeFormat("zh-CN-u-ca-chinese", { timeZone: "Asia/Shanghai", year: "numeric", month: "long", day: "numeric" }).formatToParts(new Date());
      var m = "", d = "", y = "";
      parts.forEach(function (x) { if (x.type === "month") m = x.value; if (x.type === "day") d = x.value; if (x.type === "yearName") y = x.value; });
      var dn = parseInt(d, 10);
      if (m && dn >= 1 && dn <= 30) lunar = "农历" + (y ? y + "年" : "") + m + LUNAR_D[dn - 1];
    } catch (e) {}
    $("#dateline").innerHTML = esc(s) + (lunar ? '<span class="lunar"> · ' + esc(lunar) + "</span>" : "");
  }
  function updatedLine() {
    var st = S.index, g = Date.parse(st.generated);
    var ok = st.sources.filter(function (s) { return s.ok; }).length;
    $("#updated").innerHTML = "更新于 <b>" + rel(g) + "</b> · " + ok + " 个来源 · " + fmtNum(st.count) + " 条新闻";
    $("#foot-stats").textContent = "收录最近 " + st.window_days + " 天 · 最近更新 " + absTime(g);
  }
  function showNewNotice() {
    var n = newCount();
    if (!lastVisit || n < 1 || S.view !== "home") return;
    var el = $("#notice");
    var since = lastVisit;
    el.innerHTML = "<span>自你上次来访，新增了 <b>" + n + '</b> 条新闻。</span><button class="link-btn" id="see-new">按时间查看</button><button class="link-btn" id="close-notice">知道了</button>';
    el.hidden = false;
    $("#see-new").addEventListener("click", function () {
      el.hidden = true; resetFilters(); S.q = ""; $("#q").value = ""; S.sort = "new";
      var gap = Date.now() - since;
      S.range = gap < 6 * 3600000 ? "6h" : gap < 86400000 ? "24h" : gap < 3 * 86400000 ? "3d" : "all";
      setView("list");
    });
    $("#close-notice").addEventListener("click", function () { el.hidden = true; });
  }
  function setSearchOpen(on, noFocus) {
    $(".search").classList.toggle("open", on);
    $(".masthead").classList.toggle("searching", on);
    if (on && !noFocus) $("#q").focus();
  }
  function mobileSearch() {
    var btn = document.createElement("button");
    btn.className = "icon-btn only-mobile"; btn.type = "button"; btn.setAttribute("aria-label", "搜索");
    btn.innerHTML = '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l5 5"/></svg>';
    btn.addEventListener("click", function () { setSearchOpen(!$(".search").classList.contains("open")); });
    $(".mast-actions").insertBefore(btn, $("#btn-theme"));
    if (S.q) setSearchOpen(true, true);
  }

  // ------------------------------------------------------------ boot
  function boot() {
    applyPrefs(); dateline(); bind(); mobileSearch();
    var initialView = readHash();
    $("#view-home").hidden = false;
    $("#view-home").innerHTML = skeleton();
    renderSections();
    fetchJSON(DATA + "index.json?t=" + Math.floor(Date.now() / 60000)).then(function (idx) {
      S.index = idx; S.now = Date.now();
      idx.sources.forEach(function (s) { S.src[s.id] = s; });
      updatedLine();
      var first = idx.days.slice(0, 2).map(function (d) { return d.date; });
      if (S.date && first.indexOf(S.date) < 0) first.push(S.date);
      if (initialView === "timeline" && S.day && first.indexOf(S.day) < 0) first.push(S.day);
      return Promise.all(first.map(loadDay)).then(function () {
        setView(initialView, { noHash: true });
        showNewNotice();
        save(LS.visit, Date.now());
        setTimeout(function () {
          loadAll().then(function () {
            if (S.view === "list") renderList(true);
            else if (S.view === "home") { var y = window.scrollY; renderHome(); window.scrollTo(0, y); }
          });
        }, 700);
      });
    }).catch(function () {
      $("#view-home").innerHTML = '<div class="empty"><h3>暂时无法载入新闻</h3><p>请检查网络后刷新页面。</p></div>';
      $("#updated").textContent = "暂时无法连接";
    });
    setInterval(function () { S.now = Date.now(); if (S.index) updatedLine(); }, 60000);
    if ("serviceWorker" in navigator && location.protocol === "https:") {
      navigator.serviceWorker.register("sw.js").catch(function () {});
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
